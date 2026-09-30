import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Bell, Check, ClipboardCheck, History, Maximize2, Pause, Play, RotateCcw, ShieldCheck, X } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { usePluginHost } from "../../plugins";
import { useSceneBackdrop } from "../../hooks/useSceneBackdrop";
import { href, navigate } from "../../app/router";
import { BrandMark } from "../../app/Shell";
import { useSceneClock } from "../../hooks/useSceneClock";
import { DEMO_ACTS, MOCK_DURATION, sampleMockScene } from "../../engine/scene/mockScript";
import { SceneStage } from "../../render/SceneStage";
import { percent } from "../../engine/labels";
import type { UnifiedEvent } from "../../types";
import "./demo.css";

const LOG: Array<{ t: number; text: string; code?: string; tone?: "accent" | "ok" | "warn" }> = [
  { t: 0.4, text: "客厅摄像头已连接" },
  { t: 1.6, text: "画面里有人在走动" },
  { t: 4.6, text: "有人进入客厅", code: "person_entered_zone 0.94", tone: "accent" },
  { t: 6.2, text: "找到 17 个身体关键点", code: "coco17" },
  { t: 6.8, text: "认出是爷爷", tone: "ok" },
  { t: 7.6, text: "换成卡通形象显示，不保留真实画面" },
  { t: 8.9, text: "识别到降压药盒", code: "object_detected 0.95", tone: "accent" },
  { t: 9.7, text: "识别到水杯", code: "object_detected 0.90" },
  { t: 10.4, text: "识别到老花镜", code: "object_detected 0.82" },
  { t: 12.8, text: "手靠近药盒", code: "hand_near_object 0.89", tone: "accent" },
  { t: 14.1, text: "拿起药盒", code: "object_picked 0.91", tone: "accent" },
  { t: 16.2, text: "手靠近面部", code: "hand_to_face 0.74", tone: "accent" },
  { t: 18.6, text: "放回药盒", code: "object_put_down 0.86" },
  { t: 19.2, text: "五个步骤全部对上", tone: "ok" },
  { t: 20.0, text: "记录：疑似完成服药", code: "confidence 0.78", tone: "warn" },
  { t: 22.8, text: "已通知家属确认", tone: "ok" },
];

