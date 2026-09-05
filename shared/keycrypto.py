"""Encryption helpers for per-account SERP provider API keys.

Lives in the top-level `shared/` package, not inside either Django project:
the backend writes these tokens and the ENGINE reads them back, and the two
run as separate images. A copy in each would be two implementations of one
derivation -- and a divergence would strand every key already stored.

WHY NOT FERNET
--------------
The brief asked for `cryptography.fernet.Fernet`.  That package is NOT
installed in the tracker image (`pip show cryptography` -> not found) and the
instruction was to avoid adding new dependencies, so this module builds an
equivalent authenticated-encryption token out of the Python standard library
only (hmac + hashlib + secrets).  The construction is deliberately
conservative and uses no hand-written primitives:

    root     = SHA256(SERP_KEY_SECRET)
    enc_key  = HMAC-SHA256(root, b"enc")
    mac_key  = HMAC-SHA256(root, b"mac")
    stream   = HMAC-SHA256(enc_key, nonce || counter)   # CTR-style keystream
    cipher   = plaintext XOR stream
    tag      = HMAC-SHA256(mac_key, version || nonce || cipher)   # encrypt-then-MAC
    token    = "v1:" + urlsafe_b64(nonce || cipher || tag)

The nonce is 16 fresh random bytes per call, so the keystream is never reused.
The tag is verified with `hmac.compare_digest` before any plaintext is
returned, so a tampered or truncated ciphertext raises instead of decrypting.

Tokens are version-prefixed.  If `cryptography` is installed later, add a
"v2:" Fernet branch to `decrypt_key` and re-encrypt on next write -- existing
"v1:" values stay readable.  Do NOT change the v1 derivation; it would strand
every key already stored.
"""

import base64
import hashlib
import hmac
import os
import secrets


class KeyCryptoUnconfigured(RuntimeError):
	"""SERP_KEY_SECRET is absent, so no key can be encrypted or decrypted."""


_VERSION_ = b"v1"
_PREFIX_ = "v1:"
_NONCE_BYTES_ = 16
_TAG_BYTES_ = 32
_BLOCK_ = 32


def _master_secret_():
	"""Read the master secret from the environment.

	Raises at call time (not import time) so a missing env var never stops
	the app from booting -- only the key endpoints fail, and loudly.
	"""
	secret = os.environ.get("SERP_KEY_SECRET", "")
	# .env.example ships a literal placeholder. Left unchanged it is public
	# knowledge, so every key stored on that instance is readable by anyone
	# holding the repo. Refuse it as loudly as an absent secret.
	if secret.startswith("change-me"):
		raise KeyCryptoUnconfigured(
			"SERP_KEY_SECRET is still the placeholder from .env.example -- "
			"generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
		)
	if not secret:
		raise KeyCryptoUnconfigured(
			"SERP_KEY_SECRET is not set -- per-account SERP keys cannot be "
			"encrypted or decrypted without it."
		)
	return secret.encode("utf-8")


def _derive_(purpose):
	root = hashlib.sha256(_master_secret_()).digest()
	return hmac.new(root, purpose, hashlib.sha256).digest()


def _keystream_(enc_key, nonce, length):
	out = bytearray()
	counter = 0
	while len(out) < length:
		block = hmac.new(
			enc_key, nonce + counter.to_bytes(4, "big"), hashlib.sha256
		).digest()
		out.extend(block)
		counter += 1
	return bytes(out[:length])


def _xor_(data, stream):
	return bytes(a ^ b for a, b in zip(data, stream))


def encrypt_key(plain_key):
	"""Encrypt a raw provider API key into a storable token string.

	Returns "" for an empty input so a blank key round-trips as blank.
	"""
	if not plain_key:
		return ""

	plain = plain_key.encode("utf-8")
	nonce = secrets.token_bytes(_NONCE_BYTES_)
	cipher = _xor_(plain, _keystream_(_derive_(b"enc"), nonce, len(plain)))
	tag = hmac.new(
		_derive_(b"mac"), _VERSION_ + nonce + cipher, hashlib.sha256
	).digest()

	return _PREFIX_ + base64.urlsafe_b64encode(nonce + cipher + tag).decode("ascii")


def decrypt_key(token):
	"""Reverse `encrypt_key`.  Returns "" for empty/unset values.

	Raises ValueError if the token is malformed or fails authentication.
	"""
	if not token:
		return ""

	if not token.startswith(_PREFIX_):
		raise ValueError("unrecognised SERP key token format")

	try:
		raw = base64.urlsafe_b64decode(token[len(_PREFIX_):].encode("ascii"))
	except Exception:
		raise ValueError("SERP key token is not valid base64")

	if len(raw) < _NONCE_BYTES_ + _TAG_BYTES_:
		raise ValueError("SERP key token is truncated")

	nonce = raw[:_NONCE_BYTES_]
	cipher = raw[_NONCE_BYTES_:-_TAG_BYTES_]
	tag = raw[-_TAG_BYTES_:]

	expected = hmac.new(
		_derive_(b"mac"), _VERSION_ + nonce + cipher, hashlib.sha256
	).digest()
	if not hmac.compare_digest(tag, expected):
		raise ValueError("SERP key token failed authentication")

	return _xor_(cipher, _keystream_(_derive_(b"enc"), nonce, len(cipher))).decode("utf-8")


def mask_key(plain_key):
	"""Render a key for display: first 6 and last 4 characters only.

	Short keys are masked entirely rather than leaking a large fraction.
	"""
	if not plain_key:
		return ""
	if len(plain_key) < 16:
		return "*" * len(plain_key)
	return plain_key[:6] + "…" + plain_key[-4:]
