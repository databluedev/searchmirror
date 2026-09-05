import React, { useEffect, useMemo, useState } from "react";
import Cookies from "universal-cookie";

// SiteMark -- the icon shown next to a tracked domain.
//
// The icon comes from this instance's own API, never from the site it depicts.
// Loading `https://<domain>/favicon.ico` in the browser is fine for the one
// domain the account owns and a privacy leak for every other one: /competitors
// renders a mark for each discovered competitor, so opening that page fired ~47
// requests to third-party SEO vendors -- several of them direct competitors of
// this product -- handing each of them the user's IP, User-Agent and referrer.
// One visit left eight third-party cookies in the profile. A self-hosted
// tracker must not phone home to anybody, least of all on the user's behalf
// without their knowing, so the backend fetches and caches the icon and the
// browser only ever talks to SearchMirror.
//
// When the proxy has nothing to give -- 204, an error, a deadline, a domain
// that will not parse -- the component paints a letter tile instead, generated
// here, so the fallback is fully offline and there is never a broken-image
// glyph on screen.
//
// Both the tile and the proxied icon are carried by the same <img> element,
// deliberately: every existing stylesheet sizes these icons through `img`
// selectors and width/height attributes, and swapping the element for a <span>
// would silently drop all of it.

// Tile colours and radius live in _tokens.scss. Read them out of the cascade so
// this component holds no literal of its own, and memoise once they resolve.
let tileStyle = null;

function readTileStyle() {
   if (tileStyle) return tileStyle;
   if (typeof window === "undefined" || !window.getComputedStyle) {
      return { bg: "", ink: "", radius: 0 };
   }
   const root = window.getComputedStyle(document.documentElement);
   const style = {
      bg: root.getPropertyValue("--surface-2").trim(),
      ink: root.getPropertyValue("--ink-3").trim(),
      // --r-sm is an absolute px radius for a control of ordinary size; the tile
      // is drawn in a 64-unit box and scaled by CSS, so the token rides along as
      // 64ths and keeps its proportion at every call site.
      radius: parseFloat(root.getPropertyValue("--r-sm")) || 0,
   };
   if (style.bg && style.ink) tileStyle = style;
   return style;
}

// prjt.D_N and its siblings are inconsistent -- bare domains, full URLs with a
// protocol and a path, and the occasional empty string or label. Reduce all of
// them to a hostname, and return "" for anything that will not parse.
export function siteHost(value) {
   if (typeof value !== "string") return "";
   const raw = value.trim();
   if (!raw) return "";
   let host = "";
   try {
      const absolute = /^[a-z][a-z0-9+.-]*:\/\//i.test(raw) ? raw : "https://" + raw;
      host = new URL(absolute).hostname;
   } catch (err) {
      return "";
   }
   // A hostname with no dot is a label, not a site -- "Overall", "All domains".
   return host.indexOf(".") > 0 ? host : "";
}

function siteInitial(host) {
   const letter = host.replace(/^www\./i, "").charAt(0).toUpperCase();
   return /[A-Z0-9]/.test(letter) ? letter : "";
}

function letterTile(initial) {
   const { bg, ink, radius } = readTileStyle();
   const rect = bg
      ? '<rect width="64" height="64" rx="' + radius + '" fill="' + bg + '"/>'
      : "";
   const text =
      ink && initial
         ? '<text x="32" y="44" text-anchor="middle" fill="' +
           ink +
           '" font-family="Space Grotesk, sans-serif" font-size="34" font-weight="600">' +
           initial +
           "</text>"
         : "";
   const svg =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">' + rect + text + "</svg>";
   return "data:image/svg+xml," + encodeURIComponent(svg);
}

// An <img> carries no deadline of its own, and neither does a fetch. A request
// that black-holes -- a proxy still waiting on an upstream that no longer
// resolves, a firewalled network -- would otherwise hang indefinitely: `onError`
// never fires, the tile never gets its turn, and the row reads as permanently
// loading. Worse at this scale, the browser allows only a handful of concurrent
// connections per origin, so a page of stalled icon requests would starve the
// app's own API calls. Give every fetch a deadline instead of trusting the
// network to fail.
const ICON_TIMEOUT_MS = 6000;

