// /prompt/citations/:id -- the detail view for one model answer.
//
// This module used to carry a second copy of the Geo Citations list page and
// only fall through to the detail view when the route had an `:id`. The route
// always has one, so that copy was unreachable, yet its effect still fired
// /getsetting and /llmtracker/list on every citation view. The list lives in
// pages/llmTracker; this route renders the detail page and nothing else.
export { default } from "./citations_page";
