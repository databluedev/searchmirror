import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Canonical app-wide button. Styled with the app's design tokens (bg-ink,
// bg-surface, bg-accent, hairline) so a shadcn/ui screen and a legacy MUI screen
// render the same greys and the same blue. Tailwind preflight is off, so this
// coexists with MUI without either resetting the other.
//
// Preflight being off has two consequences this file has to answer for itself,
// because nothing else will:
//
//  1. `border-style` keeps the user-agent value. On a <button> that is
//     `outset`, at the UA's 2px width -- which is why every one of these
//     rendered with a grey bevel. Tailwind's `border` utility sets width only,
//     so the width and the style are both stated here, explicitly.
//  2. The class named `border` is also a Bootstrap utility, and Bootstrap's
//     version is the shorthand `border: 1px solid #dee2e6`. Wherever
//     _bootstrap.scss lands after the Tailwind output -- which route-level
//     lazy chunks make likely -- that shorthand repaints the colour, and a
//     `border-line` on the same element cannot outrank it. `border-[1px]`
//     produces a class name Bootstrap does not define, so the collision is
//     gone rather than won on ordering.
//
// Radius is `rounded-pill`: docs/DESIGN.md, "Button -- pill (--r-pill)". It was
// rounded-sm (8px) here while the MUI theme computed 999px for the same button
// on the next screen.
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-pill border-[1px] border-solid border-transparent text-[13.5px] font-semibold transition-colors duration-fast ease-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-ink text-white hover:bg-ink-hover",
        accent: "bg-accent text-white hover:opacity-90",
        secondary: "bg-surface text-ink border-line hover:bg-surface-2",
        ghost: "text-ink-2 hover:bg-surface-2 hover:text-ink",
        danger: "bg-down text-white hover:opacity-90",
      },
      size: {
        default: "h-[38px] px-[18px]",
        sm: "h-8 px-3 text-[12.5px]",
        lg: "h-12 px-7 text-[15px]",
        icon: "h-[38px] w-[38px]",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  }
);

const Button = React.forwardRef(({ className, variant, size, ...props }, ref) => (
  <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
));
Button.displayName = "Button";

export { Button, buttonVariants };
