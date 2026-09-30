import { Database, Eye, Plug, ShieldCheck } from "lucide-react";
import { AI_API_URL, connectionLabel, useRuntime } from "../../app/runtime";
import { Dot, Panel, Pill, Segmented } from "../../design/ui";
import { systemRows } from "../shared";
import "./settings.css";

export function SettingsPage() {
  const runtime = useRuntime();
  const { mode, setMode, connection } = runtime;
  const rows = systemRows(runtime);
  return (
    <div className="page settings-page">
      <header className="page-head">
        <div><h1>系统设置</h1><p>数据源、运行状态与隐私边界。</p></div>
      </header>
      <div className="grid-2">
        <Panel title="数据源" icon={<Database size={18} />}>
          <div className="set-row">
            <div><strong>运行模式</strong><span>演示数据用于离线展示；实时 API 连接 AI 服务，离线时不会回退到演示数据。</span></div>
            <Segmented label="数据源" value={mode} onChange={setMode} options={[{ value: "mock", label: "演示" }, { value: "real", label: "实时 API" }]} />
          </div>
          <div className="set-row"><div><strong>连接状态</strong><span>{connection.reason ?? "—"}</span></div><Pill tone={connection.status === "offline" ? "risk" : connection.status === "loading" ? "warn" : "ok"}>{connectionLabel(connection)}</Pill></div>
          <div className="set-row"><div><strong>AI 服务地址</strong><span>VITE_AI_API_URL</span></div><code>{AI_API_URL}</code></div>
          <div className="set-row"><div><strong>隐私预览源</strong><span>VITE_AI_PREVIEW_SOURCE，实时隐私舞台读取 /api/v1/vision/preview</span></div><code>{import.meta.env.VITE_AI_PREVIEW_SOURCE ?? "未配置"}</code></div>
        </Panel>
        <Panel title="运行状态" icon={<Plug size={18} />}>
          <ul className="set-status">
            {rows.map((row) => <li key={row.id}><Dot tone={row.tone} /><div><strong>{row.label}</strong><span>{row.detail}</span></div><b>{row.value}</b></li>)}
          </ul>
        </Panel>
        <Panel title="隐私边界" icon={<ShieldCheck size={18} />} className="set-privacy">
          <ul className="set-list">
            <li><Eye size={16} /><span>界面只渲染骨骼关键点和卡漫形象，不提供原始画面入口；隐私渲染不可用时保持关闭，不回退到原始视频。</span></li>
            <li><ShieldCheck size={16} /><span>脱敏发生在软件边界，不代表摄像头端已删除原始帧。</span></li>
            <li><ShieldCheck size={16} /><span>事件是 AI 辅助判断，不是医学诊断；“疑似 / 候选”需要人工复核。</span></li>
            <li><ShieldCheck size={16} /><span>只有证据状态为 available 且带有地址时才显示回放。</span></li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}
