/**
 * Every outbound link on the marketing page. One place, so nothing hotlinks a
 * service and nothing drifts. Kept in step with landing/src/lib/site.ts — the
 * two builds render the same page.
 *
 * REPO_URL is the href behind every "View on GitHub" button, and LICENCE_URL,
 * DOCS_URL and ISSUES_URL are derived from it — change it in one place and all
 * four follow. Mirror any change into landing/src/lib/site.ts; the two builds
 * render the same page.
 *
 * DOCS_URL points into docs/, which is published in full. It used to point at
 * the README because docs/ held internal planning and audit notes that were
 * gitignored; those were deleted on 2026-09-05 and every remaining file there
 * ships.
 */
const REPO_URL = "https://github.com/databluedev/searchmirror";
const LICENCE_URL = `${REPO_URL}/blob/main/LICENSE`;
const DOCS_URL = `${REPO_URL}/tree/main/docs`;
const ISSUES_URL = `${REPO_URL}/issues`;

/** The app's own auth routes — the paths App.js actually registers. */
const SIGNUP_URL = "/signup";
const SIGNIN_URL = "/login";

export {
  DOCS_URL,
  ISSUES_URL,
  LICENCE_URL,
  REPO_URL,
  SIGNIN_URL,
  SIGNUP_URL
};
