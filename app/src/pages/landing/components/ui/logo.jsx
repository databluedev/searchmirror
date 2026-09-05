import { cn } from "../../lib/utils";
import logoDark from "../../../../assets/images/logo-dark.png";
// The SearchMirror mark. brand/logo-mark.svg is the source of truth; this PNG
// is the master raster it was traced from, and is what the rest of the app
// loads, so the marketing header and the app rail draw the same file.
function LogoMark({ className }) {
  return <img
    src={logoDark}
    alt="SearchMirror"
    className={cn("h-6 w-6 object-contain", className)}
  />;
}
function Wordmark({ className }) {
  // Metrics match .brandWord in assets/styles/modules/_shell.scss and
  // .authBrand__word in pages/welcome/style.scss: 600 with "Search" dropped to
  // 500 / --ink-3, tracking -0.02em. tracking-display (-0.035em) is for
  // headings; using it here made the logotype set tighter on the marketing
  // page than the identical lockup one click later inside the product.
  return <span className={cn("flex items-center gap-2.5", className)}>
      <LogoMark />
      <span className="text-[17px] font-semibold tracking-[-0.02em] text-ink">
        <span className="font-medium text-ink-3">Search</span>Mirror
      </span>
    </span>;
}
function GitHubIcon({ className }) {
  return <svg
    viewBox="0 0 16 16"
    className={cn("h-4 w-4", className)}
    fill="currentColor"
    aria-hidden="true"
    focusable="false"
  >
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>;
}
export {
  GitHubIcon,
  LogoMark,
  Wordmark
};
