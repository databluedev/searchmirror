/* Text that came from the SERP provider, made safe to put in the DOM.

   DataBlue leaves markup in the strings it sends -- an AI Overview source title
   arrives as "<b>ScraperAPI</b> Review: Honest..." -- and leaves whole blocks
   null rather than empty: serp_features.ai_overview.raw is literally null on
   every keyword whose SERP had no AI answer. Rendering either one straight
   prints markup at the reader or the word "null" in place of a value.

   Both readers of ai_overview -- the keyword panel and the keywords table --
   go through here so the two cannot drift. */

// Tags stripped, entities decoded, anything that is not a string -> "".
// Never produces HTML: the output is only ever used as a text child.
export const plainText = (value) => {
   if (typeof value !== "string") {
      return "";
   }
   return value
      .replace(/<[^>]*>/g, "")
      .replace(/&nbsp;/g, " ")
      .replace(/&quot;/g, '"')
      .replace(/&#0*39;|&apos;/g, "'")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      // last, so a decoded "&amp;lt;" cannot become a tag
      .replace(/&amp;/g, "&")
      .replace(/\s+/g, " ")
      .trim();
};

// Only a real web link is ever put in an href; anything else renders as text.
export const safeHref = (value) => {
   const link = typeof value === "string" ? value.trim() : "";
   return /^https?:\/\//i.test(link) ? link : "";
};
