import {
  AiOverviewArt,
  CompareBarsArt,
  ImportArt,
  RankRowsArt,
  RolesArt,
  ScheduleArt,
  SparklineArt
} from "./feature-art";
import { Glow } from "../ui/glow";
import { Lede, MicroLabel, Section, SectionHeading } from "../ui/section";
const FEATURES = [
  {
    title: "Rank tracking",
    body: "Positions on Google for the region, language and device you choose. The bundled scheduler runs them overnight, and Refresh runs them now. One page of results is the default depth, and the Search Visibility Score rolls the whole set into one figure you can watch move.",
    Art: RankRowsArt
  },
  {
    title: "Keyword-level history",
    body: "Every check is kept. Open a keyword and read its whole line \u2014 when it moved and how far \u2014 beside the Google snippet the result is showing now and the best one it has had.",
    Art: SparklineArt
  },
  {
    title: "AI Overview tracking",
    body: "At Advanced depth a check also records whether Google answered with an AI Overview and which sites it cited. The keyword page shows the answer Google gave and the sources behind it, so you can see whether you are in it.",
    Art: AiOverviewArt
  },
  {
    title: "Projects and bulk import",
    body: "One project per domain. Paste a list or upload a CSV, and set the country, language, device and SERP depth once for everything in it.",
    Art: ImportArt
  },
  {
    title: "Competitor comparison",
    body: "SearchMirror reads your SERPs to find who actually ranks for your keywords, then puts your domain and its rivals on one axis, same checks, same day. Same scale, so the gap is real.",
    Art: CompareBarsArt
  },
  {
    title: "Reports and CSV export",
    body: "Build a rank or overview sheet from the checks you already have, read it in the app, and export the keyword table to CSV when you want it out. The bundled scheduler only runs rank checks, so nothing is mailed out on a timer unless you wire one up yourself.",
    Art: ScheduleArt
  },
  {
    title: "Team access and roles",
    body: "Add the people who need it and give each a role. Permissions are per module and per project, and they fail closed \u2014 an unmapped screen is denied, not allowed.",
    Art: RolesArt
  }
];
function Features() {
  return <Section id="features" labelledBy="features-heading">
      <Glow className="right-0 top-24 h-[26rem] w-[26rem]" />

      <div className="max-w-[46rem]">
        <MicroLabel>What it does</MicroLabel>
        <SectionHeading id="features-heading" className="max-w-[22ch]">
          Seven things it actually does.
        </SectionHeading>
        <Lede>
          The tracking half of the product: what ranks, what moved, who else is
          there, and who on your team may see it. None of it is metered by us,
          and none of it is behind a tier.
        </Lede>
      </div>

      <ul className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(({ title, body, Art }) => <li
    key={title}
    className="group flex flex-col rounded-md border border-line bg-surface p-5 transition-all duration-fast ease-brand hover:-translate-y-1 hover:border-accent/40 hover:shadow-[0_14px_32px_-18px_rgba(15,15,16,0.28)]"
  >
            <Art />
            <h3 className="mt-5 text-[15px] font-semibold tracking-display transition-colors duration-fast group-hover:text-accent">
              {title}
            </h3>
            <p className="mt-2 text-[13.5px] leading-[1.6] text-ink-2">{body}</p>
          </li>)}
      </ul>
    </Section>;
}
export {
  Features
};
