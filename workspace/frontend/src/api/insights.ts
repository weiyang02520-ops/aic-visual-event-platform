import type { DetectorProviderStatusContract, ObservationViewContract } from "../contracts";
import { BackendApiClient } from "./backend";

/** `/ready` payload. Every field is optional because the frontend must tolerate partial readiness. */
export interface ReadinessContract {
  ready?: boolean;
  status?: string;
  database?: string;
  plugin_manager?: string;
  detector?: string;
  tracker?: string;
  plugins?: number;
}

/**
 * Read-only AI runtime endpoints that the legacy Repository interface does not
 * cover. They are only used in Real mode; Mock mode never calls them.
 */
export function createInsightsApi(baseUrl: string, timeoutMs = 8000) {
  const client = new BackendApiClient({ baseUrl, timeoutMs });
  return {
    ready: () => client.get<ReadinessContract>("/ready"),
    detectors: () => client.get<DetectorProviderStatusContract[]>("/api/v1/providers/detectors"),
    visionPreview: (source: string, maxFrames = 16) =>
      client.get<ObservationViewContract[]>(`/api/v1/vision/preview?source=${encodeURIComponent(source)}&max_frames=${maxFrames}`),
  };
}

export type InsightsApi = ReturnType<typeof createInsightsApi>;
