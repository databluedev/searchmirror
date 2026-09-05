import * as React from "react";
import { cn } from "@/lib/utils";

// Hairline card on --surface, the app's standard container. Tokens only, so it
// matches the legacy `.card`/widget surfaces exactly during the MUI -> shadcn
// transition.
//
// `border-[1px] border-solid` rather than `border`: Bootstrap defines a class
// of that name as the shorthand `border: 1px solid #dee2e6`, which repaints the
// hairline wherever its stylesheet lands after the Tailwind output, and
// preflight -- which is what normally sets border-style -- is off. See the note
// in button.jsx.
const Card = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-md border-[1px] border-solid border-line bg-surface", className)} {...props} />
));
Card.displayName = "Card";

const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col gap-1 p-4", className)} {...props} />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h3 ref={ref} className={cn("text-[15px] font-semibold leading-tight text-ink", className)} {...props} />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p ref={ref} className={cn("text-[13px] text-ink-3", className)} {...props} />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-4 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex items-center p-4 pt-0", className)} {...props} />
));
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
