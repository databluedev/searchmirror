import { FlickeringGrid } from "./flickering-grid";
import { useReducedMotion } from "../../hooks/use-reduced-motion";
import { cn } from "../../lib/utils";
function BackgroundGrid({ className }) {
  const reduced = useReducedMotion();
  return <div
    aria-hidden="true"
    className={cn(
      "pointer-events-none absolute inset-0 grid-fade select-none",
      className
    )}
  >
      {reduced ? <div className="static-grid h-full w-full" /> : <FlickeringGrid
    className="h-full w-full"
    squareSize={4}
    gridGap={6}
    flickerChance={0.24}
    color="#0f0f10"
    maxOpacity={0.1}
  />}
    </div>;
}
export {
  BackgroundGrid
};
