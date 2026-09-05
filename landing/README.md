# landing

The public marketing page for SearchMirror. A separate app on purpose: `app/` is
React 18 + Vite + MUI 5 + SCSS, which cannot host Tailwind or the shadcn registry.

Vite 5 · React 18 · TypeScript 5.8 · Tailwind 3.4 · shadcn/ui + magicui ·
lucide-react.

```bash
pnpm install
pnpm dev      # http://localhost:5180
pnpm build    # -> dist/
pnpm preview
```

Design tokens come from `docs/DESIGN.md` and live in `src/index.css` as CSS
custom properties, mirrored into `tailwind.config.ts`. No hex literals in
components; the one exception is the categorical chart hues in
`src/components/sections/feature-art.tsx`, which are the app's own chart palette.

`src/lib/site.ts` holds every outbound link. **`REPO_URL` is still a placeholder
and must be set before this page is published** — it is the href behind every
"View on GitHub" button, and the licence, docs and issues links derive from it.

Nothing is fetched from a third party: Space Grotesk is self-hosted from
`public/fonts`, the favicon is served from `public/` (source: `brand/`), the mark
is inline SVG, and there is no analytics of any kind (`docs/DESIGN.md`, rule 7).

`index.html`'s `theme-color` has to be kept in step with `--paper` by hand —
nothing enforces it.

## Keeping it honest

Every claim on this page has to be true of the shipped product. Two were not and
were removed: a **client portal** (deleted in migration `0006_remove_client_portal`)
and **SERP-feature tracking** (the live parser writes an empty `SNIPPETS` list on
every check, so every feature flag is permanently false, and AI Overviews are not
implemented in any layer). A per-run credit meter was also claimed; the product
shows the DataBlue account balance in settings and nothing else, so the copy now
says that instead.

This page and `app/src/pages/landing/` are two builds of the same marketing
story. Change one, change the other.
