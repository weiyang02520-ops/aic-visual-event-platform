import { Box, ChevronRight, Clock3, Search } from "lucide-react";
import type { ObjectMemoryItem } from "./types";

function relativeTime(value: string | null) {
  if (!value) return "暂无事件";
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.round(diff / 60000);
  return minutes < 1 ? "刚刚" : minutes < 60 ? `${minutes} 分钟前` : `${Math.round(minutes / 60)} 小时前`;
}

export function ObjectList({ items, selectedId, query, onQuery, onSelect }: {
  items: ObjectMemoryItem[];
  selectedId: string | null;
  query: string;
  onQuery: (value: string) => void;
  onSelect: (objectId: string) => void;
}) {
  return <section className="panel object-memory-list">
    <div className="panel-heading object-memory-heading">
      <div>
        <span className="panel-kicker">OBJECT MEMORY / REGISTRY</span>
        <h2>关注对象</h2>
        <p className="object-memory-lead">统一查看注册信息、识别状态与事件关联。</p>
      </div>
      <span className="count-pill">{items.length}</span>
    </div>
    <label className="object-memory-search"><Search size={15} /><input value={query} onChange={(event) => onQuery(event.target.value)} placeholder="搜索名称、类别或插件" /></label>
    <div className="object-list-table" role="list">
      <div className="object-list-head" aria-hidden="true"><span>对象</span><span>类别</span><span>插件 / 事件</span><span>状态</span><span /></div>
      {items.length === 0 ? <div className="object-memory-empty"><Box size={20} /><span>没有匹配的关注对象</span></div> : items.map((item) => <button className={`object-list-row ${item.object.object_id === selectedId ? "selected" : ""}`} key={item.object.object_id} onClick={() => onSelect(item.object.object_id)} role="listitem">
        <span className="object-list-name"><span className="object-list-icon"><Box size={15} /></span><span><strong>{item.object.name}</strong><small>{item.object.object_id}</small></span></span>
        <span className="object-category">{item.category}</span>
        <span className="object-relation"><strong>{item.relatedPluginNames.length ? item.relatedPluginNames.join("、") : "尚未关联"}</strong><small>{item.relatedEvents.length ? `${item.relatedEvents.length} 条事件` : "暂无事件"}</small></span>
        <span className={`object-status ${item.object.status === "active" ? "active" : "inactive"}`}><i />{item.object.status}</span>
        <span className="object-list-open"><ChevronRight size={16} /></span>
      </button>)}
    </div>
    <div className="object-memory-list-foot"><Clock3 size={14} /><span>最近出现时间</span><strong>{items.find((item) => item.object.object_id === selectedId)?.lastSeen ? relativeTime(items.find((item) => item.object.object_id === selectedId)?.lastSeen ?? null) : "选择对象查看"}</strong></div>
  </section>;
}