/** `#/demo/12` starts the rehearsal at 12 s, handy for jumping to a specific act on stage. */
export function DemoPage({ startAt }: { startAt?: string | null }) {
  const { mode, runAnalysis } = useRuntime();
  const host = usePluginHost();
  // The story ends in a medication alert, which only exists while that plugin runs.
  const medication = host.running.some((slot) => slot.plugin.plugin_id === "elderly_care");
  const [finished, setFinished] = useState(false);
  const start = Math.min(MOCK_DURATION - 0.5, Math.max(0, Number(startAt) || 0));
  const clock = useSceneClock(MOCK_DURATION, { loop: false, autoplay: true, start, onEnd: () => setFinished(true) });
  const backdrop = useSceneBackdrop();
  const rawFrame = useMemo(() => sampleMockScene(clock.t, backdrop.layout), [clock.t, backdrop.layout]);
  const filtered = host.filterFrame(rawFrame)!;
  const frame = medication ? filtered : { ...filtered, eventReady: false, alertReady: false };
  const act = DEMO_ACTS.find((item) => clock.t >= item.start && clock.t < item.end) ?? DEMO_ACTS[DEMO_ACTS.length - 1];
  const actIndex = DEMO_ACTS.indexOf(act);
  const [created, setCreated] = useState<UnifiedEvent | null>(null);
  const triggered = useRef(false);
  const logRef = useRef<HTMLOListElement>(null);
  const log = LOG.filter((entry) => entry.t <= clock.t && (medication || entry.t < 19));

  // Mock mode writes a real (fixture) event through the same Repository path, so it shows up in the Event Center.
  useEffect(() => {
    if (clock.t < 19) { triggered.current = false; return; }
    if (frame.eventReady && medication && !triggered.current && mode === "mock") {
      triggered.current = true;
      void runAnalysis("mock://elderly-medication").then(setCreated);
    }
  }, [clock.t, frame.eventReady, medication, mode, runAnalysis]);

  useEffect(() => { logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" }); }, [log.length]);

  const restart = useCallback(() => { setFinished(false); setCreated(null); clock.restart(); }, [clock]);
  const jump = useCallback((delta: number) => {
    const target = DEMO_ACTS[Math.min(DEMO_ACTS.length - 1, Math.max(0, actIndex + delta))];
    setFinished(false);
    clock.seek(target.start + 0.01);
  }, [actIndex, clock]);
  const fullscreen = useCallback(() => {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen?.();
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return;
      if (event.code === "Space") { event.preventDefault(); if (finished) restart(); else clock.toggle(); }
      else if (event.key === "ArrowRight") jump(1);
      else if (event.key === "ArrowLeft") jump(-1);
      else if (event.key.toLowerCase() === "r") restart();
      else if (event.key.toLowerCase() === "f") fullscreen();
      else if (event.key === "Escape" && !document.fullscreenElement) navigate("dashboard");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [clock, finished, fullscreen, jump, restart]);

  const view = frame.phase === "action" || (frame.phase === "recognize" && frame.cartoonReveal >= 1) ? "fusion" : "cartoon";

  return (
    <div className="demo">
      <div className="demo-stage">
        {/* Once the event card is up, object labels would sit behind it; the card carries the story from here. */}
        {/* A person-photo scene has its own geometry; the scripted story then runs on the neutral grid. */}
        <SceneStage frame={frame} view={view} backdropImage={backdrop.photo ? null : backdrop.image} showTags={!(frame.phase === "event" || frame.phase === "alert" || finished)} />
      </div>

      <header className="demo-top">
        <div className="demo-brand"><BrandMark size={32} /><div><strong>Sentinel</strong><span>AI 视觉机器人 · 智能监护</span></div></div>
        <ol className="demo-acts">
          {DEMO_ACTS.map((item, index) => {
            const progress = Math.min(1, Math.max(0, (clock.t - item.start) / (item.end - item.start)));
            return (
              <li key={item.key} className={index === actIndex ? "current" : index < actIndex ? "done" : ""}>
                <button onClick={() => { setFinished(false); clock.seek(item.start + 0.01); }}>
                  <span className="act-bar"><i style={{ width: `${progress * 100}%` }} /></span>
                  <span className="act-name"><b className="num">{String(item.index).padStart(2, "0")}</b>{item.title}</span>
                </button>
              </li>
            );
          })}
        </ol>
        <div className="demo-top-actions">
          <span className="demo-badge"><ShieldCheck size={14} />演示剧本</span>
          <button className="icon-btn" onClick={fullscreen} aria-label="全屏"><Maximize2 size={17} /></button>
          <a className="icon-btn" href={href("dashboard")} aria-label="退出演示"><X size={18} /></a>
        </div>
      </header>

      <section className="demo-caption" key={act.key}>
        <span className="caption-index num">{String(act.index).padStart(2, "0")}<small>/ 06</small></span>
        <h1>{act.title}</h1>
        <p>{act.caption}</p>
      </section>

      <aside className={`demo-log ${frame.alertReady ? "dim" : ""}`} aria-label="AI 思维日志">
        <header><History size={16} />机器人看到了什么<span className="num">{clock.t.toFixed(1)}s</span></header>
        <ol ref={logRef}>
          {log.map((entry) => (
            <li key={entry.t} className={entry.tone ?? ""}>
              <span className="num">{entry.t.toFixed(1)}</span>
              <div><strong>{entry.text}</strong>{entry.code && <code>{entry.code}</code>}</div>
            </li>
          ))}
        </ol>
      </aside>

      {!medication && clock.t >= 19 && (
        <section className="demo-event demo-off">
          <header><ClipboardCheck size={18} /><span>用药辅助插件已停用</span></header>
          <p>机器人仍然看到了拿药和手靠近嘴边的动作，但没有插件来理解“这是在吃药”，所以不会生成事件，也不会提醒家属。</p>
          <a className="btn btn-primary" href={href("plugins")}>去插件中心开启</a>
        </section>
      )}

      {medication && (frame.phase === "event" || frame.phase === "alert" || finished) ? (
        <section className={`demo-event ${frame.alertReady ? "shifted" : ""}`}>
          <header><ClipboardCheck size={18} /><span>用药辅助 · 判断依据</span></header>
          <ol className="demo-chain">
            {frame.steps.map((step, index) => (
              <li key={step.key} style={{ ["--i" as string]: index }} className={step.done ? "on" : ""}>
                <span className="chain-dot"><Check size={14} strokeWidth={3} /></span>
                <strong>{step.label}</strong>
                <b className="num">{percent(step.confidence)}</b>
              </li>
            ))}
          </ol>
          <div className="demo-verdict">
            <strong>疑似完成服药</strong>
            <span>置信度 <b className="num">78%</b> · 待人工复核</span>
            <small>辅助判断，不是医学诊断</small>
          </div>
        </section>
      ) : null}

      {frame.alertReady && (
        <section className="demo-notify" role="status">
          <div className="notify-app"><Bell size={15} />Sentinel · 家属端<span>刚刚</span></div>
          <strong>爷爷 疑似完成早间服药</strong>
          <p>08:01 在客厅茶几拿起降压药盒并有手部接近面部动作。AI 辅助判断，请确认。</p>
          <div className="notify-actions"><span>查看推理</span><span className="primary">确认已服药</span></div>
        </section>
      )}

      <footer className="demo-controls">
        <button className="icon-btn" onClick={() => (finished ? restart() : clock.toggle())} aria-label={clock.playing ? "暂停" : "播放"}>{clock.playing ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}</button>
        <button className="icon-btn" onClick={restart} aria-label="重播"><RotateCcw size={17} /></button>
        <span className="demo-keys"><kbd>空格</kbd> 播放 / 暂停　<kbd>←</kbd><kbd>→</kbd> 切换　<kbd>R</kbd> 重播　<kbd>F</kbd> 全屏　<kbd>Esc</kbd> 退出</span>
      </footer>

      {finished && (
        <div className="demo-end">
          <div className="demo-end-card">
            <span className="eyebrow">演示完成</span>
            <h2>从看见，到理解，到提醒</h2>
            <p>人物、物品、动作被转化为可解释、可复核的事件；全程不展示原始画面。</p>
            <div className="demo-end-actions">
              <button className="btn btn-ghost" onClick={restart}><RotateCcw size={16} />再演示一次</button>
              <a className="btn btn-primary" href={href("events", created?.event_id ?? null)}>查看事件推理<ArrowRight size={16} /></a>
            </div>
            {mode === "real" && <small className="faint">当前为实时 API 模式：演示剧本没有写入事件。</small>}
          </div>
        </div>
      )}
    </div>
  );
}
