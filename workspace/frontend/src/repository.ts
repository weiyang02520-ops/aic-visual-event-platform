import type { Mode, Repository } from "./types";
import { createMockAdapter, createRealAdapter } from "./api";

/**
 * Compatibility entry point kept for existing App.tsx callers.
 * New frontend code should import adapters from `src/api` directly.
 */
export function createMockRepository(): Repository {
  return createMockAdapter();
}

export function createRealRepository(baseUrl: string): Repository {
  return createRealAdapter(baseUrl);
}

/** Explicit provider switch used by callers that need to construct a source outside App. */
export function createRepository(mode: Mode, baseUrl = "http://127.0.0.1:8010"): Repository {
  return mode === "mock" ? createMockRepository() : createRealRepository(baseUrl);
}
