import { Activity, ArrowUpRight, Check, Search, SlidersHorizontal, X } from "lucide-react";
import type { ReviewStatus, UnifiedEventContract } from "../../contracts";

function relativeTime(value: string) {
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.round(diff / 60000);
  return minutes < 1 ? "刚刚" : minutes < 60 ? `${minutes} 分钟前` : `${Math.round(minutes / 60)} 小时前`;
}

function reviewLabel(status: ReviewStatus) {
  return status === "pending" ? "待复核" : status === "confirmed" ? "已确认" : "已驳回";
}

function evidenceLabel(event: UnifiedEventContract) {
  const status = event.evidence[0]?.status;
  return status === "fixture" ? "测试 fixture" : status === "provided_unverified" ? "已提供·未验证" : status === "available" ? "可回放" : "待解析";
}

export function EventList({ events, query, status, onQuery, onStatus, onSelect, onReview }: {
  events: UnifiedEventContract[];
  query: string;
  status: ReviewStatus | "all";
  onQuery: (value: string) => void;
  onStatus: (value: ReviewStatus | "all") => void;
  onSelect: (event: UnifiedEventContract) => void;
  onReview: (event: UnifiedEventContract, status: ReviewStatus) => Promise<void>;
}) {
  return <section className="panel full-panel event-center-panel"><div className="panel-heading"><div><span className="panel-kicker">EVENT CENTER / HISTORY</span><h2>事件中心</h2><p className="event-center-lead">从 AI 事实到人工复核，查看每个事件的来源、判断和证据。</p></div><div className="filter-row"><label className="search-box"><Search size={15} /><input value={query} onChange={(event) => onQuery(event.target.value)} placeholder="搜索事件、位置或对象" /></label><label className="filter-select"><SlidersHorizontal size={15} /><select value={status} onChange={(event) => onStatus(event.target.value as ReviewStatus | "all")}><option value="all">全部状态</option><option value="pending">待复核</option><option value="confirmed">已确认</option><option value="rejected">已驳回</option></select></label></div></div><div className="event-table"><div className="event-table-head"><span>事件</span><span>来源</span><span>置信度</span><span>状态</span><span>时间</span><span /></div>{events.length === 0 ? <div className="event-contract-empty">没有匹配事件</div> : events.map((event) => <div className="event-table-row" key={event.event_id}><div className="table-event"><div className={`event-type ${event.severity}`}><Activity size={15} /></div><div><strong>{event.title}</strong><small>{event.plugin_id} · {String(event.object?.label ?? "基础事实")}</small></div></div><span className="source-cell"><strong>{event.source_id}</strong><small className="evidence-inline">证据：{evidenceLabel(event)}</small></span><span className="confidence"><i style={{ width: `${event.confidence * 100}%` }} />{Math.round(event.confidence * 100)}%</span><span className={`review-badge ${event.review_status}`}>{reviewLabel(event.review_status)}</span><span className="table-time">{relativeTime(event.started_at)}</span><button className="table-open" onClick={() => onSelect(event)} title="查看事件详情"><ArrowUpRight size={15} /></button>{event.review_status === "pending" && <div className="table-row-actions"><button onClick={() => onReview(event, "confirmed")} title="确认"><Check size={14} /></button><button onClick={() => onReview(event, "rejected")} title="驳回"><X size={14} /></button></div>}</div>)}</div></section>;
}
