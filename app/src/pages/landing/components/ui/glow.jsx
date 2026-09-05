import { cn } from "../../lib/utils";
function Glow({ className }) {
  return <div
    aria-hidden="true"
    className={cn(
      "pointer-events-none absolute -z-10 rounded-full blur-[110px]",
      "bg-[radial-gradient(circle,hsl(var(--accent)/0.16),transparent_70%)]",
      className
    )}
  />;
}
export {
  Glow
};
