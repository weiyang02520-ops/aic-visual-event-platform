import { useMemo, useState, type FormEvent } from "react";
import { Boxes, Camera, Clock3, GitFork, History, Link2, MapPin, Plus, Search, UserRound, Users, X } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { href, navigate } from "../../app/router";
import { Empty, Modal, Panel, Pill, Segmented, reviewTone } from "../../design/ui";
import { CATEGORY_LABELS, clockTime, percent, relativeTime, reviewLabel, type ObjectCategory } from "../../engine/labels";
import { ActionTimeline } from "./ActionTimeline";
import { buildMemory, type MemoryItem } from "../../engine/memory";
import { ObjectGlyph } from "../../render/ObjectGlyph";
import { pluginLabel } from "../shared";
import "./memory.css";

const CATEGORY_ORDER: ObjectCategory[] = ["medicine", "tool", "daily"];

function Thumb({ item, size }: { item: MemoryItem; size: number }) {
  const [broken, setBroken] = useState(false);
  const uri = item.object.reference_uris[0];
  if (uri && !broken) return <img className="mem-img" src={uri} alt={item.object.name} onError={() => setBroken(true)} />;
  return <ObjectGlyph kind={item.glyph} size={size} />;
}

function RegisterModal({ onClose }: { onClose: () => void }) {
  const { createObject, createPerson } = useRuntime();
  const [kind, setKind] = useState<"object" | "person">("object");
  const [name, setName] = useState("");
  const [detail, setDetail] = useState("");
  const [reference, setReference] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const clean = name.trim();
    if (!clean) { setError(kind === "object" ? "请填写物品名称" : "请填写人员名称"); return; }
    const references = reference.trim() ? [reference.trim()] : [];
    setBusy(true);
    const ok = kind === "object" ? await createObject(clean, detail.trim(), references) : await createPerson(clean, detail.trim(), references);
    setBusy(false);
    if (ok) onClose();
  }

  return (
    <Modal title="登记新物品或家人" subtitle="填写名称，可附一张参考图链接。" onClose={onClose}>
      <form className="reg-form" onSubmit={submit}>
        <Segmented label="登记类型" value={kind} onChange={(value) => { setKind(value); setError(null); }} options={[{ value: "object", label: "物品" }, { value: "person", label: "人员" }]} />
        <label className="field"><span>{kind === "object" ? "物品名称" : "人员名称"}</span><input autoFocus value={name} onChange={(event) => setName(event.target.value)} placeholder={kind === "object" ? "例如：降压药盒" : "例如：爷爷"} /></label>
        <label className="field"><span>{kind === "object" ? "类别与常放位置" : "角色"}</span><input value={detail} onChange={(event) => setDetail(event.target.value)} placeholder={kind === "object" ? "例如：medicine · 客厅茶几" : "例如：resident / family / staff"} /></label>
        <label className="field"><span><Link2 size={13} /> 参考图链接（可选）</span><input value={reference} onChange={(event) => setReference(event.target.value)} placeholder="https://…/reference.jpg" inputMode="url" /></label>
        {error && <p className="reg-error" role="alert">{error}</p>}
        <div className="reg-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>取消</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? "保存中…" : "保存"}</button>
        </div>
      </form>
    </Modal>
  );
}

function MemoryDetail({ item }: { item: MemoryItem }) {
  const { plugins } = useRuntime();
  return (
    <Panel className="mem-detail" title={item.object.name} icon={<Boxes size={18} />} aside={<button className="icon-btn" style={{ width: 32, height: 32 }} onClick={() => navigate("memory")} aria-label="关闭详情"><X size={16} /></button>}>
      <div className="mem-detail-hero glyph-tile"><Thumb item={item} size={120} /></div>
      <div className="mem-detail-tags">
        <Pill tone="accent">{CATEGORY_LABELS[item.category]}</Pill>
        <Pill tone={item.object.status === "active" ? "ok" : "neutral"}>{item.object.status}</Pill>
        {item.pluginIds.map((id) => <Pill key={id}>{pluginLabel(plugins, id)}</Pill>)}
      </div>
      <p className="muted mem-desc">{item.object.description || "未填写描述"}</p>
      <dl className="kv">
        <div><dt><MapPin size={13} /> 最近已知位置</dt><dd>{item.lastLocation ?? (item.status === "ambiguous" ? "无法确定" : "未知")}</dd></div>
        <div><dt><Clock3 size={13} /> 最近出现</dt><dd>{item.lastSeen ? `${relativeTime(item.lastSeen)} · ${clockTime(item.lastSeen)}` : "—"}</dd></div>
        <div><dt><Camera size={13} /> 来源摄像头</dt><dd>{item.lastSource ?? "—"}</dd></div>
        <div><dt><History size={13} /> 出现次数</dt><dd className="num">{item.appearances.length}</dd></div>
        <div><dt>编号</dt><dd>{item.object.object_id}</dd></div>
      </dl>
      <p className="faint mem-note">“最近已知”是历史记录，不代表物品此刻一定在该位置。</p>
      {item.sameLabel.length > 0 && (
        <div className="mem-candidates">
          <strong><GitFork size={14} /> 同名候选 {item.sameLabel.length + 1} 个</strong>
          <span>登记库里还有 {item.sameLabel.map((id) => <a key={id} href={href("memory", id)}>{id}</a>)} 也叫“{item.object.name}”。只凭名字的记录会同时列给它们，不会合并成一个。</span>
        </div>
      )}
      <h3 className="mem-h3">出现记录</h3>
      {item.appearances.length ? (
        <ol className="mem-timeline">
          {item.appearances.map((appearance) => (
            <li key={appearance.event_id} className={appearance.ambiguous ? "ambiguous" : ""}>
              <a href={href("events", appearance.event_id)}>
                <strong>{appearance.title}</strong>
                <span>{appearance.location ?? "—"} · {relativeTime(appearance.at)}{appearance.source_id ? ` · ${appearance.source_id}` : ""}{appearance.confidence != null ? ` · ${percent(appearance.confidence)}` : ""}</span>
                <span className="mem-app-tags">
                  <Pill tone={reviewTone(appearance.review_status)}>{reviewLabel(appearance.review_status)}</Pill>
                  {appearance.ambiguous ? <Pill tone="warn">同名候选 · 不确定是这一个</Pill> : <Pill>{appearance.matchedBy === "id" ? "按编号匹配" : "按名称匹配"}</Pill>}
                </span>
              </a>
            </li>
          ))}
        </ol>
      ) : <Empty title="还没有见过它">位置保持“未知”，不会猜测</Empty>}
    </Panel>
  );
}

