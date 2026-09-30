import { useMemo, useState } from "react";
import { Camera, History, SplitSquareVertical } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { href } from "../../app/router";
import { Empty, Panel, Pill } from "../../design/ui";
import { clockTime, factLabel, percent, relativeTime } from "../../engine/labels";
import { buildTimeline, filterTimeline, groupTimeline } from "../../engine/timeline";

/** Recent actions across all events: newest first, filterable, grouped by source and continuity segment. */
export function ActionTimeline() {
  const { events, connection } = useRuntime();
  const all = useMemo(() => buildTimeline(events), [events]);
  const [types, setTypes] = useState<Set<string>>(new Set());
  const [subject, setSubject] = useState<string>("");
  const [object, setObject] = useState<string>("");

  const typeOptions = useMemo(() => [...new Set(all.map((entry) => entry.fact_type))], [all]);
  const subjects = useMemo(() => [...new Set(all.map((entry) => entry.subject).filter((value): value is string => Boolean(value)))], [all]);
  const objects = useMemo(() => [...new Set(all.map((entry) => entry.object).filter((value): value is string => Boolean(value)))], [all]);
  const shown = filterTimeline(all, { factTypes: types, subject: subject || null, object: object || null });
  const groups = groupTimeline(shown);

  function toggleType(type: string) {
    setTypes((current) => {
      const next = new Set(current);
      if (next.has(type)) next.delete(type); else next.add(type);
      return next;
    });
  }

  return (
    <div className="tl-layout">
      <Panel className="tl-filters" title="筛选" icon={<History size={18} />}>
        <span className="eyebrow">动作类型</span>
        <div className="plugin-chips tl-chips">
          <button aria-pressed={types.size === 0} onClick={() => setTypes(new Set())}>全部</button>
          {typeOptions.map((type) => <button key={type} aria-pressed={types.has(type)} onClick={() => toggleType(type)}>{factLabel(type)}</button>)}
        </div>
        <label className="field"><span>人物</span>
          <select value={subject} onChange={(event) => setSubject(event.target.value)}><option value="">全部人物</option>{subjects.map((value) => <option key={value} value={value}>{value}</option>)}</select>
        </label>
        <label className="field"><span>物品</span>
          <select value={object} onChange={(event) => setObject(event.target.value)}><option value="">全部物品</option>{objects.map((value) => <option key={value} value={value}>{value}</option>)}</select>
        </label>
        <p className="faint tl-note">“识别到物品”只更新位置记忆，不算动作，所以不出现在这里。不同摄像头、或摄像头中断前后的动作分段显示，不会被当成一个连续过程。</p>
      </Panel>

      <div className="tl-groups">
        {groups.length ? groups.map((group) => (
          <Panel key={group.key} className="tl-group"
            title={<><Camera size={16} /> {group.source_id}</>}
            aside={<Pill tone={group.segment == null ? "neutral" : "accent"}><SplitSquareVertical size={12} />{group.segment == null ? "连续段未标注" : `连续段 ${group.segment}`}</Pill>}>
            <ol className="tl-list">
              {group.entries.map((entry) => (
                <li key={entry.id}>
                  <span className="tl-time num" title={entry.exactTime ? "事实自带时间" : "事实没有独立时间，按事件时间窗估算"}>{clockTime(entry.at)}{!entry.exactTime && <i>≈</i>}</span>
                  <span className="tl-dot" />
                  <div className="tl-body">
                    <strong>{factLabel(entry.fact_type)}</strong>
                    <span>{[entry.subject, entry.object, entry.location].filter(Boolean).join(" · ") || "—"}</span>
                    <a href={href("events", entry.event_id)}>{entry.event_title} · {relativeTime(entry.at)}</a>
                  </div>
                  <b className="num">{percent(entry.confidence)}</b>
                </li>
              ))}
            </ol>
          </Panel>
        )) : <Panel><Empty icon={<History size={24} />} title={all.length ? "没有符合条件的动作" : "还没有动作记录"}>{connection.status === "offline" ? connection.reason : undefined}</Empty></Panel>}
      </div>
    </div>
  );
}
