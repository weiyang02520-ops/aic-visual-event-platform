import { Check, X } from "lucide-react";
import type { ReviewStatus, UnifiedEventContract } from "../../contracts";
import { EventTimeline } from "./EventTimeline";

function reviewLabel(status: ReviewStatus) {
  return status === "pending" ? "待复核" : status === "confirmed" ? "已确认" : "已驳回";
}

export function EventDetail({ event, onClose, onReview }: { event: UnifiedEventContract; onClose: () => void; onReview: (event: UnifiedEventContract, status: ReviewStatus) => Promise<void> }) {
  async function review(status: ReviewStatus) {
    await onReview(event, status);
    onClose();
  }
  return <div className="event-drawer-backdrop" onClick={onClose}><aside className="event-drawer" onClick={(click) => click.stopPropagation()}><div className="drawer-heading"><div><span className="panel-kicker">EVENT DETAIL / {event.plugin_id}</span><h2>{event.title}</h2><span className={`event-detail-status ${event.review_status}`}>{reviewLabel(event.review_status)}</span></div><button className="icon-button" onClick={onClose}><X size={16} /></button></div><p className="drawer-description">{event.description}</p><div className="drawer-facts"><div><span>来源</span><strong>{event.source_id}</strong></div><div><span>置信度</span><strong>{Math.round(event.confidence * 100)}%</strong></div><div><span>时间窗</span><strong>{event.started_at} → {event.ended_at}</strong></div><div><span>位置</span><strong>{event.location ?? "未标注"}</strong></div><div><span>人物</span><strong>{String(event.subject?.label ?? event.subject?.id ?? "未关联")}</strong></div><div><span>对象</span><strong>{String(event.object?.label ?? event.object?.id ?? "未关联")}</strong></div></div><h3>AI 推理链</h3><EventTimeline facts={event.facts} /><h3>证据链</h3><div className="evidence-list">{event.evidence.length ? event.evidence.map((evidence, index) => <div key={`${evidence.source_id}-${index}`}><b>{evidence.status}</b><span>{evidence.source_id}</span><small>{evidence.started_at} → {evidence.ended_at}</small>{evidence.uri && evidence.status === "available" ? <a className="evidence-open" href={evidence.uri} target="_blank" rel="noreferrer">打开证据回放</a> : <small className="evidence-unavailable">回放地址未验证</small>}</div>) : <span className="drawer-muted">没有可解析证据；不能伪造回放地址</span>}</div>{event.review_status === "pending" && <div className="drawer-actions"><button className="primary-button" onClick={() => review("confirmed")}><Check size={15} /> 确认事件</button><button className="ghost-button drawer-reject" onClick={() => review("rejected")}><X size={15} /> 驳回</button></div>}</aside></div>;
}
