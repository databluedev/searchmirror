import { ArrowRight } from "lucide-react";

import { BackgroundGrid } from "@/components/ui/background-grid";
import { ButtonLink } from "@/components/ui/button";
import { Glow } from "@/components/ui/glow";
import { GitHubIcon } from "@/components/ui/logo";
import { MicroLabel } from "@/components/ui/section";
import { TypingAnimation } from "@/components/ui/typing-animation";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { REPO_URL, SIGNUP_URL } from "@/lib/site";

const HEADLINE_A = "Track every keyword you want,";
const HEADLINE_B = "on a key you own.";

/** Sample data, in the product's own vocabulary. Marked aria-hidden: it is an
 *  illustration of the interface, not information the reader needs read out. */
const SAMPLE: Array<[string, string, string, "up" | "down" | "flat"]> = [
  ["seo rank tracker", "3", "+4", "up"],
  ["serp api pricing", "7", "+1", "up"],
  ["keyword position check", "12", "-2", "down"],
  ["best rank tracker 2026", "18", "0", "flat"],
];

export function Hero() {
  const reduced = useReducedMotion();

  return (
    <div id="top" className="relative isolate overflow-hidden">
      <BackgroundGrid />
      <Glow className="left-1/2 top-[-12rem] h-[34rem] w-[34rem] -translate-x-1/2" />

      <div className="mx-auto w-full max-w-[1200px] px-6 pb-20 pt-16 md:px-8 md:pb-28 md:pt-24">
        <div className="flex flex-col items-center text-center">
          <MicroLabel className="text-ink-2">Open source · Bring your own key</MicroLabel>

          {/* Sized so the second line fits on one line at every breakpoint —
              36px at 375px is the binding case. */}
          <h1 className="mt-7 text-[2.25rem] font-semibold leading-[0.98] tracking-tightest sm:text-[3.25rem] md:text-[4rem] lg:text-[5rem]">
            <span className="sr-only">{`${HEADLINE_A} ${HEADLINE_B}`}</span>
            <span aria-hidden="true" className="block max-w-[16ch]">
              {HEADLINE_A}
            </span>
            {/* An invisible copy of the line holds the box open, so the typing
                animation never reflows the page beneath it. Both copies share a
                single grid cell, which keeps them in normal flow and therefore
                wrapping identically at any width. */}
            <span aria-hidden="true" className="grid">
              <span className="invisible [grid-area:1/1]">{HEADLINE_B}</span>
              <span className="[grid-area:1/1]">
                {reduced ? (
                  HEADLINE_B
                ) : (
                  <TypingAnimation
                    as="span"
                    className="leading-[0.98] tracking-tightest"
                    delay={420}
                    duration={42}
                    startOnView={false}
                    cursorStyle="line"
                  >
                    {HEADLINE_B}
                  </TypingAnimation>
                )}
              </span>
            </span>
          </h1>

          <p className="mt-7 max-w-[56ch] text-[1.0625rem] leading-[1.6] text-ink-2 sm:text-[1.125rem]">
            SearchMirror is a self-hostable rank tracker and AI-visibility
            monitor. Every check runs on a key you own — DataBlue for search,
            your own AI keys for assistant mentions — so you pay your providers
            directly and nothing on top of it.
          </p>

          <div className="mt-9 flex flex-col items-center gap-3 sm:flex-row">
            <ButtonLink href={SIGNUP_URL} size="lg" className="w-full sm:w-auto">
              Get started
              <ArrowRight aria-hidden="true" />
            </ButtonLink>
            <ButtonLink
              href={REPO_URL}
              rel="noreferrer noopener"
              variant="secondary"
              size="lg"
              className="w-full sm:w-auto"
            >
              <GitHubIcon />
              View on GitHub
            </ButtonLink>
          </div>

          {/* Anything laid directly over the grid is `--ink-2` or darker. A
              grid square at full opacity puts #d9d9d9 under the glyphs, where
              `--ink-3` falls to 3.61:1; `--ink-2` holds 7.46:1. Dropping the
              grid to the 0.06 opacity `--ink-3` would need makes it invisible.
              Text inside the sample card is unaffected — that card is opaque. */}
          <p className="mt-5 text-[13px] text-ink-2">
            No trial, no seat count, no card. Clone it and run it.
          </p>
        </div>

        <SampleTable />
      </div>
    </div>
  );
}

function SampleTable() {
  return (
    <div className="relative mx-auto mt-16 w-full max-w-[680px] md:mt-20">
      <Glow className="left-1/2 top-6 h-64 w-[26rem] -translate-x-1/2" />

      {/* The card is an illustration of the interface, filled with sample data.
          It is hidden from assistive tech and described once, in a sentence. */}
      <p className="sr-only">
        Illustration of the keyword table: four sample keywords with their
        current position and their change over seven days, and a footer showing
        that the run has happened and the search settings it used.
      </p>

      <div
        aria-hidden="true"
        className="overflow-hidden rounded-md border border-line bg-surface shadow-[0_1px_2px_rgba(15,15,16,0.04),0_18px_50px_-24px_rgba(15,15,16,0.28)]"
      >
        <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3.5">
          <span className="text-[13.5px] font-semibold tracking-display">
            Keywords
          </span>
          <span className="micro">4 of 4 checked today</span>
        </div>

        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="bg-surface-2">
              <th scope="col" className="px-5 py-2.5 text-micro font-semibold uppercase text-ink-3">
                Keyword
              </th>
              <th scope="col" className="px-3 py-2.5 text-right text-micro font-semibold uppercase text-ink-3">
                Pos
              </th>
              <th scope="col" className="px-5 py-2.5 text-right text-micro font-semibold uppercase text-ink-3">
                7d
              </th>
            </tr>
          </thead>
          <tbody>
            {SAMPLE.map(([keyword, position, delta, direction]) => (
              <tr key={keyword} className="border-t border-line-2">
                <td className="truncate px-5 py-3 text-[13.5px] text-ink-2">
                  {keyword}
                </td>
                <td className="num px-3 py-3 text-right text-[14px] font-semibold">
                  {position}
                </td>
                {/* The sign carries the direction; `--up` / `--down` reinforce
                    it. Keeping the numeral in `--ink` is what makes this legible
                    — the two rank colours are 2.6:1 and 4.4:1 as text on white. */}
                <td className="num px-5 py-3 text-right text-[13.5px] font-semibold">
                  <span
                    className={
                      "mr-1.5 align-[0.08em] text-[9px] " +
                      (direction === "up"
                        ? "text-up"
                        : direction === "down"
                          ? "text-down"
                          : "text-flat")
                    }
                  >
                    {direction === "up" ? "▲" : direction === "down" ? "▼" : "—"}
                  </span>
                  {delta}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-between gap-3 border-t border-line bg-surface px-5 py-3 text-[12.5px] text-ink-3">
          <span>Checked today</span>
          <span className="num">Google · Desktop · United Kingdom</span>
        </div>
      </div>
    </div>
  );
}