// The deadline is only honest if it measures the request rather than the wait
// in front of it: /competitors asks for ~47 icons at once, and with no gate the
// browser would queue most of them past their own timers and fall every one of
// them back to a tile. Admit a few at a time and start each clock when its
// request actually goes out.
const MAX_IN_FLIGHT = 6;
let inFlight = 0;
const waiting = [];

function runQueued(task) {
   return new Promise((resolve) => {
      const start = () => {
         inFlight += 1;
         resolve(
            task().finally(() => {
               inFlight -= 1;
               const next = waiting.shift();
               if (next) next();
            })
         );
      };
      if (inFlight < MAX_IN_FLIGHT) start();
      else waiting.push(start);
   });
}

// An <img> cannot set an Authorization header, and the proxy requires one --
// tokens travel in that header rather than a cookie precisely so a third-party
// page cannot forge an authenticated request, and the API is a separate origin
// in every shipped compose file, so a cookie would not be sent cross-site
// anyway. Putting the token in the src query string would write it into browser
// history, referrers and every access log. So fetch the bytes with the same
// header the rest of the app uses and hand the <img> a same-origin blob.
async function fetchIcon(host) {
   const token = new Cookies().get("session_token");
   if (!token) return "";
   const controller = new AbortController();
   const timer = setTimeout(() => controller.abort(), ICON_TIMEOUT_MS);
   try {
      const response = await fetch(
         global.apiurl + "/site-icon?domain=" + encodeURIComponent(host),
         {
            signal: controller.signal,
            // No ambient credentials: the header above is the whole story.
            credentials: "omit",
            headers: { Authorization: "Token " + token },
         }
      );
      // 204 is the contract's "no icon"; 404 covers an instance whose backend
      // predates the endpoint. Everything else that is not a plain 200 -- 401,
      // 5xx, a redirect that lands somewhere odd -- takes the same path.
      if (response.status !== 200) return "";
      const blob = await response.blob();
      if (!blob.size || !/^image\//i.test(blob.type)) return "";
      return URL.createObjectURL(blob);
   } catch (err) {
      // Aborted, offline, CORS, malformed body. The tile covers all of it.
      return "";
   } finally {
      clearTimeout(timer);
   }
}

// One request per distinct host, not per rendered mark: a competitor table
// repeats the same domain across many rows, and the project switcher renders
// the marks the projects list already drew. Failures are cached alongside
// successes so a backend that is down cannot be re-asked once per row.
const MAX_CACHED_ICONS = 256;
const iconCache = new Map();

function loadIcon(host) {
   const cached = iconCache.get(host);
   if (cached) return cached;
   const pending = runQueued(() => fetchIcon(host));
   iconCache.set(host, pending);
   if (iconCache.size > MAX_CACHED_ICONS) {
      // Map iterates in insertion order, so the first key is the oldest. Its
      // blob has long since been decoded by any <img> still showing it; the URL
      // is released so the bytes can be collected.
      const oldest = iconCache.keys().next().value;
      const evicted = iconCache.get(oldest);
      iconCache.delete(oldest);
      evicted.then((url) => {
         if (url) URL.revokeObjectURL(url);
      });
   }
   return pending;
}

// `alt` and `onError` are swallowed on purpose: the mark is decorative next to
// a domain name that is already on screen, and the fallback is handled here.
export function SiteMark({ domain, alt, onError, ...props }) {
   const host = useMemo(() => siteHost(domain), [domain]);
   const tile = useMemo(() => letterTile(siteInitial(host)), [host]);
   // "" means the tile is showing -- the starting state, so nothing renders
   // blank or broken while the proxy is asked, and the resting state for every
   // domain the proxy cannot serve.
   const [icon, setIcon] = useState("");

   useEffect(() => {
      setIcon("");
      if (!host) return undefined;
      let live = true;
      loadIcon(host).then((url) => {
         if (live && url) setIcon(url);
      });
      return () => {
         live = false;
      };
   }, [host]);

   // Bytes that arrived with an image content type can still fail to decode.
   // Dropping back to the tile is safe from a loop: the tile is a data URI, and
   // with it in place there is no handler left to fire.
   return (
      <img
         {...props}
         src={icon || tile}
         alt=""
         onError={icon ? () => setIcon("") : undefined}
      />
   );
}

export default SiteMark;
