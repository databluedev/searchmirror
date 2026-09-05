import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));

// Migration of the CRA app to Vite. Everything here exists to keep a 2021-era
// CRA tree building unchanged -- no source rewrite, same MUI 5 / SCSS output.
export default defineConfig({
  plugins: [react()],

  // CRA's package.json sets "homepage": ".", which breaks deep routes because a
  // relative asset path on /projects asks for /projects/assets/... Serve from
  // the root instead, same as the CRA prod image does via PUBLIC_URL=/.
  base: '/',

  // 438 of the 487 source files put JSX inside .js. esbuild only parses JSX
  // from .jsx unless told otherwise, so point the loader at the whole src tree
  // rather than renaming every file.
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.jsx?$/,
    exclude: [],
  },

  optimizeDeps: {
    esbuildOptions: {
      // The dependency scanner crawls src/index.js -> App.js -> every page to
      // find bare imports. It runs its own esbuild pass that does not inherit
      // the `esbuild` option above, so it needs the JSX loader too.
      loader: { '.js': 'jsx' },
      // Same reason for `global`: pre-bundled deps are transformed by this
      // esbuild instance, not by Vite's define pass.
      define: { global: 'globalThis' },
    },
  },

  // src/index.js assigns global.apiurl, global.token, global.PageTopLoader and
  // ~30 other keys, and 227 files read them back -- 627 sites in total. webpack
  // shimmed `global`; the browser does not have it. Aliasing the identifier to
  // globalThis keeps every one of those sites working with no source edit.
  define: {
    global: 'globalThis',
  },

  resolve: {
    // Two consumers. shadcn/ui generates components that import from
    // "@/lib/utils"; and the shared SCSS sheet writes its asset paths as
    // "@/assets/..." because a relative one would break -- see the note at the
    // top of src/assets/styles/style.scss.
    alias: {
      '@': path.resolve(root, 'src'),
    },
  },

  css: {
    preprocessorOptions: {
      scss: {
        // sass-embedded's compiler API: the current, non-deprecated path, and
        // faster on a tree this size. It does NOT fix relative url() rebasing
        // inside @imported partials -- Vite compiles the entry with a file:
        // URL and no entry importer, so dart-sass resolves every relative
        // @import through its own filesystem importer and Vite's rebasing
        // importer is never called. Measured identical on Vite 6, 7 and 8.
        // That is why shared stylesheets here write "@/assets/...".
        api: 'modern-compiler',
        // The tree is entirely @import-based and still uses `/` for division
        // in places. Silence the migration noise rather than rewriting 47
        // stylesheets in what is a build-tooling change.
        silenceDeprecations: ['legacy-js-api', 'import', 'slash-div', 'global-builtin', 'color-functions'],
      },
    },
  },

  server: {
    host: true,
    port: 3000,
    strictPort: true,
    watch: {
      // Windows bind mounts do not propagate inotify into the container.
      // Same reason CRA needed CHOKIDAR_USEPOLLING here.
      usePolling: true,
      interval: 2000,
    },
    // In Docker the server listens on 3000 but the browser reaches it on the
    // published port, so the HMR socket has to be told which port to dial --
    // the CRA equivalent of WDS_SOCKET_PORT. Unset outside Docker, where the
    // listening port and the browser's port are the same.
    hmr: process.env.VITE_HMR_CLIENT_PORT
      ? { clientPort: Number(process.env.VITE_HMR_CLIENT_PORT) }
      : true,
  },

  preview: {
    host: true,
    port: 3000,
    strictPort: true,
  },

  build: {
    outDir: 'build',
    sourcemap: false,
    // CRA warned at 500 kB; MUI + apexcharts + exceljs + xlsx in one chunk is
    // legitimately larger than that.
    chunkSizeWarningLimit: 1500,
  },
});
