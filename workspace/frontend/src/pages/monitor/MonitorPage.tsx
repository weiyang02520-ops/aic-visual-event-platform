import { useState } from "react";
import { Activity, Pause, Play, Puzzle, RotateCcw, ScanEye, ShieldAlert, ShieldCheck, UserRound } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { href } from "../../app/router";
import { Dot, Empty, Panel, Pill, Segmented, Switch } from "../../design/ui";
import { useLiveScene, type DemoSource } from "../../hooks/useLiveScene";
import { CATEGORY_LABELS, factLabel, percent } from "../../engine/labels";
import { SceneStage, type ViewMode } from "../../render/SceneStage";
import { ObjectGlyph } from "../../render/ObjectGlyph";
import { PersonPortrait } from "../../render/PersonPortrait";
import { usePluginHost } from "../../plugins";
import { PrivacyExplainer } from "../privacy/PrivacyExplainer";
import { isRunning, pluginLabel } from "../shared";
import "./monitor.css";

const fmt = (t: number) => `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(Math.floor(t % 60)).padStart(2, "0")}`;
export function MonitorPage() {
  const { mode, runAnalysis, analyzing, canMutate, togglePlugin } = useRuntime();
  const host = usePluginHost();
  const [view, setView] = useState<ViewMode>("cartoon");
  const [demo, setDemo] = useState<DemoSource>("script");
  // Start just before the skeleton locks on so the page opens with a person in view.
  const scene = useLiveScene({ start: 4.2, demo });
  const { clock, source } = scene;
  // Objects are only marked when a running plugin watches their category.
  const frame = host.filterFrame(scene.frame);
  const person = frame?.person ?? null;
  const visibleObjects = frame?.objects.filter((object) => object.state !== "hidden") ?? [];
  const facts = [...(frame?.facts ?? [])].reverse();
  const closed = !source;

  return (
    <div className="page monitor">
      <header className="page-head">
        <div>
          <h1>隐私监护</h1>
          <p>只有人物被换成卡通形象或骨骼，房间和物品保持原样。看得到发生了什么，但看不到人的真实样子。</p>
        </div>
        <div className="page-actions">
          {mode === "mock" && scene.photoAvailable && <Segmented label="演示素材" value={demo} onChange={setDemo} options={[{ value: "script", label: "用药演示" }, { value: "photo", label: "实拍照片" }]} />}
          <Segmented label="显示模式" value={view} onChange={setView} options={[{ value: "cartoon", label: "卡漫" }, { value: "skeleton", label: "骨骼" }, { value: "fusion", label: "融合" }]} />
          <button className="btn btn-primary" onClick={() => void runAnalysis()} disabled={analyzing || !canMutate}><ScanEye size={16} />{analyzing ? "分析中…" : "开始一次分析"}</button>
        </div>
      </header>

      <div className="mon-grid">
        <div className="mon-stage-col">
          <div className="stage-frame mon-stage">
            <SceneStage frame={frame} view={view} backdropImage={scene.backdropImage} />
            <div className="stage-hud top-left">
              <span className="hud-chip"><Dot tone={closed ? "warn" : "ok"} live={!closed} />{scene.room} · Camera 01 <b>{mode === "mock" ? (scene.isPhoto ? "实拍照片 · 真实骨骼" : scene.backdropImage ? "演示 · 实拍环境" : "演示 · 未放环境照片") : closed ? "未接入" : "实时预览"}</b></span>
            </div>
            <div className="stage-hud top-right">
              {person?.render === "unregistered"
                ? <span className="hud-chip hud-alert"><ShieldAlert size={15} />未登记人员 · 只显示骨骼</span>
                : <span className="hud-chip"><ShieldCheck size={15} />已登记人员以卡通形象显示</span>}
            </div>
            {frame?.latestFact && (
              <div className="stage-hud bottom-left" key={frame.latestFact.fact_type + frame.latestFact.t}>
                <span className="hud-chip fact-chip"><Activity size={15} />{factLabel(frame.latestFact.fact_type)}<b className="num">{percent(frame.latestFact.confidence)}</b></span>
              </div>
            )}
            {closed && (
              <div className="stage-closed">
                <ShieldCheck size={34} />
                <strong>隐私渲染流未接入</strong>
                <span>{scene.reason || "等待骨骼 / 卡漫输出"}</span>
                <small>隐私监护页不会回退到原始视频。</small>
              </div>
            )}
          </div>

          <div className="player">
            <button className="icon-btn" onClick={clock.toggle} disabled={closed} aria-label={clock.playing ? "暂停" : "播放"}>{clock.playing ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}</button>
            <button className="icon-btn" onClick={clock.restart} disabled={closed} aria-label="从头播放"><RotateCcw size={17} /></button>
            <span className="player-time num">{fmt(clock.t)} / {fmt(source?.duration ?? 0)}</span>
            <div className="scrubber">
              <input type="range" min={0} max={source?.duration ?? 1} step={0.05} value={clock.t} onChange={(event) => clock.seek(Number(event.target.value))} disabled={closed} aria-label="时间轴" style={{ ["--p" as string]: `${source ? (clock.t / source.duration) * 100 : 0}%` }} />
              <div className="scrub-markers" aria-hidden="true">
                {source?.markers.map((marker) => <span key={`${marker.fact_type}-${marker.t}`} style={{ left: `${(marker.t / source.duration) * 100}%` }} className={marker.t <= clock.t ? "on" : ""} title={factLabel(marker.fact_type)} />)}
              </div>
            </div>
          </div>
        </div>

        <aside className="mon-side">
          <PrivacyExplainer mode="rgb-local" poseAvailable={mode === "mock" || Boolean(frame?.person)} objectAvailable={mode === "mock" || visibleObjects.length > 0} />

          <Panel className="mon-card" title="场景插件" icon={<Puzzle size={18} />} aside={<a className="panel-sub" href={href("plugins")}>插件中心 →</a>}>
            <ul className="plugin-toggles">
              {host.slots.map((slot) => {
                const Icon = slot.def.icon;
                return (
                  <li key={slot.plugin.plugin_id} className={slot.running ? "on" : ""}>
                    <span className="plugin-toggle-icon"><Icon size={18} /></span>
                    <div><strong>{slot.def.label}</strong><span>{slot.def.watches.length ? `识别${slot.def.watches.map((category) => CATEGORY_LABELS[category]).join("、")}` : slot.def.scene}</span></div>
                    <Switch checked={slot.plugin.enabled} onChange={() => void togglePlugin(slot.plugin)} label={`${slot.plugin.enabled ? "停用" : "启用"}${slot.def.label}`} disabled={!canMutate || slot.plugin.state === "error"} />
                  </li>
                );
              })}
              {!host.slots.length && <li className="faint">没有已安装的插件</li>}
            </ul>
          </Panel>

          <Panel className="mon-card" title="人物状态" icon={<UserRound size={18} />} aside={<Pill tone={!person ? "neutral" : person.render === "unregistered" ? "risk" : person.render === "avatar" ? "ok" : "accent"}>{!person ? "无人" : person.render === "unregistered" ? "未登记" : person.render === "avatar" ? "已登记" : "识别中"}</Pill>}>
            <div className="mon-person">
              <div className="mon-portrait"><PersonPortrait keypoints={person?.keypoints ?? null} size={92} mode={view === "skeleton" ? "skeleton" : "cartoon"} cartoonOpacity={frame?.cartoonReveal ?? 1} render={person?.render} /></div>
              <dl className="kv">
                <div><dt>身份</dt><dd>{person?.label ?? "—"}</dd></div>
                <div><dt>显示方式</dt><dd>{!person ? "—" : person.render === "unregistered" ? "骨骼 + 提醒" : person.render === "avatar" ? "卡通形象" : "确认身份中"}</dd></div>
                <div><dt>动作</dt><dd>{person?.action ? factLabel(person.action) : "—"}</dd></div>
                <div><dt>姿态 · 区域</dt><dd>{person ? `${person.pose} · ${person.zone}` : "—"}</dd></div>
              </dl>
            </div>
          </Panel>

          <Panel className="mon-card" title="刚刚发生" icon={<Activity size={18} />} aside={<span className="panel-sub num">{facts.length} 条</span>}>
            {facts.length ? (
              <ul className="fact-feed">
                {facts.slice(0, 5).map((fact, index) => (
                  <li key={`${fact.fact_type}-${fact.t}`} className={index === 0 ? "latest" : ""}>
                    <span className="num">{fmt(fact.t)}</span><strong>{factLabel(fact.fact_type)}</strong><b className="num">{percent(fact.confidence)}</b>
                  </li>
                ))}
              </ul>
            ) : <Empty title="还没有动作" />}
          </Panel>

          <Panel className="mon-card" title="识别对象" icon={<ScanEye size={18} />} aside={<span className="panel-sub num">{visibleObjects.length}</span>}>
            {visibleObjects.length ? (
              <div className="mon-chips">
                {visibleObjects.map((object) => <span key={object.id} className={`obj-chip ${object.state}`}><ObjectGlyph kind={object.glyph} size={22} />{object.label}<b className="num">{object.state === "held" ? "手持" : percent(object.confidence)}</b></span>)}
              </div>
            ) : <Empty title="暂无识别对象" />}
          </Panel>

          {/* Each running plugin renders its own card; the page does not know what any plugin is. */}
          {host.running.map((slot) => {
            const { Panel: PluginPanel, icon: Icon, label } = slot.def;
            return (
              <Panel key={slot.plugin.plugin_id} className="mon-card plugin-slot" title={label} icon={<Icon size={18} />} aside={<Pill tone="ok">插件</Pill>}>
                <PluginPanel {...host.contextFor(slot, frame)} />
              </Panel>
            );
          })}
          {host.running.length === 0 && <Panel className="mon-card"><Empty icon={<Puzzle size={22} />} title="没有运行中的插件">画面只保留人物骨骼，打开上方的插件后才会识别物品和生成提醒。</Empty></Panel>}
        </aside>
      </div>
    </div>
  );
}
