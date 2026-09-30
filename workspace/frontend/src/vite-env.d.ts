/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AI_API_URL?: string;
  /** Source passed to /api/v1/vision/preview for the Real privacy stage, e.g. a local video path. */
  readonly VITE_AI_PREVIEW_SOURCE?: string;
  readonly VITE_MAKERVERSE_API_URL?: string;
  readonly VITE_MAKERVERSE_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