export function MemoryPage({ selectedId }: { selectedId: string | null }) {
  const { objects, events, persons } = useRuntime();
  const [filter, setFilter] = useState<ObjectCategory | "all">("all");
  const [query, setQuery] = useState("");
  const [registering, setRegistering] = useState(false);
  const [tab, setTab] = useState<"things" | "actions">("things");
  const items = useMemo(() => buildMemory(objects, events), [objects, events]);
  const shown = items.filter((item) => (filter === "all" || item.category === filter) && (!query.trim() || `${item.object.name} ${item.object.description}`.toLowerCase().includes(query.trim().toLowerCase())));
  const selected = items.find((item) => item.object.object_id === selectedId) ?? null;
  const counts = Object.fromEntries(CATEGORY_ORDER.map((category) => [category, items.filter((item) => item.category === category).length])) as Record<ObjectCategory, number>;

  return (
    <div className="page memory-page">
      <header className="page-head">
        <div>
          <h1>物品记忆</h1>
          <p>机器人认识的物品和家人：是什么、最近在哪儿见过、和哪些事件有关。</p>
        </div>
        <div className="page-actions">
          <Segmented label="记忆视图" value={tab} onChange={setTab} options={[{ value: "things", label: "物品与人" }, { value: "actions", label: "最近动作" }]} />
          {tab === "things" && <label className="search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索记忆" /></label>}
          <button className="btn btn-primary" onClick={() => setRegistering(true)}><Plus size={16} />登记</button>
        </div>
      </header>

      {tab === "actions" ? <ActionTimeline /> : <>
      <div className="mem-stats">
        {CATEGORY_ORDER.map((category) => (
          <button key={category} className={`mem-stat ${filter === category ? "active" : ""}`} onClick={() => setFilter(filter === category ? "all" : category)} aria-pressed={filter === category}>
            <strong className="num">{counts[category]}</strong><span>{CATEGORY_LABELS[category]}</span>
          </button>
        ))}
        <div className="mem-stat static"><strong className="num">{persons.length}</strong><span>认识的人</span></div>
      </div>

      <div className={`mem-layout ${selected ? "with-detail" : ""}`}>
        <div>
          {CATEGORY_ORDER.filter((category) => filter === "all" || filter === category).map((category) => {
            const group = shown.filter((item) => item.category === category);
            if (!group.length) return null;
            return (
              <section key={category} className="mem-group">
                <h2 className="eyebrow">{CATEGORY_LABELS[category]} · {group.length}</h2>
                <div className="mem-grid">
                  {group.map((item) => (
                    <a key={item.object.object_id} className={`mem-card ${selected?.object.object_id === item.object.object_id ? "selected" : ""}`} href={href("memory", item.object.object_id)}>
                      <div className="mem-thumb glyph-tile"><Thumb item={item} size={72} /></div>
                      <strong>{item.object.name}</strong>
                      <span className="mem-loc"><MapPin size={12} />{item.lastLocation ?? (item.status === "ambiguous" ? "位置无法确定" : "位置未知")}</span>
                      {item.sameLabel.length > 0 && <Pill tone="warn" className="mem-badge">同名候选</Pill>}
                      <div className="mem-card-foot"><span>{item.lastSeen ? relativeTime(item.lastSeen) : "未出现"}</span><b className="num">{item.appearances.length} 次</b></div>
                    </a>
                  ))}
                </div>
              </section>
            );
          })}
          {!shown.length && <Panel><Empty icon={<Boxes size={26} />} title={items.length ? "没有匹配的记忆" : "记忆库是空的"}>点击右上角「登记」让 AI 记住新的物品</Empty></Panel>}

          <section className="mem-group">
            <h2 className="eyebrow">认识的人 · {persons.length}</h2>
            {persons.length ? (
              <div className="mem-people">
                {persons.map((person) => (
                  <div key={person.person_id} className="mem-person">
                    <span className="mem-avatar"><UserRound size={20} /></span>
                    <div><strong>{person.display_name}</strong><span>{person.role || "unknown"} · 隐私保护</span></div>
                  </div>
                ))}
              </div>
            ) : <Panel><Empty icon={<Users size={24} />} title="还没有登记人员" /></Panel>}
          </section>
        </div>
        {selected && <MemoryDetail item={selected} />}
      </div>
      </>}

      {registering && <RegisterModal onClose={() => setRegistering(false)} />}
    </div>
  );
}
