import { categoryOf, glyphOf, type GlyphKind, type ObjectCategory } from "./labels.ts";

export interface MemoryObjectInput {
  object_id: string;
  name: string;
  description: string;
  reference_uris: string[];
  status: string;
  created_at?: string;
}

export interface MemoryEventInput {
  event_id: string;
  plugin_id: string;
  title: string;
  source_id?: string;
  confidence?: number;
  started_at: string;
  ended_at: string;
  location?: string | null;
  review_status: string;
  object?: Record<string, unknown> | null;
}

export interface MemoryAppearance {
  event_id: string;
  title: string;
  at: string;
  location: string | null;
  plugin_id: string;
  review_status: string;
  source_id: string | null;
  confidence: number | null;
  /** "id": the event named this exact registry entry. "label": matched by name only. */
  matchedBy: "id" | "label";
  /** True when the event only gave a name that several registered objects share. */
  ambiguous: boolean;
}

export type MemoryStatus = "known" | "ambiguous" | "unknown";

export interface MemoryItem {
  object: MemoryObjectInput;
  category: ObjectCategory;
  glyph: GlyphKind;
  appearances: MemoryAppearance[];
  lastSeen: string | null;
  lastLocation: string | null;
  lastSource: string | null;
  pluginIds: string[];
  /** Other registered objects with the same name; kept as separate candidates, never merged. */
  sameLabel: string[];
  /** known: last position backed by an id match; ambiguous: only same-name evidence; unknown: never seen. */
  status: MemoryStatus;
}

function eventObjectId(event: MemoryEventInput): string {
  const target = event.object ?? {};
  return String(target.id ?? target.object_id ?? target.registry_id ?? "");
}

function eventObjectName(event: MemoryEventInput): string {
  const target = event.object ?? {};
  return String(target.label ?? target.name ?? "");
}

/** Event objects may carry a registry id or only a display label; both are accepted. */
export function eventMentionsObject(event: MemoryEventInput, object: MemoryObjectInput): boolean {
  const id = eventObjectId(event);
  const name = eventObjectName(event);
  return (id !== "" && id === object.object_id) || (name !== "" && name === object.name);
}

export function buildMemory(objects: MemoryObjectInput[], events: MemoryEventInput[]): MemoryItem[] {
  const byName = new Map<string, string[]>();
  objects.forEach((object) => byName.set(object.name, [...(byName.get(object.name) ?? []), object.object_id]));
  const ids = new Set(objects.map((object) => object.object_id));

  return objects.map((object) => {
    const siblings = (byName.get(object.name) ?? []).filter((id) => id !== object.object_id);
    const appearances: MemoryAppearance[] = events
      .filter((event) => eventMentionsObject(event, object))
      // An event that names a different registered id belongs to that object, not to every same-name sibling.
      .filter((event) => { const id = eventObjectId(event); return id === "" || id === object.object_id || !ids.has(id); })
      .map((event) => {
        const matchedBy = eventObjectId(event) === object.object_id ? "id" as const : "label" as const;
        return {
          event_id: event.event_id,
          title: event.title,
          at: event.ended_at || event.started_at,
          location: event.location ?? null,
          plugin_id: event.plugin_id,
          review_status: event.review_status,
          source_id: event.source_id ?? null,
          confidence: typeof event.confidence === "number" ? event.confidence : null,
          matchedBy,
          ambiguous: matchedBy === "label" && siblings.length > 0,
        };
      })
      .sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());

    const certain = appearances.filter((item) => !item.ambiguous);
    const anchor = certain[0] ?? null;
    const text = `${object.name} ${object.description}`;
    const eventCategory = events.filter((event) => eventMentionsObject(event, object)).map((event) => event.object?.category).find((value) => typeof value === "string");
    return {
      object,
      category: categoryOf(`${text} ${eventCategory ?? ""}`),
      glyph: glyphOf(text),
      appearances,
      // Location/time only come from evidence that is certainly about this object.
      lastSeen: anchor?.at ?? null,
      lastLocation: certain.find((item) => item.location)?.location ?? null,
      lastSource: anchor?.source_id ?? null,
      pluginIds: [...new Set(appearances.map((item) => item.plugin_id))],
      sameLabel: siblings,
      status: anchor ? "known" : appearances.length ? "ambiguous" : "unknown",
    };
  });
}
