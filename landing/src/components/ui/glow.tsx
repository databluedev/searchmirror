import { cn } from "@/lib/utils";

/**
 * The blue-violet wash from the reference layouts. One hue only — `--accent`,
 * the same blue the app reserves for links and focus — so the page still reads
 * as near-monochrome. Decorative and never behind body text.
 */
export function Glow({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute -z-10 rounded-full blur-[110px]",
        "bg-[radial-gradient(circle,hsl(var(--accent)/0.16),transparent_70%)]",
        className,
      )}
    />
  );
}
