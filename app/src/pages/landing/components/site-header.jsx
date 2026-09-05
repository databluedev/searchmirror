import { ButtonLink } from "./ui/button";
import { GitHubIcon, Wordmark } from "./ui/logo";
import { REPO_URL, SIGNIN_URL, SIGNUP_URL } from "../lib/site";
const NAV = [
  ["Why BYOK", "#byok"],
  ["Features", "#features"],
  ["AI visibility", "#geo"],
  ["How it works", "#how"],
  ["Self-host", "#hosting"]
];
function SiteHeader() {
  return <header className="sticky top-0 z-50 border-b border-line bg-paper/85 backdrop-blur-md">
      {/* Full-width bar, 3-column grid with equal side columns so the nav is
          pinned to the TRUE center of the viewport regardless of the logo's and
          actions' differing widths. Logo left, nav dead-center, actions right. */}
      <div className="grid h-14 w-full grid-cols-[1fr_auto_1fr] items-center gap-3 px-4 md:gap-6 md:px-10 lg:px-16">
        <a
    href="#top"
    className="justify-self-start rounded-sm text-ink no-underline"
    aria-label="SearchMirror — top of page"
  >
          <Wordmark />
        </a>

        <nav aria-label="Sections" className="hidden justify-self-center lg:block">
          <ul className="flex items-center gap-8">
            {NAV.map(([label, href]) => <li key={href}>
                <a
    href={href}
    className="rounded-sm text-[13.5px] font-medium text-ink-2 transition-colors duration-fast hover:text-accent"
  >
                  {label}
                </a>
              </li>)}
          </ul>
        </nav>

        <div className="flex items-center justify-self-end gap-1 sm:gap-2">
          <a
    href={REPO_URL}
    rel="noreferrer noopener"
    className="hidden rounded-sm p-2 text-ink-2 transition-colors duration-fast hover:text-ink sm:inline-flex"
    aria-label="SearchMirror on GitHub"
  >
            <GitHubIcon />
          </a>
          {/* Shown at every width. This was `hidden sm:inline-flex`, which left
              a phone with "Get started" as the only action and no route to the
              login screen at all -- there is no drawer here to hide it in. */}
          <ButtonLink href={SIGNIN_URL} variant="ghost" className="px-2.5 sm:px-[18px]">
            Sign in
          </ButtonLink>
          <ButtonLink href={SIGNUP_URL} className="px-3.5 sm:px-[18px]">Get started</ButtonLink>
        </div>
      </div>
    </header>;
}
export {
  SiteHeader
};
