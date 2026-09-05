// One reading of a failed auth request, for every screen in this directory.
//
// These pages used to branch on the server's prose. login.js matched the exact
// string "You are not a user of our tool. So kindly register with the Tracker.";
// the API now answers "No SearchMirror account exists for this email.", so the
// branch stopped firing and signing in with an unknown address did nothing at
// all -- no message, no redirect, nothing on screen. The other four screens
// dereferenced error.response.data with no guard, or swallowed the failure and
// left the button spinning.
//
// So: never read the message to decide what to do, and never end a failed
// submit without something the user can see.

// Shown when the request never reached a view that could explain itself: the
// API is down, DNS failed, the request was aborted. Same sentence the account
// screens use.
const GENERIC_ERROR = "Could not reach SearchMirror. Please try again.";

export function authErrorMessage(error) {
  const data = error && error.response && error.response.data;
  const message = data && typeof data.message === "string" ? data.message.trim() : "";
  return message || GENERIC_ERROR;
}

export default authErrorMessage;
