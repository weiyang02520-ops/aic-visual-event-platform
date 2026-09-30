import { useMemo, useState } from "react";
import { AlertCircle, Box, Check, ChevronRight, CircleDashed, ClipboardCheck, FileSearch, Film, Gavel, Hand, MapPin, ScanEye, Search, UserRound, X } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { href } from "../../app/router";
import { ConfidenceRing, Empty, Panel, Pill, Segmented, reviewTone } from "../../design/ui";
import { clockTime, factLabel, percent, planCueLabel, relativeTime, reviewLabel } from "../../engine/labels";
import type { EventExplanation, StageKey } from "../../engine/explain";
import type { ReviewStatus, UnifiedEvent } from "../../types";
import { pluginLabel, useExplanations } from "../shared";
import "./events.css";

const STAGE_ICONS: Record<StageKey, typeof UserRound> = { person: UserRound, object: ScanEye, interaction: Box, action: Hand, verdict: Gavel };

function evidenceText(status: string): string {
  const map: Record<string, string> = {
    available: "可回放", fixture: "测试 fixture", provided_unverified: "已提供 · 未验证", unavailable: "不可用", unsupported: "不支持", designed: "已记录时间窗 · 待解析",
  };
  return map[status] ?? status;
}

function ReasoningFlow({ explanation, eventId, active, onSelect }: { explanation: EventExplanation; eventId: string; active: StageKey; onSelect: (key: StageKey) => void }) {
  return (
    <div className="flow" key={eventId} role="list">
      {explanation.stages.map((stage, index) => {
        const Icon = STAGE_ICONS[stage.key];
        return (
          <div className="flow-cell" key={stage.key} role="listitem" style={{ ["--i" as string]: index }}>
            <button className={`flow-node ${stage.status} ${stage.key === "verdict" ? "verdict" : ""} ${active === stage.key ? "active" : ""}`} onClick={() => onSelect(stage.key)} aria-pressed={active === stage.key}>
              <span className="flow-icon">{stage.status === "missing" ? <CircleDashed size={22} /> : <Icon size={22} />}</span>
              <strong>{stage.title}</strong>
              <span className="flow-conf num">{stage.status === "missing" ? "缺失" : percent(stage.confidence)}</span>
            </button>
            {index < explanation.stages.length - 1 && <span className={`flow-link ${explanation.stages[index + 1].status}`} aria-hidden="true"><i /></span>}
          </div>
        );
      })}
    </div>
  );
}

