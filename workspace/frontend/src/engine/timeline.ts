/** Recent-action timeline built from event facts (frozen contract §5). Pure, no React. */

export interface TimelineFactInput {
  fact_type: string;
  confidence: number;
  location?: string | null;
  timestamp?: string;
  subject?: Record<string, unknown> | null;
  object?: Record<string, unknown> | null;
  metadata?: Record<string, unknown>;
}

export interface TimelineEventInput {
  event_id: string;
  title: string;
  source_id: string;
  started_at: string;
  ended_at: string;
  location?: string | null;
  subject?: Record<string, unknown> | null;
  object?: Record<string, unknown> | null;
  facts: TimelineFactInput[];
}

export interface TimelineEntry {
  id: string;
  event_id: string;
  event_title: string;
  fact_type: string;
  at: string;
  /** False when the fact had no own timestamp and its time was spread across the event window. */
  exactTime: boolean;
  confidence: number;
  location: string | null;
  subject: string | null;
  object: string | null;
  source_id: string;
  segment: number | null;
}

/**
 * Detections only update location memory; they are not actions (contract §5).
 * Everything else is kept, including zone transitions and candidates.
 */
const NON_ACTIONS = new Set(["object_detected", "person_detected", "person_present", "scene_observed"]);

const PERSON_ONLY = new Set(["person_entered_zone", "motion"]);

function text(value: Record<string, unknown> | null | undefined): string | null {
  const label = value?.label ?? value?.name ?? value?.id ?? value?.track_id;
  return label === undefined || label === null || label === "" ? null : String(label);
}

function segmentOf(fact: TimelineFactInput): number | null {
  const raw = fact.metadata?.continuity_segment;
  return typeof raw === "number" && Number.isFinite(raw) ? raw : null;
}

export function buildTimeline(events: TimelineEventInput[]): TimelineEntry[] {
  const entries: TimelineEntry[] = [];
  events.forEach((event) => {
    const start = new Date(event.started_at).getTime();
    const end = new Date(event.ended_at).getTime();
    const span = Number.isFinite(end - start) ? Math.max(0, end - start) : 0;
    const count = event.facts.length;
    event.facts.forEach((fact, index) => {
      if (NON_ACTIONS.has(fact.fact_type)) return;
      const own = fact.timestamp && !Number.isNaN(new Date(fact.timestamp).getTime()) ? fact.timestamp : null;
      const at = own ?? new Date(start + (count > 1 ? (span * index) / (count - 1) : 0)).toISOString();
      const source = fact.metadata?.source_id;
      entries.push({
        id: `${event.event_id}:${index}`,
        event_id: event.event_id,
        event_title: event.title,
        fact_type: fact.fact_type,
        at,
        exactTime: Boolean(own),
        confidence: fact.confidence,
        location: fact.location ?? event.location ?? null,
        subject: text(fact.subject) ?? text(event.subject),
        // Person-only facts must not inherit the event's object (entering a room is not about the pill box).
        object: text(fact.object) ?? (PERSON_ONLY.has(fact.fact_type) ? null : text(event.object)),
        source_id: typeof source === "string" && source ? source : event.source_id,
        segment: segmentOf(fact),
      });
    });
  });
  // Newest first, like TemporalVisualMemory.recent_actions().
  return entries.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
}

export interface TimelineFilter {
  factTypes?: Set<string>;
  subject?: string | null;
  object?: string | null;
}

export function filterTimeline(entries: TimelineEntry[], filter: TimelineFilter): TimelineEntry[] {
  return entries.filter((entry) =>
    (!filter.factTypes || filter.factTypes.size === 0 || filter.factTypes.has(entry.fact_type))
    && (!filter.subject || entry.subject === filter.subject)
    && (!filter.object || entry.object === filter.object));
}

export interface TimelineGroup {
  key: string;
  source_id: string;
  segment: number | null;
  entries: TimelineEntry[];
}

/**
 * Group by source and continuity segment. Facts from different cameras, or
 * from before/after an observation gap, are never presented as one sequence.
 */
export function groupTimeline(entries: TimelineEntry[]): TimelineGroup[] {
  const groups = new Map<string, TimelineGroup>();
  entries.forEach((entry) => {
    const key = `${entry.source_id}#${entry.segment ?? "-"}`;
    const group = groups.get(key) ?? { key, source_id: entry.source_id, segment: entry.segment, entries: [] };
    group.entries.push(entry);
    groups.set(key, group);
  });
  return [...groups.values()];
}
