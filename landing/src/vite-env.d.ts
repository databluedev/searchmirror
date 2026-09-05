/// <reference types="vite/client" />

// Typed so `import.meta.env.VITE_APP_ORIGIN` is not `any` and a typo in the
// name is a build error rather than an undefined at runtime.
interface ImportMetaEnv {
  readonly VITE_APP_ORIGIN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
