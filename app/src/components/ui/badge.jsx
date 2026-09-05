import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Pill badge. Semantic variants map to the app's status tokens (up/down/accent)
// so a mention chip or a "Connected" dot reads the same across shadcn and legacy
// screens.
const badgeVariants = cva(
  "inline-flex items-center rounded-pill px-2.5 py-0.5 text-[12px] font-semibold leading-none",
  {
    variants: {
      variant: {
        default: "bg-surface-2 text-ink-3",
        up: "bg-surface-2 text-up",
        down: "bg-surface-2 text-down",
        accent: "bg-accent-weak text-accent",
        solid: "bg-up text-white",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

function Badge({ className, variant, ...props }) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
