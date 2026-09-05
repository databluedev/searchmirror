import { Glow } from "../ui/glow";
import { HyperText } from "../ui/hyper-text";
import { Lede, MicroLabel, Section, SectionHeading } from "../ui/section";
import { useReducedMotion } from "../../hooks/use-reduced-motion";
const POINTS = [
  [
    "Your key, your quota",
    "Every check runs on your own DataBlue account. No reseller sits between you and the data, and no plan of ours caps how much of your own quota you may spend."
  ],
  [
    "One page is the default",
    "A keyword costs one DataBlue request per page of results, and one page is the default. Depth and Advanced extraction are both settings you turn up deliberately, never a surprise on the invoice."
  ],
  [
    "You can see the balance",
    "Settings reads your DataBlue account and shows what is left on it \u2014 plan, included, used this period. The figure comes from DataBlue, not from a ledger of ours."
  ],
  [
    "Seats are not a meter",
    "Add the whole team and every client you have. Neither one changes what you pay, because neither one costs us anything."
  ]
];
function Byok() {
  const reduced = useReducedMotion();
  return <Section id="byok" labelledBy="byok-heading">
      <div className="grid gap-14 lg:grid-cols-[1fr_minmax(0,26rem)] lg:items-start lg:gap-20">
        <div>
          <MicroLabel>Bring your own key</MicroLabel>
          <SectionHeading id="byok-heading">
            Your key. Your quota. Your invoice.
          </SectionHeading>
          <Lede>
            Most rank trackers buy SERP data wholesale and sell it to you by the
            keyword. The margin is the business, so the pricing page is built to
            hide it. SearchMirror does not resell anything: you connect your own
            DataBlue key and the calls are billed to you, at DataBlue's rate. The
            same rule holds for the AI keys behind the visibility checks — every
            call lands on an account you own, metered by nobody but your provider.
          </Lede>

          <dl className="mt-12 grid gap-x-10 gap-y-9 sm:grid-cols-2">
            {POINTS.map(([term, description]) => <div key={term}>
                <dt className="text-[15px] font-semibold tracking-display">
                  {term}
                </dt>
                <dd className="mt-2 text-[14px] leading-[1.6] text-ink-2">
                  {description}
                </dd>
              </div>)}
          </dl>
        </div>

        <div className="relative">
          <Glow className="right-0 top-0 h-72 w-72" />
          <div className="rounded-md border border-line bg-surface p-7 shadow-[0_1px_2px_rgba(15,15,16,0.04),0_18px_50px_-30px_rgba(15,15,16,0.25)]">
            {
    /* HyperText renders one span per glyph, which a screen reader would
       spell out. The readable string is given once, and the animated
       version is hidden from the accessibility tree. */
  }
            <p className="py-2 font-mono text-[2rem] font-bold leading-none tracking-display sm:text-[2.5rem]">
              <span className="sr-only">No markup.</span>
              {reduced ? <span aria-hidden="true">NO MARKUP</span> : <span aria-hidden="true">
                  <HyperText
    as="span"
    startOnView
    animateOnHover={false}
    duration={900}
    className="block py-0 text-[2rem] leading-none tracking-display sm:text-[2.5rem]"
  >
                    NO MARKUP
                  </HyperText>
                </span>}
            </p>

            <p className="mt-4 text-[14px] leading-[1.6] text-ink-2">
              What one keyword check costs you, in full:
            </p>

            <dl className="mt-6 divide-y divide-line-2 border-y border-line text-[13.5px]">
              <div className="flex items-baseline justify-between gap-4 py-3">
                <dt className="text-ink-2">DataBlue SERP call</dt>
                <dd className="num font-semibold">1 credit</dd>
              </div>
              <div className="flex items-baseline justify-between gap-4 py-3">
                <dt className="text-ink-2">SearchMirror's share of it</dt>
                <dd className="num font-semibold">0</dd>
              </div>
              <div className="flex items-baseline justify-between gap-4 py-3">
                <dt className="text-ink-2">Per-seat charge</dt>
                <dd className="num font-semibold">0</dd>
              </div>
            </dl>

            <p className="mt-6 text-[12.5px] leading-[1.6] text-ink-3">
              SearchMirror never sees your key on any server but yours when you
              self-host, and never bills a call to an account you do not own.
            </p>
          </div>
        </div>
      </div>
    </Section>;
}
export {
  Byok
};