function EventDetail({ event, explanation }: { event: UnifiedEvent; explanation: EventExplanation }) {
  const { plugins, review, canMutate } = useRuntime();
  const [active, setActive] = useState<StageKey>("verdict");
  const [busy, setBusy] = useState(false);
  const stage = explanation.stages.find((item) => item.key === active) ?? explanation.stages[explanation.stages.length - 1];
  const cue = planCueLabel(event.metadata.plan_cue);
  const planEntry = typeof event.metadata.plan_entry === "string" ? event.metadata.plan_entry : null;
  const subject = event.subject ?? {};
  const object = event.object ?? {};

  async function act(status: ReviewStatus) {
    setBusy(true);
    await review(event, status);
    setBusy(false);
  }

  return (
    <div className="ev-detail" key={event.event_id}>
      <header className="ev-head">
        <div>
          <div className="ev-tags">
            <Pill tone={reviewTone(event.review_status)}>{reviewLabel(event.review_status)}</Pill>
            <Pill>{pluginLabel(plugins, event.plugin_id)}</Pill>
            {explanation.isMedication && <Pill tone={explanation.sequenceComplete ? "accent" : "warn"}>{explanation.sequenceComplete ? "序列完整" : "序列不完整"}</Pill>}
          </div>
          <h1>{event.title}</h1>
          <p className="muted"><MapPin size={14} /> {event.location ?? "未标注位置"} · {event.source_id} · {clockTime(event.started_at)} – {clockTime(event.ended_at)}</p>
        </div>
      </header>

      <Panel title="为什么会有这条提醒" icon={<FileSearch size={18} />} aside={<span className="panel-sub">点击每一步查看看到了什么</span>} className="ev-flow-panel">
        <ReasoningFlow explanation={explanation} eventId={event.event_id} active={active} onSelect={setActive} />
        <div className={`stage-detail ${stage.status}`}>
          <div className="stage-detail-head">
            <strong>{stage.title}</strong>
            <span>{stage.reason}</span>
          </div>
          {stage.facts.length > 0 && (
            <ul className="stage-facts">
              {stage.facts.map((fact, index) => (
                <li key={`${fact.fact_type}-${index}`}>
                  <code>{fact.fact_type}</code>
                  <span>{factLabel(fact.fact_type)}</span>
                  <span className="faint">{fact.location ?? "—"}</span>
                  <b className="num">{percent(fact.confidence)}</b>
                </li>
              ))}
            </ul>
          )}
          {stage.key === "verdict" && <p className="stage-note">由 {pluginLabel(plugins, event.plugin_id)} 插件把前序事实按时间与同一人物 / 物品关联后生成。{explanation.verdict.disclaimer}。</p>}
          {stage.status === "missing" && <p className="stage-note warn"><AlertCircle size={15} /> 该环节没有对应事实，判断因此降级为复核线索。</p>}
        </div>
      </Panel>

      <div className="ev-bottom">
        <Panel className="verdict-card" title="判断结果" icon={<Gavel size={18} />}>
          <div className="verdict-body">
            <ConfidenceRing value={event.confidence} size={120} stroke={9} tone={explanation.sequenceComplete ? "accent" : "warn"} />
            <div>
              <h2>{explanation.verdict.headline}</h2>
              <p className="muted">{event.description}</p>
              {cue && <p className="verdict-cue"><ClipboardCheck size={15} /> 用药计划：{cue}{planEntry ? ` · ${planEntry}` : ""}</p>}
            </div>
          </div>
          <p className="disclaimer">{explanation.verdict.disclaimer} · 需人工复核后才可作为记录</p>
          {event.review_status === "pending" ? (
            <div className="verdict-actions">
              <button className="btn btn-ok" disabled={busy || !canMutate} onClick={() => void act("confirmed")}><Check size={16} /> 确认</button>
              <button className="btn btn-danger" disabled={busy || !canMutate} onClick={() => void act("rejected")}><X size={16} /> 驳回</button>
            </div>
          ) : <p className="muted verdict-done">已由人工{reviewLabel(event.review_status)}</p>}
        </Panel>

        <div className="ev-side-stack">
          <Panel title="关联实体" icon={<UserRound size={18} />}>
            <dl className="kv">
              <div><dt>人物</dt><dd>{String(subject.label ?? subject.id ?? "未关联")}</dd></div>
              <div><dt>物品</dt><dd>{object.id ? <a href={href("memory", String(object.id))}>{String(object.label ?? object.id)}</a> : String(object.label ?? "未关联")}</dd></div>
              <div><dt>插件版本</dt><dd>{pluginLabel(plugins, event.plugin_id)} {event.plugin_version}</dd></div>
            </dl>
          </Panel>
          <Panel title="证据" icon={<Film size={18} />}>
            {event.evidence.length ? (
              <ul className="evidence">
                {event.evidence.map((evidence, index) => (
                  <li key={`${evidence.source_id}-${index}`}>
                    <div><Pill tone={evidence.status === "available" ? "ok" : "neutral"}>{evidenceText(evidence.status)}</Pill><span className="faint">{evidence.source_id}</span></div>
                    <span className="muted num">{clockTime(evidence.started_at)} – {clockTime(evidence.ended_at)}</span>
                    {evidence.status === "available" && evidence.uri ? <a className="btn btn-ghost btn-sm" href={evidence.uri} target="_blank" rel="noreferrer"><Film size={14} /> 打开回放</a> : <span className="faint">回放地址未验证，不提供播放</span>}
                  </li>
                ))}
              </ul>
            ) : <Empty title="没有证据时间窗">不能伪造回放地址</Empty>}
          </Panel>
        </div>
      </div>
    </div>
  );
}

