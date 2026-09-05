import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-pill text-[13.5px] font-semibold transition-all duration-fast ease-brand disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-ink text-white hover:bg-accent hover:-translate-y-0.5 hover:shadow-[0_10px_26px_-12px_rgba(26,60,255,0.55)]",
        secondary: "bg-surface text-ink hairline hover:-translate-y-0.5 hover:border-[color:var(--ink-4)] hover:shadow-[0_10px_26px_-16px_rgba(15,15,16,0.3)]",
        ghost: "text-ink-2 hover:bg-surface-2 hover:text-ink"
      },
      size: {
        default: "h-[38px] px-[18px]",
        lg: "h-12 px-7 text-[15px]"
      }
    },
    defaultVariants: { variant: "primary", size: "default" }
  }
);
const Button = React.forwardRef(
  ({ className, variant, size, ...props }, ref) => <button
    ref={ref}
    className={cn(buttonVariants({ variant, size }), className)}
    {...props}
  />
);
Button.displayName = "Button";
const ButtonLink = React.forwardRef(
  ({ className, variant, size, ...props }, ref) => <a
    ref={ref}
    className={cn(buttonVariants({ variant, size }), className)}
    {...props}
  />
);
ButtonLink.displayName = "ButtonLink";
export {
  Button,
  ButtonLink,
  buttonVariants
};
