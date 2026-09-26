import { useMemo, useState } from "react";
import type { ReviewStatus, UnifiedEventContract } from "../../contracts";
import type { UnifiedEvent } from "../../types";
import { EventDetail } from "./EventDetail";
import { EventList } from "./EventList";

function toContract(event: UnifiedEvent): UnifiedEventContract {
  return {
    ...event,
    facts: event.facts.map((fact) => ({ ...fact })),
    metadata: { ...event.metadata },
    evidence: event.evidence.map((evidence) => ({ ...evidence })),
  };
}

export function EventCenter({ events, onReview }: { events: UnifiedEvent[]; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ReviewStatus | "all">("all");
  const [selected, setSelected] = useState<UnifiedEventContract | null>(null);
  const contractEvents = useMemo(() => events.map(toContract), [events]);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return contractEvents.filter((event) => {
      if (status !== "all" && event.review_status !== status) return false;
      if (!normalized) return true;
      return [event.title, event.description, event.plugin_id, event.source_id, event.location ?? "", String(event.object?.label ?? ""), String(event.subject?.label ?? "")]
        .join(" ").toLowerCase().includes(normalized);
    });
  }, [contractEvents, query, status]);
  async function review(event: UnifiedEventContract, nextStatus: ReviewStatus) {
    const original = events.find((item) => item.event_id === event.event_id);
    if (original) await onReview(original, nextStatus);
  }
  return <><EventList events={filtered} query={query} status={status} onQuery={setQuery} onStatus={setStatus} onSelect={setSelected} onReview={review} />{selected && <EventDetail event={selected} onClose={() => setSelected(null)} onReview={review} />}</>;
}
