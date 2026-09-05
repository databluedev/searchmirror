import React from "react";

/* docs/DESIGN.md, "Loading". The product has exactly two loading idioms:
 *
 *   - the top progress line (App.js mounts it once, driven through
 *     `global.PageTopLoader`) for a page-level fetch whose result has no shape
 *     yet -- the competitors page is the one that qualifies, because one status
 *     call there decides between five different screens;
 *   - a --surface-2 skeleton in the shape of the content it replaces, for
 *     anything whose shape IS known -- a table, a card, a stat row.
 *
 * Everything else -- MUI's CircularProgress, a centred `.loading` bar on an
 * otherwise blank h100vh, a "Loading..." string -- was a third, fourth and
 * fifth idiom, and the app mixed several of them on one route.
 *
 * The classes below are the ones routeComponents/private_route.js already
 * paints for its React.lazy fallback (_shell.scss, "skeletons"), so a page that
 * fetches on mount continues the shape the route fallback started rather than
 * swapping to a different object mid-load.
 *
 * A skeleton has to match what replaces it -- same rough height, same column
 * count -- or the page jumps when the data lands, which is worse than no
 * skeleton at all. Every measurement passed in below was taken off the loaded
 * page in a 1440px browser, not estimated: a react-data-table row is 52px and
 * its header row is 41px, the Geo insight cards are 276px, the search strip
 * above a table is 38px.
 */

/* One bone. `width`/`height` are inline because they are per-site
   measurements, not a design decision worth a class each; the colour and the
   shimmer come from .skeleton (_shell.scss / _motion.scss) and are never
   overridden. */
export function Bone({ className = "", width, height, style }) {
   const cls = className ? "skeleton " + className : "skeleton";
   return <div className={cls} style={{ width, height, ...style }} aria-hidden="true" />;
}

/* A table card: the header rule plus `rows` body rows, inside the same raised
   surface the real table sits on. Flat bones on the page background read as a
   different object from the card that lands on top of them. */
export function TableBones({ rows = 6, rowHeight = 52, headHeight = 41 }) {
   return (
      <div className="pageSkeleton__table">
         <div className="skeleton skeleton--row skeleton--row-head" style={{ height: headHeight }} />
         {Array.from({ length: rows }).map((row, i) => (
            <div key={i} className="skeleton skeleton--row" style={{ height: rowHeight }} />
         ))}
      </div>
   );
}

/* The page title, the subtitle line under it, and the primary action. */
export function HeadBones() {
   return (
      <div className="pageSkeleton__head">
         <div className="pageSkeleton__title">
            <div className="skeleton skeleton--title" />
            <Bone width="300px" height="14px" />
         </div>
         <div className="skeleton skeleton--action" />
      </div>
   );
}

/* The search box and its two icon buttons that sit above every list table. */
export function SearchBones() {
   return (
      <div className="pageSkeleton__search">
         <Bone width="250px" height="38px" />
         <Bone width="38px" height="38px" />
         <Bone width="38px" height="38px" />
      </div>
   );
}

/* `count` cards on one row -- the stat strip, or any equal-width card row.
   .pageSkeleton__stats is a 4-up grid that drops to 2-up then 1-up, so a row of
   2 cards is expressed by overriding the column count rather than by a second
   grid class. */
export function CardBones({ count = 4, height }) {
   const style = count === 4 ? undefined : { gridTemplateColumns: `repeat(${count}, minmax(0, 1fr))` };
   return (
      <div className="pageSkeleton__stats" style={style}>
         {Array.from({ length: count }).map((card, i) => (
            <div key={i} className="skeleton skeleton--stat" style={height ? { height } : undefined} />
         ))}
      </div>
   );
}

/* The whole page. Every section is opt-in so each page describes its own
   shape; `children` covers the pages that are not head/cards/search/table. */
export default function PageSkeleton({
   label = "Loading",
   head = true,
   cards = 0,
   cardHeight,
   search = false,
   rows = 0,
   rowHeight,
   className,
   children,
}) {
   return (
      <div className={className ? "layout " + className : "layout"} role="status" aria-live="polite" aria-busy="true">
         <div className="pageSkeleton" aria-hidden="true">
            {head ? <HeadBones /> : null}
            {cards > 0 ? <CardBones count={cards} height={cardHeight} /> : null}
            {search ? <SearchBones /> : null}
            {children}
            {rows > 0 ? <TableBones rows={rows} rowHeight={rowHeight} /> : null}
         </div>
         {/* Last, not first. `.layout > * + *` (_modern.scss) puts 32px above
             every child after the first, so a leading label -- even an
             absolutely-positioned, visually-hidden one -- pushes the whole
             skeleton 32px below where the real header lands, and the page
             jumps up the moment the data arrives. */}
         <span className="visually-hidden">{label}</span>
      </div>
   );
}
