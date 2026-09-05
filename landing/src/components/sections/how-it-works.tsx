import { Lede, MicroLabel, Section, SectionHeading } from "@/components/ui/section";

const STEPS: Array<[string, string, string]> = [
  [
    "Bring your keys",
    "Paste a DataBlue API key for search, and an AI provider key or two for visibility. The DataBlue key is checked against your account and its balance shown; every key is stored encrypted on your instance and sent nowhere but the provider it belongs to.",
    "~2 minutes",
  ],
  [
    "Add your domains",
    "One project per domain. Paste keywords or import a CSV, then set the country — 51 to choose from — plus the language, device and extraction depth once for the whole project.",
    "~5 minutes",
  ],
  [
    "Watch the balance",
    "Settings shows what DataBlue has left on your key, read from DataBlue itself. Depth stays at one page unless you raise it, so a keyword is a request and the arithmetic stays yours to check.",
    "Any time",
  ],
];

export function HowItWorks() {
  // A `--surface-2` band on the white ground, with `--surface` cards on top —
  // the pairing DESIGN.md specifies. This section was briefly inverted (white
  // band, paper cards) because `--ink-3` on the old warm `--surface-2` measured
  // 4.31:1, under rule 4's floor. The token is #f5f5f6 now and the same pair
  // measures 4.68:1, so the inversion is no longer needed.
  return (
    <Section id="how" labelledBy="how-heading" className="bg-surface-2">
      <div className="max-w-[46rem]">
        <MicroLabel>How it works</MicroLabel>
        <SectionHeading id="how-heading" className="max-w-[20ch]">
          Three steps, then it runs itself.
        </SectionHeading>
        <Lede>
          There is no onboarding call and no sales step, because there is nothing
          to sell you. Setup is the keys, the domains, and one depth setting that
          decides what a keyword costs.
        </Lede>
      </div>

      <ol className="mt-14 grid gap-5 md:grid-cols-3">
        {STEPS.map(([title, body, timing], index) => (
          <li
            key={title}
            className="flex flex-col rounded-md border border-line bg-surface p-6"
          >
            <div className="flex items-baseline justify-between gap-4">
              <span className="num text-[13px] font-semibold text-ink-3">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="micro">{timing}</span>
            </div>
            <h3 className="mt-6 text-[1.25rem] font-semibold tracking-display">
              {title}
            </h3>
            <p className="mt-3 text-[13.5px] leading-[1.6] text-ink-2">{body}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
