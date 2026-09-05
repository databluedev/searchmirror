# Tests

Security and wiring regressions, run against a **running stack**. The app is
djongo on MongoDB, where `manage.py test` cannot create a test database — and
every bug covered here was a routing or authentication bug that only a real
HTTP request can prove. A view that looks guarded and is not looks identical
in a unit test; it does not look identical to curl.

```bash
docker compose up -d
pip install pytest requests
pytest tests -v
```

Point at another instance or account with `TRACKER_API`, `TRACKER_EMAIL`,
`TRACKER_PASSWORD`.

| File | Covers |
|------|--------|
| `test_authentication.py` | Anonymous callers are refused. `permission_classes` on a plain `django.views.View` or a bare function guards nothing — these assert the response code, not the decorator. |
| `test_ownership.py` | A token may only act for its own account, in the body and in the query string. |
| `test_cron_gate.py` | Scheduled endpoints refuse anyone without the instance `CRON_TOKEN`, and the deleted debug routes stay deleted. Never sends a valid token: that would run the job and spend real credits. |
| `test_registration.py` | The public signup endpoint. It read five optional fields with `[]` instead of `.get()`, so a client posting only username/email/password got a 500. Creates a probe account and removes it in teardown — validation gates `save()`, so a payload that fails validation never reaches the code under test. |
| `test_first_run.py` | A brand-new account must not meet a 500 on its first day: keyword panels before any ranking run, an unrecognised language, project reads with no saved settings. |
| `test_no_credential_leak.py` | The report share link answered anonymous callers with the owner's API token; it asserts the routes stay gone and that nothing token-shaped comes back, plus that the public preview pages refuse junk without raising. |
| `test_byok.py` | Keys are masked on read, all four AI providers are offered, the balance read costs nothing, and no account reports a dead subscription. |
