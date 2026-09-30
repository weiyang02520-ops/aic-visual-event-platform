import { ArrowRight, Bell, Box, Cpu, FileSearch, History, Play, Puzzle, ShieldCheck, UserRound } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { href } from "../../app/router";
import { ConfidenceRing, Dot, Empty, Panel, Pill, reviewTone } from "../../design/ui";
import { useLiveScene } from "../../hooks/useLiveScene";
import { factLabel, percent, relativeTime, reviewLabel } from "../../engine/labels";
import { ObjectGlyph } from "../../render/ObjectGlyph";
import { PersonPortrait } from "../../render/PersonPortrait";
import { SceneStage } from "../../render/SceneStage";
import type { ScenePhase } from "../../engine/scene/types";
import { usePluginHost } from "../../plugins";
import { isRunning, isToday, pluginLabel, systemRows, useExplanations } from "../shared";
import "./dashboard.css";

const PHASE_COPY: Record<ScenePhase, string> = {
  idle: "房间里暂时没有人", person: "发现人物", recognize: "提取骨骼，换成卡通形象", object: "看到了茶几上的物品", action: "正在关注拿药动作", event: "整理成一条记录", alert: "已提醒家属",
};

export function DashboardPage() {
  const runtime = useRuntime();
  const { mode, events, plugins, connection } = runtime;
  const host = usePluginHost();
  const scene = useLiveScene({ start: 12 });
  const frame = host.filterFrame(scene.frame);
  const explanations = useExplanations(events);
  const latest = events[0];
  const latestExplain = latest ? explanations.get(latest.event_id) : undefined;
  const person = frame?.person ?? null;
  const visibleObjects = frame?.objects.filter((object) => object.state !== "hidden") ?? [];
  const running = plugins.filter(isRunning).length;
  const pending = events.filter((event) => event.review_status === "pending").length;
  const rows = systemRows(runtime);

  return (
    <div className="page dashboard">
      <header className="page-head dash-greeting">
        <div>
          <h1>{person ? `${person.label} 在${scene.room}` : `${scene.room}里暂时没有人`}</h1>
          <p>{frame ? PHASE_COPY[frame.phase] : scene.reason || "等待视觉画面接入"} · 今日 {events.filter((event) => isToday(event.started_at)).length} 条记录，{pending} 条待你确认</p>
        </div>
        <div className="page-actions">
          <a className="btn btn-ghost" href={href("demo")}><Play size={15} fill="currentColor" />比赛演示</a>
          <a className="btn btn-primary" href={href("monitor")}>打开隐私监护<ArrowRight size={16} /></a>
        </div>
      </header>

      <div className="dash-hero">
        <section className="panel dash-live">
          <div className="stage-frame dash-stage">
            <SceneStage frame={frame} view="cartoon" backdropImage={scene.backdropImage} showTags={false} />
            <div className="dash-stage-top"><span className="hud-chip"><Dot tone={frame ? "ok" : "warn"} live={Boolean(frame)} />{scene.room} · Camera 01</span><span className="hud-chip"><ShieldCheck size={14} />只显示卡通形象</span></div>
            {!frame && <div className="dash-stage-empty">{scene.reason || "画面未接入"}</div>}
          </div>
          <div className="dash-stats">
            <div><strong className="num">{person ? 1 : 0}</strong><span>在场人数</span></div>
            <div><strong className="num">{visibleObjects.length}</strong><span>看到的物品</span></div>
            <div><strong className="num">{events.filter((event) => isToday(event.started_at)).length}</strong><span>今日记录</span></div>
            <div><strong className="num">{running}/{plugins.length}</strong><span>运行插件</span></div>
          </div>
        </section>

        <div className="dash-side">
          <Panel className="dash-person" title="当前人物" icon={<UserRound size={18} />} aside={person ? <Pill tone={person.identified ? "ok" : "accent"}>{person.identified ? "已识别" : "识别中"}</Pill> : <Pill>无人</Pill>}>
            <div className="person-row">
              <div className="person-portrait"><PersonPortrait keypoints={person?.keypoints ?? null} size={96} cartoonOpacity={frame?.cartoonReveal ?? 1} render={person?.render} /></div>
              <dl className="kv">
                <div><dt>正在</dt><dd>{person?.action ?? "—"}</dd></div>
                <div><dt>姿态</dt><dd>{person?.pose ?? "—"}</dd></div>
                <div><dt>位置</dt><dd>{person?.zone ?? "—"}</dd></div>
              </dl>
            </div>
          </Panel>

          <Panel className="dash-event" title="最新提醒" icon={<Bell size={18} />} aside={latest && <Pill tone={reviewTone(latest.review_status)}>{reviewLabel(latest.review_status)}</Pill>}>
            {latest && latestExplain ? (
              <>
                <div className="event-hero">
                  <ConfidenceRing value={latest.confidence} size={76} stroke={6} tone={latestExplain.sequenceComplete ? "accent" : "warn"} />
                  <div>
                    <h3>{latestExplain.verdict.headline}</h3>
                    <p className="muted">{latest.location ?? "未标注位置"} · {relativeTime(latest.started_at)}</p>
                  </div>
                </div>
                <ol className="stage-strip">
                  {latestExplain.stages.map((stage) => <li key={stage.key} className={stage.status}><i /><span>{stage.title}</span></li>)}
                </ol>
                <div className="event-foot">
                  <span className="faint">{latestExplain.verdict.disclaimer}</span>
                  <a href={href("events", latest.event_id)}>查看依据 →</a>
                </div>
              </>
            ) : <Empty icon={<Bell size={22} />} title="还没有提醒">{connection.status === "offline" ? connection.reason : undefined}</Empty>}
          </Panel>
        </div>
      </div>

      <section className="dash-plugins" aria-label="插件分析">
        {host.slots.map((slot) => {
          const Icon = slot.def.icon;
          const summary = slot.running ? slot.def.summarize(host.contextFor(slot, frame)) : null;
          return (
            <a key={slot.plugin.plugin_id} className={`dash-plugin ${slot.running ? "on" : "off"}`} href={slot.running ? href("monitor") : href("plugins")}>
              <span className="dash-plugin-icon"><Icon size={20} /></span>
              <div>
                <span className="dash-plugin-name">{slot.def.label}<Dot tone={slot.running ? "ok" : "neutral"} /></span>
                <strong>{summary?.headline ?? "插件已停用"}</strong>
                <small>{summary?.detail ?? "在插件中心开启"}</small>
              </div>
            </a>
          );
        })}
        <a className="dash-plugin add" href={href("plugins")}><span className="dash-plugin-icon"><Puzzle size={20} /></span><div><span className="dash-plugin-name">更多能力</span><strong>风险检测 · 生活提醒</strong><small>通过插件扩展</small></div></a>
      </section>

      <div className="grid-3 dash-lower">
        <Panel title="看到的物品" icon={<Box size={18} />} aside={<a className="panel-sub" href={href("memory")}>物品记忆 →</a>}>
          {visibleObjects.length ? (
            <ul className="obj-list">
              {visibleObjects.map((object) => (
                <li key={object.id}>
                  <span className="glyph-tile"><ObjectGlyph kind={object.glyph} size={34} /></span>
                  <div><strong>{object.label}</strong><span>{object.state === "held" ? "正被拿在手里" : "在茶几附近"}</span></div>
                  <b className="num">{percent(object.confidence)}</b>
                </li>
              ))}
            </ul>
          ) : <Empty title="暂时没有看到物品">{mode === "real" ? scene.reason || "等待画面" : undefined}</Empty>}
        </Panel>

        <Panel title="最近记录" icon={<History size={18} />} aside={<a className="panel-sub" href={href("events")}>全部 →</a>}>
          {events.length ? (
            <ul className="analysis-list">
              {events.slice(0, 4).map((event) => {
                const explanation = explanations.get(event.event_id)!;
                return (
                  <li key={event.event_id}>
                    <a href={href("events", event.event_id)}>
                      <div className="analysis-top"><strong>{explanation.verdict.headline}</strong><Pill tone={reviewTone(event.review_status)}>{reviewLabel(event.review_status)}</Pill></div>
                      <span className="analysis-meta">{explanation.stages.flatMap((stage) => stage.facts.map((fact) => factLabel(fact.fact_type))).slice(-2).join(" → ") || event.title} · {pluginLabel(plugins, event.plugin_id)} · {relativeTime(event.started_at)}</span>
                    </a>
                  </li>
                );
              })}
            </ul>
          ) : <Empty title="暂无记录" />}
        </Panel>

        <Panel title="设备状态" icon={<Cpu size={18} />} aside={<span className="panel-sub">{mode === "mock" ? "演示数据" : "实时"}</span>}>
          <ul className="sys-list">
            {rows.map((row) => <li key={row.id}><Dot tone={row.tone} /><div><strong>{row.label}</strong><span title={row.detail}>{row.detail}</span></div><b>{row.value}</b></li>)}
          </ul>
        </Panel>
      </div>

      <p className="dash-foot faint"><FileSearch size={14} /> 所有提醒都是辅助判断，不是医学诊断，需要家人或护理人员确认。</p>
    </div>
  );
}