export function EventsPage({ selectedId }: { selectedId: string | null }) {
  const { events, plugins, connection } = useRuntime();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ReviewStatus | "all">("all");
  const [pluginFilter, setPluginFilter] = useState<string>("all");
  const explanations = useExplanations(events);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return events.filter((event) => {
      if (status !== "all" && event.review_status !== status) return false;
      if (pluginFilter !== "all" && event.plugin_id !== pluginFilter) return false;
      if (!needle) return true;
      return [event.title, event.description, event.plugin_id, event.source_id, event.location ?? "", String(event.object?.label ?? ""), String(event.subject?.label ?? "")].join(" ").toLowerCase().includes(needle);
    });
  }, [events, query, status, pluginFilter]);
  const selected = events.find((event) => event.event_id === selectedId) ?? filtered[0] ?? null;
  const counts = { pending: events.filter((event) => event.review_status === "pending").length };

  return (
    <div className="page events-page">
      <header className="page-head">
        <div>
          <h1>事件分析</h1>
          <p>每条提醒都说明它是怎么得出的：看到了谁、看到了什么物品、做了什么动作。</p>
        </div>
        <div className="page-actions"><Pill tone="warn">{counts.pending} 条待复核</Pill></div>
      </header>

      <div className="ev-layout">
        <aside className="ev-list panel">
          <div className="ev-list-tools">
            <label className="search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索事件、位置、物品" /></label>
            <div className="plugin-chips" role="group" aria-label="按插件筛选">
              {[{ id: "all", label: "全部插件" }, ...plugins.map((plugin) => ({ id: plugin.plugin_id, label: pluginLabel(plugins, plugin.plugin_id) }))].map((chip) => (
                <button key={chip.id} aria-pressed={pluginFilter === chip.id} onClick={() => setPluginFilter(chip.id)}>{chip.label}</button>
              ))}
            </div>
            <Segmented label="复核状态" value={status} onChange={setStatus} options={[{ value: "all", label: "全部" }, { value: "pending", label: "待复核" }, { value: "confirmed", label: "已确认" }, { value: "rejected", label: "已驳回" }]} />
          </div>
          <div className="ev-items">
            {filtered.length ? filtered.map((event) => {
              const explanation = explanations.get(event.event_id)!;
              return (
                <a key={event.event_id} href={href("events", event.event_id)} className={`ev-item ${selected?.event_id === event.event_id ? "selected" : ""}`} aria-current={selected?.event_id === event.event_id ? "true" : undefined}>
                  <span className={`ev-sev ${event.severity}`} />
                  <div className="ev-item-main">
                    <strong>{event.title}</strong>
                    <span>{pluginLabel(plugins, event.plugin_id)} · {event.location ?? "—"}</span>
                    <div className="chain">{explanation.stages.map((stage) => <i key={stage.key} className={stage.status === "passed" ? "on" : "miss"} />)}</div>
                  </div>
                  <div className="ev-item-side">
                    <b className="num">{percent(event.confidence)}</b>
                    <span>{relativeTime(event.started_at)}</span>
                    <Pill tone={reviewTone(event.review_status)}>{reviewLabel(event.review_status)}</Pill>
                  </div>
                  <ChevronRight size={16} className="ev-chevron" />
                </a>
              );
            }) : <Empty title={events.length ? "没有匹配的事件" : "还没有事件"}>{connection.status === "offline" ? connection.reason : undefined}</Empty>}
          </div>
        </aside>
        <section className="ev-main">
          {selected ? <EventDetail key={selected.event_id} event={selected} explanation={explanations.get(selected.event_id)!} /> : <Panel><Empty icon={<FileSearch size={26} />} title="选择一条事件查看依据" /></Panel>}
        </section>
      </div>
    </div>
  );
}
