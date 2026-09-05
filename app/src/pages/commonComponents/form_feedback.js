import { toast } from 'react-toastify';

// One way to report a blocked submit, used by every form in the app.
//
// A long form can push its first invalid field far below the fold, so an
// inline message on its own reads as "the button did nothing". Every
// validation branch therefore does the same three things: keeps its inline
// message on the field, raises a toast naming what is missing, and brings the
// offending field into view with focus on it so keyboard and screen-reader
// users get the same signal.

const FOCUSABLE = [
   'input:not([type="hidden"]):not([disabled])',
   'select:not([disabled])',
   'textarea:not([disabled])',
   'button:not([disabled])',
   '[tabindex]:not([tabindex="-1"])',
].join(', ');

const prefersReducedMotion = () =>
   typeof window !== 'undefined' &&
   typeof window.matchMedia === 'function' &&
   window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Accepts a ref, a raw node, or nothing at all -- a form that has not wired a
// ref to the failing field still gets the toast.
const resolveNode = (field) => {
   if (!field) return null;
   const node = Object.prototype.hasOwnProperty.call(field, 'current') ? field.current : field;
   return node && typeof node.scrollIntoView === 'function' ? node : null;
};

export function focusInvalidField(field) {
   const node = resolveNode(field);
   if (!node) return;

   const reveal = () => {
      node.scrollIntoView({
         behavior: prefersReducedMotion() ? 'auto' : 'smooth',
         block: 'center',
         inline: 'nearest',
      });

      const target = typeof node.matches === 'function' && node.matches(FOCUSABLE)
         ? node
         : node.querySelector(FOCUSABLE);

      if (target) {
         // preventScroll keeps focus from jumping ahead of the smooth scroll.
         try {
            target.focus({ preventScroll: true });
         } catch (err) {
            target.focus();
         }
      }
   };

   // Wait for the paint that renders the error state, so focus lands on a
   // control that already carries aria-invalid.
   if (typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function') {
      window.requestAnimationFrame(reveal);
   } else {
      reveal();
   }
}

export function revealFormError(message, field) {
   if (message) {
      toast.error(message);
   }
   focusInvalidField(field);
}
