import { Check, Minus } from "lucide-react";

import { ButtonLink } from "@/components/ui/button";
import { GitHubIcon } from "@/components/ui/logo";
import { Lede, MicroLabel, Section, SectionHeading } from "@/components/ui/section";
import { REPO_URL } from "@/lib/site";

/**
 * Self-hosting only. This section used to put a paid "Hosted" plan beside it —
 * a monthly fee, managed upgrades and backups, and email support with a
 * working-day response. None of that exists: there is no hosted instance, no
 * signup for one, and no billing in the product. A hosted service is intended
 * later; when it is real, add the second column back rather than reviving this
 * copy, because the SLA in it was never something anyone had agreed to.
 */

type Row = { text: string; plus: boolean };

// Both the good and the awkward parts. The `plus: false` rows are the honest
// cost of running it yourself and are the reason a hosted option is wanted at
// all — they stay.
const SELF_HOST: Row[] = [
  { text: "Free. There is no paid tier of the software.", plus: true },
  { text: "Your server, your database, your backups.", plus: true },
  { text: "Docker Compose, MongoDB and roughly 2 GB of RAM.", plus: true },
  { text: "You apply the upgrades and you own the uptime.", plus: false },
  { text: "Support is the issue tracker, answered when we can.", plus: false },
];

export function Hosting() {
  return (
    <Section id="hosting" labelledBy="hosting-heading">
      <div className="max-w-[46rem]">
        <MicroLabel>Self-host</MicroLabel>
        <SectionHeading id="hosting-heading" className="max-w-[22ch]">
          The repository is the whole product.
        </SectionHeading>
        <Lede>
          There is no paid tier, no hosted plan to upgrade to, and nothing held
          back for one. You clone it, you run it, and it is yours — which also
          means the upgrades and the uptime are yours. That trade is the whole
          deal, and it is stated in full below.
        </Lede>
      </div>

      <div className="mt-14 max-w-[34rem]">
        <div className="flex flex-col rounded-md border border-line bg-surface p-7">
          <div className="flex items-baseline justify-between gap-4 border-b border-line pb-5">
            <h3 className="text-[1.375rem] font-semibold tracking-display">
              Self-host
            </h3>
            <span className="num text-[15px] font-semibold text-ink-2">Free</span>
          </div>
          <p className="mt-5 text-[13.5px] text-ink-3">
            Clone, configure, docker compose up.
          </p>

          <ul className="mt-6 space-y-3.5">
            {SELF_HOST.map(({ text, plus }) => (
              <li key={text} className="flex gap-3 text-[13.5px] leading-[1.55]">
                {plus ? (
                  <Check
                    aria-hidden="true"
                    className="mt-0.5 h-4 w-4 shrink-0 text-ink"
                    strokeWidth={2}
                  />
                ) : (
                  <Minus
                    aria-hidden="true"
                    className="mt-0.5 h-4 w-4 shrink-0 text-ink-4"
                    strokeWidth={2}
                  />
                )}
                <span className={plus ? "text-ink-2" : "text-ink-3"}>{text}</span>
              </li>
            ))}
          </ul>

          <div className="mt-8">
            <ButtonLink
              href={REPO_URL}
              rel="noreferrer noopener"
              variant="secondary"
            >
              <GitHubIcon />
              Read the setup guide
            </ButtonLink>
          </div>
        </div>
      </div>
    </Section>
  );
}
