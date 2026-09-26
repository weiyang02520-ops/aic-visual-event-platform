import type { ReviewStatus, UnifiedEventContract } from "../../contracts";
import type { BackendApiClient } from "./client";

export function createEventsApi(client: BackendApiClient) {
  return {
    list: () => client.get<UnifiedEventContract[]>("/api/v1/events"),
    review: (eventId: string, status: ReviewStatus) => client.post<UnifiedEventContract>(`/api/v1/events/${encodeURIComponent(eventId)}/review`, { status }),
  };
}
