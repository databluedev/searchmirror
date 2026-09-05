import * as React from "react";

import { cn } from "@/lib/utils";

/** Page rhythm: 80px of vertical air on small screens, 112px from md up. */
export function Section({
  id,
  className,
  children,
  labelledBy,
}: {
  id?: string;
  className?: string;
  children: React.ReactNode;
  labelledBy?: string;
}) {
  return (
    <section
      id={id}
      aria-labelledby={labelledBy}
      className={cn("relative border-t border-line", className)}
    >
      <div className="mx-auto w-full max-w-[1200px] px-6 py-20 md:px-8 md:py-28">
        {children}
      </div>
    </section>
  );
}

/** Bracketed uppercase micro-label. Brackets are drawn by CSS, not typed. */
export function MicroLabel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <span className={cn("micro", className)}>{children}</span>;
}

export function SectionHeading({
  id,
  children,
  className,
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h2
      id={id}
      className={cn(
        "mt-5 max-w-[18ch] text-balance text-[2rem] font-semibold leading-[1.05] tracking-display sm:text-[2.5rem] lg:text-[3rem]",
        className,
      )}
    >
      {children}
    </h2>
  );
}

export function Lede({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p className={cn("mt-5 max-w-[58ch] text-[1.0625rem] leading-[1.6] text-ink-2", className)}>
      {children}
    </p>
  );
}
