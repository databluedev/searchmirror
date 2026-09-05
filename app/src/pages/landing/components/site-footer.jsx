import { ArrowRight } from "lucide-react";
import { ButtonLink } from "./ui/button";
import { GitHubIcon, Wordmark } from "./ui/logo";
import { MicroLabel } from "./ui/section";
import {
  DOCS_URL,
  ISSUES_URL,
  LICENCE_URL,
  REPO_URL,
  SIGNUP_URL
} from "../lib/site";
const PRODUCT_LINKS = [
  ["Why BYOK", "#byok"],
  ["Features", "#features"],
  ["AI visibility", "#geo"],
  ["Content tools", "#content"],
  ["How it works", "#how"],
  ["Self-host", "#hosting"]
];
const PROJECT_LINKS = [
  ["Source on GitHub", REPO_URL],
  ["Documentation", DOCS_URL],
  ["Licence", LICENCE_URL],
  ["Report an issue", ISSUES_URL]
];
function SiteFooter() {
  return <footer className="border-t border-line bg-surface">
      <div className="mx-auto w-full max-w-[1360px] px-6 md:px-8">
        <div className="flex flex-col gap-8 border-b border-line py-16 md:flex-row md:items-center md:justify-between md:py-20">
          <div>
            <MicroLabel>Start here</MicroLabel>
            <p className="mt-4 max-w-[24ch] text-[1.75rem] font-semibold leading-[1.1] tracking-display sm:text-[2.25rem]">
              Connect a key and track your first keyword today.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row md:shrink-0">
            <ButtonLink href={SIGNUP_URL} size="lg">
              Get started
              <ArrowRight aria-hidden="true" />
            </ButtonLink>
            <ButtonLink
    href={REPO_URL}
    rel="noreferrer noopener"
    variant="secondary"
    size="lg"
  >
              <GitHubIcon />
              View on GitHub
            </ButtonLink>
          </div>
        </div>

        <div className="grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-[1.5fr_1fr_1fr]">
          <div>
            <Wordmark />
            <p className="mt-4 max-w-[34ch] text-[13.5px] leading-[1.6] text-ink-2">
              An open-source SEO rank tracker and AI-visibility monitor you can
              host yourself, running on the SERP and AI keys you own.
            </p>
          </div>

          <FooterColumn heading="Product" links={PRODUCT_LINKS} />
          <FooterColumn heading="Project" links={PROJECT_LINKS} external />
        </div>

        <div className="flex flex-col gap-3 border-t border-line py-7 text-[12.5px] text-ink-3 sm:flex-row sm:items-center sm:justify-between">
          <p>
            No analytics, no tracking pixels, no third-party fonts. This page
            loads nothing from anywhere but this server.
          </p>
          <p>SearchMirror — open source.</p>
        </div>
      </div>
    </footer>;
}
function FooterColumn({
  heading,
  links,
  external = false
}) {
  return <nav aria-label={heading}>
      <h2 className="micro">{heading}</h2>
      <ul className="mt-5 space-y-3">
        {links.map(([label, href]) => <li key={label}>
            <a
    href={href}
    {...external ? { rel: "noreferrer noopener" } : {}}
    className="rounded-sm text-[13.5px] text-ink-2 transition-colors duration-fast hover:text-ink"
  >
              {label}
            </a>
          </li>)}
      </ul>
    </nav>;
}
export {
  SiteFooter
};
