import { useEffect, useMemo, useState } from "react";
import type { RegisteredObjectContract, UnifiedEventContract } from "../../contracts";
import { eventReferencesObject, toEventContract, toObjectContract } from "../../api";
import type { Plugin, RegisteredObject, UnifiedEvent } from "../../types";
import { ObjectDetail } from "./ObjectDetail";
import { ObjectList } from "./ObjectList";
import type { ObjectMemoryItem } from "./types";

function categoryFor(object: RegisteredObjectContract) {
  const text = `${object.name} ${object.description}`.toLowerCase();
  if (/药|medicine|pill/.test(text)) return "用药物品";
  if (/工具|电钻|扳手|tool|drill/.test(text)) return "工具设备";
  return "关注物品";
}

function latestEvent(events: UnifiedEventContract[]) {
  return events.reduce<string | null>((latest, event) => {
    if (!latest || new Date(event.ended_at).getTime() > new Date(latest).getTime()) return event.ended_at;
    return latest;
  }, null);
}

function pluginNamesFor(events: UnifiedEventContract[], plugins: Plugin[]) {
  const names = new Set<string>();
  events.forEach((event) => {
    const plugin = plugins.find((item) => item.plugin_id === event.plugin_id);
    names.add(plugin?.name ?? event.plugin_id);
  });
  return [...names];
}

export function ObjectMemoryPanel({ objects, events, plugins }: { objects: RegisteredObject[]; events: UnifiedEvent[]; plugins: Plugin[] }) {
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const contractObjects = useMemo(() => objects.map(toObjectContract), [objects]);
  const contractEvents = useMemo(() => events.map(toEventContract), [events]);
  const items = useMemo<ObjectMemoryItem[]>(() => contractObjects.map((object) => {
    const relatedEvents = contractEvents.filter((event) => eventReferencesObject(event, object)).sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
    return { object, category: categoryFor(object), relatedPluginNames: pluginNamesFor(relatedEvents, plugins), relatedEvents, lastSeen: latestEvent(relatedEvents) };
  }), [contractEvents, contractObjects, plugins]);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return items;
    return items.filter((item) => [item.object.object_id, item.object.name, item.object.description, item.category, ...item.relatedPluginNames].join(" ").toLowerCase().includes(normalized));
  }, [items, query]);
  const selected = items.find((item) => item.object.object_id === selectedId) ?? null;

  useEffect(() => {
    if (!selectedId || !items.some((item) => item.object.object_id === selectedId)) setSelectedId(items[0]?.object.object_id ?? null);
  }, [items, selectedId]);

  return <section className="object-memory-workspace">
    <ObjectList items={filtered} selectedId={selectedId} query={query} onQuery={setQuery} onSelect={setSelectedId} />
    <ObjectDetail item={selected} onClear={() => setSelectedId(null)} />
  </section>;
}
