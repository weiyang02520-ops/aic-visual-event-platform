import { Activity, ArrowUpRight, Box, ClipboardCheck, Network, Sparkles } from "lucide-react";
import type { PluginContract } from "../contracts";
import type { RegisteredObject, UnifiedEvent } from "../types";
import { getPluginPresentation, pluginLifecycleLabel } from "./registry";

function iconFor(kind: ReturnType<typeof getPluginPresentation>["icon"]) {
  return kind === "medicine" ? ClipboardCheck : kind === "object" ? Box : Network;
}

function reviewLabel(status: string) {
  return status === "pending" ? "待确认" : status === "confirmed" ? "已记录" : status === "rejected" ? "已驳回" : status;
}

function timeLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

export function PluginRuntimeCard({ plugin, events, objects, onToggle, stretch }: {
  plugin: PluginContract;
  events: UnifiedEvent[];
  objects: RegisteredObject[];
  onToggle: (pluginId: string) => Promise<void>;
  stretch: boolean;
}) {
  const presentation = getPluginPresentation(plugin);
  const Icon = iconFor(presentation.icon);
  return <section className={`privacy-info-card plugin-live-card ${stretch ? "stretch" : ""}`}>
    <div className="privacy-card-heading">
      <div><Icon size={20} /><strong>{presentation.label}</strong><span className={`enabled-pill plugin-state-${plugin.state}`}><i />{pluginLifecycleLabel(plugin.state)}</span></div>
      <button className="plugin-inline-toggle" onClick={() => onToggle(plugin.plugin_id)}>{plugin.enabled ? "停用" : "启用"}</button>
    </div>
    {presentation.kind === "medicine" ? <MedicineContent events={events} /> : presentation.kind === "object" ? <ObjectContent events={events} objects={objects} /> : <div className="plugin-generic-state"><Sparkles size={18} /><span>{plugin.description || "该插件已注册，等待事件输出。"}</span></div>}
  </section>;
}

function MedicineContent({ events }: { events: UnifiedEvent[] }) {
  return <div className="plugin-live-list">{events.length ? events.map((event) => <div className="plugin-live-row" key={event.event_id}><div className="plugin-live-thumb medicine-thumb" /><div><span>{timeLabel(event.started_at)}</span><strong>{event.title}</strong></div><em>{reviewLabel(event.review_status)}</em></div>) : <div className="plugin-card-empty"><Activity size={16} />等待用药相关事件</div>}</div>;
}

function ObjectContent({ events, objects }: { events: UnifiedEvent[]; objects: RegisteredObject[] }) {
  if (!objects.length) return <div className="plugin-card-empty"><Box size={16} />暂无关注对象</div>;
  return <div className="plugin-live-list">{objects.slice(0, 3).map((object, index) => {
    const related = events.find((event) => String(event.object?.label ?? "") === object.name || String(event.object?.id ?? "") === object.object_id);
    return <div className="plugin-live-row object-row" key={object.object_id}><div className={`plugin-live-thumb ${index % 2 === 0 ? "medicine-thumb" : "water-thumb"}`} /><div><strong>{object.name}</strong><span>{related?.location ? `最近位置：${related.location}` : "等待位置事实"}</span></div><ArrowUpRight size={15} /></div>;
  })}</div>;
}
