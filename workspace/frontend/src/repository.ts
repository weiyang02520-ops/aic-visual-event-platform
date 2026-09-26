import type { Repository } from "./types";
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
