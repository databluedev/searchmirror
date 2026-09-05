import { cn } from "../../lib/utils";
function Section({
  id,
  className,
  children,
  labelledBy
}) {
  return <section
    id={id}
    aria-labelledby={labelledBy}
    className={cn("relative border-t border-line", className)}
  >
      <div className="mx-auto w-full max-w-[1360px] px-6 py-20 md:px-8 md:py-28">
        {children}
      </div>
    </section>;
}
function MicroLabel({
  children,
  className
}) {
  return <span className={cn("micro", className)}>{children}</span>;
}
function SectionHeading({
  id,
  children,
  className
}) {
  return <h2
    id={id}
    className={cn(
      "mt-5 max-w-[18ch] text-balance text-[2rem] font-semibold leading-[1.05] tracking-display sm:text-[2.5rem] lg:text-[3rem]",
      className
    )}
  >
      {children}
    </h2>;
}
function Lede({
  children,
  className
}) {
  return <p className={cn("mt-5 max-w-[58ch] text-[1.0625rem] leading-[1.6] text-ink-2", className)}>
      {children}
    </p>;
}
export {
  Lede,
  MicroLabel,
  Section,
  SectionHeading
};
