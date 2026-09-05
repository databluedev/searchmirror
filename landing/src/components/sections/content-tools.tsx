import { Glow } from "@/components/ui/glow";
import { Lede, MicroLabel, Section, SectionHeading } from "@/components/ui/section";

// Only advertise content tools that are actually routed in the open-source
// product. `needs` names the user-owned credential required for generation.
const TOOLS: Array<{ title: string; body: string; needs: string | null }> = [
  {
    title: "Content Planner",
    body: "Plan an article around a primary keyword and the secondaries you pick, then have your own AI provider draft it in the built-in editor. Nothing is generated without a key of yours.",
    needs: "your AI provider key",
  },
];

export function ContentTools() {
  return (
    <Section id="content" labelledBy="content-heading">
      <Glow className="left-0 top-24 h-[24rem] w-[24rem]" />

      <div className="max-w-[46rem]">
        <MicroLabel>Content</MicroLabel>
        <SectionHeading id="content-heading" className="max-w-[22ch]">
          From keyword to draft, on a key you own.
        </SectionHeading>
        <Lede>
          Content Planner starts with the projects and keywords you already
          track. Drafting runs on your own OpenAI, Anthropic, Perplexity or
          Gemini key, so no SERP credit is spent and no key of ours is involved.
        </Lede>
      </div>

      <ul className="mt-14 max-w-[46rem]">
        {TOOLS.map(({ title, body, needs }) => (
          <li
            key={title}
            className="flex flex-col rounded-md border border-line bg-surface p-6"
          >
            <h3 className="text-[15px] font-semibold tracking-display">{title}</h3>
            <p className="mt-2 flex-1 text-[13.5px] leading-[1.6] text-ink-2">
              {body}
            </p>
            <span
              className={
                "mt-6 inline-flex w-fit items-center gap-1.5 rounded-pill px-2.5 py-1 text-[11px] font-semibold " +
                (needs
                  ? "bg-surface-2 text-ink-3 ring-1 ring-inset ring-[color:var(--line)]"
                  : "bg-ink text-white")
              }
            >
              <span
                className={"h-1.5 w-1.5 rounded-pill " + (needs ? "bg-ink-4" : "bg-white")}
              />
              {needs ? `Needs ${needs}` : "Runs on your SERP key"}
            </span>
          </li>
        ))}
      </ul>
    </Section>
  );
}
