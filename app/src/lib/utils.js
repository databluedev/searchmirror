import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// The class-name helper every shadcn/ui component imports.
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
