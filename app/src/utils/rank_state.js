/**
 * How a keyword's position is read and worded, in one place.
 *
 * The API used to send 101 for every keyword that did not rank, whatever the
 * reason. Three different facts arrived as one number:
 *
 *   - checked, and the domain was not in the pages fetched
 *   - checked, and the provider returned nothing usable
 *   - never checked at all
 *
 * Only the first is a measurement. And 101 was not even the right ceiling: the
 * default depth is three pages of ten, so a keyword that did not appear was
 * absent from the first 30 -- which is why the export rendered the same value
 * as ">30" while the history chart plotted it as 101.
 *
 * The API now sends, per row (see backend/serp/rank_state.py):
 *
 *   RW   the position, ONLY when the keyword ranks; null otherwise
 *   RS   "ranked" | "out_of_range" | "not_measured" | "never_checked"
 *   RC   the ceiling actually searched, e.g. 30
 *   RSK  a numeric sort key -- for ordering and filtering, never for display
 *
 * Read RS first, always. An unrecognised or missing state is treated as "not
 * measured", so a row from an older payload shows "we don't know" rather than
 * a position nobody observed.
 */

export const RANKED = "ranked";
export const OUT_OF_RANGE = "out_of_range";
export const NOT_MEASURED = "not_measured";
export const NEVER_CHECKED = "never_checked";

// Mirrors SORT_FLOOR in backend/serp/rank_state.py.
const SORT_FLOOR = 100000;

/** The state of one row, defaulting safely for anything unrecognised. */
export function rankState(row) {
   if (!row) return NOT_MEASURED;
   const state = row.RS;
   if (state === RANKED || state === OUT_OF_RANGE || state === NEVER_CHECKED) {
      return state;
   }
   if (state === NOT_MEASURED) return NOT_MEASURED;
   // No RS at all: fall back to RW, which is a real position or nothing.
   return typeof row.RW === "number" && row.RW > 0 ? RANKED : NOT_MEASURED;
}

/** True only when there is a real, observed position to do arithmetic with. */
export function isRanked(row) {
   return rankState(row) === RANKED && typeof row.RW === "number" && row.RW > 0;
}

/** The depth searched for this keyword, for wording an out-of-range result. */
export function rankCeiling(row) {
   const ceiling = row && row.RC;
   return typeof ceiling === "number" && ceiling > 0 ? ceiling : null;
}

/**
 * What to print in a position cell.
 *
 * `short` is for narrow columns, where there is room for "> 30" but not for a
 * sentence. Both say the same thing; neither prints a number the product did
 * not measure.
 */
export function rankLabel(row, short) {
   const state = rankState(row);
   if (state === RANKED) return String(row.RW);

   const ceiling = rankCeiling(row);
   if (state === OUT_OF_RANGE) {
      if (!ceiling) return short ? "Not ranked" : "Did not rank in the pages checked";
      return short ? "> " + ceiling : "Not in the first " + ceiling;
   }
   if (state === NEVER_CHECKED) return short ? "—" : "Not checked yet";
   return short ? "—" : "Could not be checked";
}

/** Why the cell says what it says, for a tooltip. */
export function rankExplanation(row) {
   const state = rankState(row);
   const ceiling = rankCeiling(row);
   if (state === RANKED) return "";
   if (state === OUT_OF_RANGE) {
      return ceiling
         ? "Checked. The domain was not in the first " + ceiling + " results, which is the depth this keyword is tracked at."
         : "Checked. The domain was not in the results fetched.";
   }
   if (state === NEVER_CHECKED) {
      return "This keyword has not been checked yet, so it has no position either way.";
   }
   return "The last check produced no usable result, so this keyword has no current position. Its previous rank is unchanged.";
}

/** Ordering value. Never render this -- unranked rows sort past every rank. */
export function rankSortKey(row) {
   if (!row) return SORT_FLOOR;
   if (typeof row.RSK === "number") return row.RSK;
   return isRanked(row) ? row.RW : SORT_FLOOR;
}
