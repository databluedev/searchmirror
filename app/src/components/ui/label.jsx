import * as React from "react";
import { cn } from "@/lib/utils";

// Field label -- the small, muted caption above an input.
const Label = React.forwardRef(({ className, ...props }, ref) => (
  <label
    ref={ref}
    className={cn("text-[12.5px] font-semibold text-ink-3", className)}
    {...props}
  />
));
Label.displayName = "Label";

export { Label };
