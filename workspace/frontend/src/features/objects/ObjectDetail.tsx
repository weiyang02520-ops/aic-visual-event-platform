import { Activity, CalendarClock, Image, Link2, ShieldCheck, Tag, X } from "lucide-react";
import type { ObjectMemoryItem } from "./types";

function dateLabel(value: string | null | undefined) {
  if (!value) return "接口未提供";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN", { hour12: false });
}

function reviewLabel(status: string) {
  return status === "pending" ? "待复核" : status === "confirmed" ? "已确认" : status === "rejected" ? "已驳回" : status;
}

export function ObjectDetail({ item, onClear }: { item: ObjectMemoryItem | null; onClear?: () => void }) {
  if (!item) return <aside className="panel object-memory-detail object-memory-detail-empty"><BoxPlaceholder /><strong>选择一个对象</strong><span>从左侧列表查看注册信息与关联事件。</span></aside>;
  const { object, relatedEvents } = item;
  return <aside className="panel object-memory-detail">
    <div className="panel-heading object-detail-heading"><div><span className="panel-kicker">OBJECT DETAIL / {item.category}</span><h2>{object.name}</h2></div>{onClear && <button className="icon-button object-detail-close" onClick={onClear} aria-label="清除对象选择"><X size={15} /></button>}</div>
    <div className="object-detail-status"><span className="object-status active"><i />{object.status}</span><span className="object-detail-id">{object.object_id}</span></div>
    <p className="object-detail-description">{object.description || "未填写对象描述"}</p>
    <div className="object-detail-facts"><div><span><Tag size={13} />类别</span><strong>{item.category}</strong></div><div><span><CalendarClock size={13} />最近出现</span><strong>{dateLabel(item.lastSeen)}</strong></div><div><span><Activity size={13} />关联事件</span><strong>{relatedEvents.length} 条</strong></div><div><span><ShieldCheck size={13} />关联插件</span><strong>{item.relatedPluginNames.length ? item.relatedPluginNames.join("、") : "尚未关联"}</strong></div></div>
    <h3>注册信息</h3>
    <div className="object-registration-card"><div><span>Object Contract ID</span><code>{object.object_id}</code></div><div><span>注册时间</span><strong>{dateLabel(object.created_at)}</strong></div></div>
    <h3>图片引用</h3>
    <div className="object-reference-list">{object.reference_uris.length ? object.reference_uris.map((uri) => <a href={uri} target="_blank" rel="noreferrer" key={uri}><Image size={15} /><span>{uri}</span><Link2 size={13} /></a>) : <div className="object-reference-empty"><Image size={16} /><span>暂无引用图。当前页面只展示后端已保存的引用地址。</span></div>}</div>
    <h3>最近事件</h3>
    <div className="object-event-list">{relatedEvents.length ? relatedEvents.slice(0, 6).map((event) => <div className="object-event-row" key={event.event_id}><div className={`event-type ${event.severity}`}><Activity size={14} /></div><div><strong>{event.title}</strong><span>{event.plugin_id} · {dateLabel(event.started_at)}</span></div><em className={`review-badge ${event.review_status}`}>{reviewLabel(event.review_status)}</em></div>) : <div className="object-reference-empty"><Activity size={16} /><span>还没有与该对象关联的 AI 事件。</span></div>}</div>
  </aside>;
}

function BoxPlaceholder() {
  return <div className="object-detail-placeholder"><Image size={23} /></div>;
}
