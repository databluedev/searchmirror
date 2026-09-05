const Frame = ({ children }) => <div
  aria-hidden="true"
  className="relative flex h-[122px] w-full items-center justify-center overflow-hidden rounded-sm border border-line bg-surface-2/60 px-4"
>
    {children}
  </div>;
function RankRowsArt() {
  const rows = [
    ["w-[58%]", "3", "text-up"],
    ["w-[74%]", "7", "text-up"],
    ["w-[40%]", "12", "text-down"]
  ];
  return <Frame>
      <div className="w-full space-y-2.5">
        {rows.map(([width, position, tone], i) => <div key={i} className="flex items-center gap-3 rounded-sm bg-surface px-3 py-2">
            <span className={`h-1.5 rounded-pill bg-ink-4/60 ${width}`} />
            <span className="num ml-auto text-[12px] font-semibold">{position}</span>
            <span className={`num text-[11px] font-semibold ${tone}`}>
              {tone === "text-up" ? "\u25B2" : "\u25BC"}
            </span>
          </div>)}
      </div>
    </Frame>;
}
function SparklineArt() {
  return <Frame>
      <svg viewBox="0 0 220 72" className="h-[72px] w-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity="0.18" />
            <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
    d="M0 58 L28 52 L56 55 L84 40 L112 44 L140 28 L168 30 L196 16 L220 12 L220 72 L0 72 Z"
    fill="url(#spark-fill)"
  />
        <path
    d="M0 58 L28 52 L56 55 L84 40 L112 44 L140 28 L168 30 L196 16 L220 12"
    fill="none"
    stroke="hsl(var(--accent))"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    vectorEffect="non-scaling-stroke"
  />
        <circle cx="196" cy="16" r="3.5" fill="hsl(var(--accent))" />
      </svg>
    </Frame>;
}
// An AI Overview answer block with the sources it cited under it; the first
// chip is the reader's own domain, which is the state the feature reports.
function AiOverviewArt() {
  const sources = [
    ["your-site.com", true],
    ["wikipedia.org", false],
    ["g2.com", false]
  ];
  return <Frame>
      <div className="w-full space-y-2.5">
        <div className="space-y-1.5 rounded-sm bg-surface px-3 py-2.5">
          <span className="block h-1.5 w-[92%] rounded-pill bg-ink-4/55" />
          <span className="block h-1.5 w-[78%] rounded-pill bg-ink-4/55" />
          <span className="block h-1.5 w-[45%] rounded-pill bg-ink-4/55" />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {sources.map(([label, owned]) => <span
            key={label}
            className={"rounded-pill px-2 py-0.5 text-[9.5px] font-semibold " + (owned ? "bg-ink text-white" : "bg-surface text-ink-3 ring-1 ring-inset ring-[color:var(--line)]")}
          >
              {label}
            </span>)}
        </div>
      </div>
    </Frame>;
}
function ImportArt() {
  const rows = ["seo rank tracker", "serp api pricing", "rank checker"];
  return <Frame>
      <div className="w-full space-y-2">
        <div className="flex items-center gap-2 rounded-sm bg-surface px-3 py-2">
          <span className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold text-ink-2">
            CSV
          </span>
          <span className="truncate text-[11px] text-ink-3">keywords.csv</span>
          <span className="num ml-auto text-[11px] font-semibold">248</span>
        </div>
        {rows.map((label) => <div
    key={label}
    className="flex items-center gap-2 rounded-sm bg-surface px-3 py-1.5"
  >
            <span className="h-1.5 w-1.5 shrink-0 rounded-pill bg-ink-4/60" />
            <span className="truncate text-[11px] text-ink-3">{label}</span>
          </div>)}
      </div>
    </Frame>;
}
function CompareBarsArt() {
  const series = [
    ["yours.com", "#1a3cff", "w-[82%]"],
    ["rival-one.com", "#009798", "w-[61%]"],
    ["rival-two.com", "#8a2a7a", "w-[38%]"]
  ];
  return <Frame>
      <div className="w-full space-y-3">
        {series.map(([label, colour, width]) => <div key={label} className="flex items-center gap-2.5">
            <span
    className="h-2 w-2 shrink-0 rounded-pill"
    style={{ backgroundColor: colour }}
  />
            <span className="w-[86px] shrink-0 truncate text-[11px] text-ink-3">
              {label}
            </span>
            <span className="h-2 flex-1 rounded-pill bg-surface">
              <span
    className={`block h-2 rounded-pill ${width}`}
    style={{ backgroundColor: colour }}
  />
            </span>
          </div>)}
      </div>
    </Frame>;
}
function ScheduleArt() {
  const days = ["M", "T", "W", "T", "F", "S", "S"];
  return <Frame>
      <div className="w-full space-y-3">
        <div className="flex justify-between gap-1.5">
          {days.map((day, i) => <span
    key={i}
    className={"flex h-7 flex-1 items-center justify-center rounded-sm text-[11px] font-semibold " + (i === 0 ? "bg-ink text-white" : "bg-surface text-ink-3")}
  >
              {day}
            </span>)}
        </div>
        <div className="flex items-center gap-2 rounded-sm bg-surface px-3 py-2">
          <span className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold text-ink-2">
            CSV
          </span>
          <span className="ml-auto text-[11px] text-ink-3">Weekly columns</span>
        </div>
      </div>
    </Frame>;
}
function RolesArt() {
  const members = [
    ["AM", "Owner", true],
    ["JR", "Editor", false],
    ["KP", "Viewer", false]
  ];
  return <Frame>
      <div className="w-full space-y-2">
        {members.map(([initials, role, owner]) => <div
    key={initials}
    className="flex items-center gap-2.5 rounded-sm bg-surface px-3 py-2"
  >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-pill bg-surface-2 text-[9px] font-semibold text-ink-2">
              {initials}
            </span>
            <span className="h-1.5 w-[38%] rounded-pill bg-ink-4/45" />
            <span
    className={"ml-auto rounded-pill px-2 py-0.5 text-[10px] font-semibold " + (owner ? "bg-ink text-white" : "bg-surface-2 text-ink-3 ring-1 ring-inset ring-[color:var(--line)]")}
  >
              {role}
            </span>
          </div>)}
      </div>
    </Frame>;
}
export {
  AiOverviewArt,
  CompareBarsArt,
  ImportArt,
  RankRowsArt,
  RolesArt,
  ScheduleArt,
  SparklineArt
};
