import * as React from "react";
import { cn } from "@/lib/utils";

// Text input on the app's tokens. Height and radius match the legacy field so a
// shadcn form and an MUI form line up during the transition.
//
// `border-[1px] border-solid` rather than `border`: preflight is off, so the
// border style is whatever the user agent says, and Bootstrap also defines a
// class called `border` as the shorthand `border: 1px solid #dee2e6`, which
// repaints the colour wherever its stylesheet lands after the Tailwind output.
// See the note in button.jsx.
//
// Focus is the contract in docs/DESIGN.md, "Input": --accent border plus a 3px
// --accent-weak ring. The ring was missing -- the field only changed its border
// colour, which is a 1px signal. It is a box-shadow rather than Tailwind's
// `ring-*`: those utilities read --tw-ring-offset-shadow and friends, which are
// declared in the base layer, and this build has no base layer (preflight is
// off and tailwind.css pulls only components and utilities), so a ring would
// emit a colour and no shadow.
const Input = React.forwardRef(({ className, type = "text", ...props }, ref) => (
  <input
    type={type}
    ref={ref}
    className={cn(
      "h-[38px] w-full rounded-sm border-[1px] border-solid border-line bg-surface px-3 text-[14px] text-ink",
      "placeholder:text-ink-4 focus:outline-none focus:border-accent focus:shadow-[0_0_0_3px_var(--accent-weak)] disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";

export { Input };
