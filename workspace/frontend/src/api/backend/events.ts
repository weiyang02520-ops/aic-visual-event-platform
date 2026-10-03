import type { ReviewStatus, UnifiedEventContract } from "../../contracts";
import type { BackendApiClient } from "./client";

export function createEventsApi(client: BackendApiClient) {
  return {
    list: () => client.get<UnifiedEventContract[]>("/api/v1/events"),
    review: async (eventId: string, status: ReviewStatus) => {
      const path = `/api/v1/events/${encodeURIComponent(eventId)}/review`;
      await client.patch<void>(path, { status });
      // Makerverse returns 204 for the update, while the frontend repository
      // contract returns the refreshed event to update local state.
      return client.get<UnifiedEventContract>(`/api/v1/events/${encodeURIComponent(eventId)}`);
    },
  };
}
