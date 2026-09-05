/**
 * Every outbound link on the page. One place, so nothing hotlinks a service and
 * nothing drifts.
 *
 * REPO_URL is the href behind every "View on GitHub" button, and LICENCE_URL,
 * DOCS_URL and ISSUES_URL are derived from it — change it in one place and all
 * four follow. Mirror any change into app/src/pages/landing/lib/site.js; the two builds
 * render the same page.
 *
 * DOCS_URL points into docs/, which is published in full. It used to point at
 * the README because docs/ held internal planning and audit notes that were
 * gitignored; those were deleted on 2026-09-05 and every remaining file there
 * ships.
 */
export const REPO_URL = "https://github.com/databluedev/searchmirror";
export const LICENCE_URL = `${REPO_URL}/blob/main/LICENSE`;
export const DOCS_URL = `${REPO_URL}/tree/main/docs`;
export const ISSUES_URL = `${REPO_URL}/issues`;

/**
 * The app's auth routes. /signup and /login are the paths app/src/App.js
 * actually registers — it is /login, not /signin.
 *
 * These were bare same-origin paths, which is right only when this page is
 * served from the app's own origin. This build is not in the compose stack and
 * has no proxy in front of it, so on its own port every auth CTA — both "Get
 * started" buttons and "Sign in" — hit this site's SPA fallback and re-served
 * the marketing page. Clicking "Get started" landed you back on the page you
 * were already reading.
 *
 * VITE_APP_ORIGIN names the app when the two are deployed apart (e.g.
 * "https://app.example.com", or "http://127.0.0.1:3001" for a local run).
 * Leave it unset for the same-origin deployment and the paths stay relative,
 * exactly as before.
 */
const APP_ORIGIN = (import.meta.env.VITE_APP_ORIGIN || "").replace(/\/+$/, "");

export const SIGNUP_URL = `${APP_ORIGIN}/signup`;
export const SIGNIN_URL = `${APP_ORIGIN}/login`;
