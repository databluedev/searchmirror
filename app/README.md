# Tracker frontend (Vite)

The same application as `../app`, built with Vite instead of Create React App.
React 18, MUI 5 and the SCSS tree are unchanged; only the build tooling differs.
Tailwind and shadcn/ui are available alongside MUI.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` (or `npm start`) | Dev server on :3000, HMR |
| `npm run build` | Production bundle into `build/` |
| `npm run preview` | Serve `build/` locally |

`VITE_API_URL` selects the API host. Only `VITE_`-prefixed variables reach
`import.meta.env`; the CRA build read `REACT_APP_API_URL`.

## Docker

| Service | Port | Mode |
|---|---|---|
| `app` (`tracker-app`) | 3001 | dev server, source bind-mounted |
| `app-prod` (`tracker-app-prod`) | 4001 | `vite build` served by nginx (`--profile prod`) |

## Things that are not obvious

- **JSX lives in `.js` files.** 438 of them. `vite.config.js` points the esbuild
  loader at `src/**/*.js` instead of renaming the tree, and repeats the setting
  under `optimizeDeps.esbuildOptions` because the dependency scanner runs its
  own esbuild pass.
- **`global` is aliased to `globalThis`.** `src/index.js` hangs ~30 config keys
  off `global` and 227 files read them back. `define` handles the production
  build; in dev Vite injects the same alias through `/@vite/env`.
- **SCSS asset paths must be written `@/assets/...`, never relative.** Fifteen
  page stylesheets `@import` the whole global sheet. dart-sass resolves relative
  `@import`s with its own filesystem importer, so Vite never sees those partials
  and cannot rebase their `url()`s -- a relative path would resolve against
  whichever page inlined the sheet and 404. The `@` alias resolves the same from
  any depth. This is true of Vite 6, 7 and 8 alike.
- **Sass is `sass-embedded` on `api: 'modern-compiler'`**, not `node-sass`. That
  is for currency and speed, not for url rebasing -- see the point above.
- **Tailwind runs with `preflight: false`.** Its reset would fight MUI's
  baseline. Content globs deliberately exclude `src/assets/styles/**` so the JIT
  scanner never sees legacy or MUI class names. Note that legacy `!important`
  rules in the SCSS tree still beat Tailwind utilities.
- **`.npmrc` pins `legacy-peer-deps`.** `react-apexcharts` declares a peer on
  `apexcharts>=4` while this tree is pinned to 3.
- **LF line endings only** -- see the repo `.gitattributes`.
