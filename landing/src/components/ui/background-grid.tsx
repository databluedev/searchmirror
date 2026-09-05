import { FlickeringGrid } from "@/components/ui/flickering-grid";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { cn } from "@/lib/utils";

/**
 * The hero backdrop. Decorative, so it is hidden from assistive tech and never
 * takes pointer events.
 *
 * Under `prefers-reduced-motion: reduce` the canvas is not mounted at all — the
 * grid's requestAnimationFrame loop is driven in JS and a CSS duration override
 * cannot stop it. The `.static-grid` fallback is the same 4px square on the same
 * 10px pitch, held still.
 */
export function BackgroundGrid({ className }: { className?: string }) {
  const reduced = useReducedMotion();

  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute inset-0 grid-fade select-none",
        className,
      )}
    >
      {reduced ? (
        <div className="static-grid h-full w-full" />
      ) : (
        <FlickeringGrid
          className="h-full w-full"
          squareSize={4}
          gridGap={6}
          flickerChance={0.24}
          color="#0f0f10"
          maxOpacity={0.16}
        />
      )}
    </div>
  );
}
