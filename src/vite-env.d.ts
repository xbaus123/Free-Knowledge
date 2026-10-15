/// <reference types="vite/client" />

// Monaco internals imported for their side effects (see src/lib/monaco.ts).
// Modules with real .d.ts files, like editor.api, still get full types.
declare module "monaco-esm/*";

interface ImportMetaEnv {
  /** Engine token for `npm run dev:web` (browser-only UI development). */
  readonly VITE_FK_ENGINE_TOKEN?: string;
  readonly VITE_FK_ENGINE_PORT?: string;
}
