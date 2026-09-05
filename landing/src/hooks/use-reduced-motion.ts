import { useEffect, useState } from "react";

/**
 * DESIGN.md rule 5. The two vendored magicui animations (typing, flickering
 * grid) drive themselves from timers and requestAnimationFrame, so a CSS
 * `transition-duration: 0` override cannot reach them. Components read this and
 * render their finished state instead of starting the animation at all.
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });

  useEffect(() => {
    if (!window.matchMedia) return;
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(query.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  return reduced;
}
