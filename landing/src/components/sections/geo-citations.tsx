import { Glow } from "@/components/ui/glow";
import { Lede, MicroLabel, Section, SectionHeading } from "@/components/ui/section";

// The signals a Geo Citations run records for each prompt. Kept honest — these
// are read from the assistants' own answers on the operator's AI keys.
const SIGNALS: Array<[string, string]> = [
  [
    "Mention rate over time",
    "How often the assistants name you, tracked run over run so you can watch a change take hold instead of guessing at it.",
  ],
  [
    "Sentiment",
    "Whether a mention is positive, neutral or negative. A citation that warns people off is not the same as one that recommends you.",
  ],
  [
    "Prominence",
    "How early in the answer you appear. Named in the first sentence reads very differently from a footnote at the end.",
  ],
  [
    "Top cited sources",
    "The pages the models lean on when they answer for your prompts, so you know which sources are worth earning a place in.",
  ],
  [
    "Competitor mentions",
    "The same prompts, scored for the brands that come up instead of you — the AI-side of who you are up against.",
  ],
  [
    "Suggested prompts",
    "The model proposes prompts a real buyer would ask, so your set starts from how people actually search, not a guess.",
  ],
];

// Illustrative state for the sample card. `true` means the assistant named the
// brand for the prompt on the last run.
const ASSISTANTS: Array<[string, boolean]> = [
  ["ChatGPT", true],
  ["Perplexity", true],
  ["Claude", true],
  ["Gemini", false],
];

const READOUT: Array<[string, string, string | null, "up" | "down" | null]> = [
  ["Mention rate", "62%", "+8", "up"],
  ["Sentiment", "Positive", null, null],
  ["Prominence", "Named 2nd", null, null],
];

const SOURCES = ["g2.com", "reddit.com/r/SEO", "your-blog.com"];

export function GeoCitations() {
  return (
    <Section id="geo" labelledBy="geo-heading">
      <div className="grid gap-14 lg:grid-cols-[1fr_minmax(0,26rem)] lg:items-start lg:gap-20">
        <div>
          <MicroLabel>AI visibility · Geo Citations</MicroLabel>
          <SectionHeading id="geo-heading">
            The other half of search doesn&rsquo;t rank.
          </SectionHeading>
          <Lede>
            More buyers now ask an assistant instead of scrolling a results
            page, and the assistant answers in prose with a handful of brands
            named inside it. Geo Citations runs your prompts through ChatGPT,
            Claude, Gemini and Perplexity whenever you run them, and records whether one
            of those brands is you — on your own AI keys, so the run is yours.
          </Lede>

          <dl className="mt-12 grid gap-x-10 gap-y-9 sm:grid-cols-2">
            {SIGNALS.map(([term, description]) => (
              <div key={term}>
                <dt className="text-[15px] font-semibold tracking-display">
                  {term}
                </dt>
                <dd className="mt-2 text-[14px] leading-[1.6] text-ink-2">
                  {description}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="relative">
          <Glow className="right-0 top-0 h-72 w-72" />

          {/* The card illustrates one prompt's visibility across the four
              assistants, filled with sample data and hidden from assistive
              tech — the section text carries the meaning. */}
          <p className="sr-only">
            Illustration of a prompt visibility card: for one prompt, three of
            four assistants named the brand, with a 62 percent mention rate up 8
            points, positive sentiment, second-place prominence, and three top
            cited sources.
          </p>

          <div
            aria-hidden="true"
            className="rounded-md border border-line bg-surface p-7 shadow-[0_1px_2px_rgba(15,15,16,0.04),0_18px_50px_-30px_rgba(15,15,16,0.25)]"
          >
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-[13.5px] font-semibold tracking-display">
                Prompt visibility
              </span>
              <span className="micro">last 30 days</span>
            </div>

            <p className="mt-4 rounded-sm bg-surface-2 px-3 py-2.5 text-[13px] leading-[1.5] text-ink-2">
              &ldquo;best seo rank tracker for agencies&rdquo;
            </p>

            <div className="mt-4 flex flex-wrap gap-2">
              {ASSISTANTS.map(([label, named]) => (
                <span
                  key={label}
                  className={
                    "inline-flex items-center gap-1.5 rounded-pill px-2.5 py-1 text-[11px] font-semibold " +
                    (named
                      ? "bg-ink text-white"
                      : "bg-surface text-ink-3 ring-1 ring-inset ring-[color:var(--line)]")
                  }
                >
                  <span
                    className={
                      "h-1.5 w-1.5 rounded-pill " + (named ? "bg-white" : "bg-ink-4")
                    }
                  />
                  {label}
                </span>
              ))}
            </div>

            <dl className="mt-6 divide-y divide-line-2 border-y border-line text-[13.5px]">
              {READOUT.map(([term, value, delta, direction]) => (
                <div
                  key={term}
                  className="flex items-baseline justify-between gap-4 py-3"
                >
                  <dt className="text-ink-2">{term}</dt>
                  <dd className="num font-semibold">
                    {value}
                    {delta ? (
                      <span
                        className={
                          "ml-1.5 align-[0.08em] text-[11px] font-semibold " +
                          (direction === "up" ? "text-up" : "text-down")
                        }
                      >
                        <span className="mr-0.5 text-[9px]">
                          {direction === "up" ? "▲" : "▼"}
                        </span>
                        {delta}
                      </span>
                    ) : null}
                  </dd>
                </div>
              ))}
            </dl>

            <p className="mt-5 text-[12px] font-semibold uppercase tracking-display text-ink-3">
              Top cited sources
            </p>
            <ul className="mt-2.5 space-y-1.5">
              {SOURCES.map((source) => (
                <li
                  key={source}
                  className="flex items-center gap-2 text-[12.5px] text-ink-2"
                >
                  <span className="h-1.5 w-1.5 shrink-0 rounded-pill bg-ink-4/60" />
                  <span className="num truncate">{source}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Section>
  );
}
