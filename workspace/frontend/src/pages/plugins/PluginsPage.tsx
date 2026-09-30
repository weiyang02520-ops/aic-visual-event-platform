import { ArrowRight, Bell, Droplets, FileSearch, Footprints, Hand, MoonStar, Puzzle, ScanEye, ShieldAlert, Timer, UserRound } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { Dot, Empty, Panel, Pill, Switch } from "../../design/ui";
import { CATEGORY_LABELS, factLabel } from "../../engine/labels";
import { lifecycleLabel, usePluginHost, type PluginSlot } from "../../plugins";
import { isToday } from "../shared";
import "./plugins.css";

const ROADMAP = [
  { icon: ShieldAlert, title: "跌倒风险检测", detail: "身体姿态突然变化并长时间躺地时提醒" },
  { icon: Timer, title: "久坐提醒", detail: "长时间不动时提醒起身活动" },
  { icon: MoonStar, title: "夜间离床", detail: "夜里离开卧室时通知家属" },
  { icon: Droplets, title: "饮水提醒", detail: "根据拿水杯的次数估计喝水情况" },
];

const BACKEND_SNIPPET = `ai-engine/plugins/fall_risk/
├─ manifest.json   { "plugin_id": "fall_risk", "entrypoint": "plugin.py" }
└─ plugin.py       def evaluate(facts, source_id) -> list[UnifiedEvent]`;

const FRONTEND_SNIPPET = `// src/plugins/builtin/fallRisk.tsx
export default definePlugin({
  id: "fall_risk", label: "跌倒风险",
  watches: [], inputs: ["pose_changed"],
  Panel: FallRiskPanel,
  summarize: ({ events }) => ({ ... }),
});`;

function PluginCard({ slot, onToggle, disabled }: { slot: PluginSlot; onToggle: () => void; disabled: boolean }) {
  const { def, plugin, events, running, builtin } = slot;
  const Icon = def.icon;
  const tone = plugin.state === "error" ? "risk" : plugin.state === "degraded" ? "warn" : running ? "ok" : "neutral";
  return (
    <article className={`plugin-card panel ${running ? "on" : ""}`}>
      <header>
        <span className="plugin-icon"><Icon size={24} /></span>
        <div>
          <h3>{def.label}</h3>
          <span className="faint">{def.scene} · v{plugin.version}</span>
        </div>
        <Switch checked={plugin.enabled} onChange={onToggle} label={`${plugin.enabled ? "停用" : "启用"}${def.label}`} disabled={disabled || plugin.state === "error"} />
      </header>
      <p className="muted">{def.description}</p>
      <div className="plugin-io">
        <div><span className="eyebrow">需要的动作事实</span><div className="io-tags">{def.inputs.length ? def.inputs.map((input) => <span key={input}>{factLabel(input)}</span>) : <span>—</span>}</div></div>
        <div><span className="eyebrow">产出</span><div className="io-tags out">{def.outputs.length ? def.outputs.map((output) => <span key={output}>{output}</span>) : <span>—</span>}</div></div>
      </div>
      <dl className="plugin-meta">
        <div><dt>画面上识别</dt><dd>{def.watches.length ? def.watches.map((category) => CATEGORY_LABELS[category]).join("、") : "不标记物品"}</dd></div>
        <div><dt>界面</dt><dd>{builtin ? "专属界面" : "通用卡片（未提供界面扩展）"}</dd></div>
        <div><dt>插件编号</dt><dd>{plugin.plugin_id}</dd></div>
      </dl>
      <footer>
        <span className="plugin-state"><Dot tone={tone} live={tone === "ok"} />{lifecycleLabel(plugin.state)}{plugin.error ? ` · ${plugin.error}` : ""}</span>
        <span className="num">今日 {events.filter((event) => isToday(event.started_at)).length} 条 · 累计 {events.length} 条</span>
      </footer>
    </article>
  );
}

export function PluginsPage() {
  const { togglePlugin, canMutate, connection } = useRuntime();
  const host = usePluginHost();

  return (
    <div className="page plugins-page">
      <header className="page-head">
        <div>
          <h1>插件中心</h1>
          <p>机器人负责“看”，插件负责“懂场景”。开关插件，监护画面和提醒会跟着变化；想支持新场景，加一个插件就行。</p>
        </div>
        <div className="page-actions"><Pill tone="ok">{host.running.length} / {host.slots.length} 运行中</Pill></div>
      </header>

      <Panel title="插件怎么工作" icon={<Puzzle size={18} />} className="arch-panel">
        <div className="arch">
          <div className="arch-col">
            <span className="eyebrow">机器人视觉（常开）</span>
            <div className="arch-node"><UserRound size={18} />人物感知<small>17 个身体关键点</small></div>
            <div className="arch-node"><ScanEye size={18} />物品识别<small>检测 · 跟踪</small></div>
            <div className="arch-node"><Hand size={18} />基础动作<small>靠近 · 拿起 · 手到面部</small></div>
          </div>
          <div className="arch-link"><ArrowRight size={18} /></div>
          <div className="arch-col">
            <span className="eyebrow">统一事实</span>
            <div className="arch-node bus"><Footprints size={18} />行为事实<small>谁 · 什么时候 · 在哪 · 做了什么</small></div>
          </div>
          <div className="arch-link"><ArrowRight size={18} /></div>
          <div className="arch-col">
            <span className="eyebrow">场景插件（可开关）</span>
            {host.slots.map((slot) => {
              const Icon = slot.def.icon;
              return <button key={slot.plugin.plugin_id} className={`arch-node plugin ${slot.running ? "on" : "off"}`} onClick={() => void togglePlugin(slot.plugin)} disabled={!canMutate}><Icon size={18} />{slot.def.label}<small>{slot.running ? "运行中 · 点击停用" : "已停用 · 点击启用"}</small></button>;
            })}
            <div className="arch-node ghost"><Puzzle size={18} />新插件<small>放进插件目录即被发现</small></div>
          </div>
          <div className="arch-link"><ArrowRight size={18} /></div>
          <div className="arch-col">
            <span className="eyebrow">输出</span>
            <div className="arch-node"><FileSearch size={18} />事件分析<small>说明依据 · 人工确认</small></div>
            <div className="arch-node"><Bell size={18} />智能提醒<small>家属 / 护理人员</small></div>
          </div>
        </div>
      </Panel>

      <h2 className="section-title">已安装 <span className="faint">{host.slots.length}</span></h2>
      {host.slots.length ? (
        <div className="plugin-grid">
          {host.slots.map((slot) => <PluginCard key={slot.plugin.plugin_id} slot={slot} onToggle={() => void togglePlugin(slot.plugin)} disabled={!canMutate} />)}
        </div>
      ) : <Panel><Empty icon={<Puzzle size={24} />} title="没有已安装的插件">{connection.status === "offline" ? connection.reason : undefined}</Empty></Panel>}

      <h2 className="section-title">新增一个插件</h2>
      <div className="howto">
        <div className="howto-step panel">
          <span className="howto-no">1</span>
          <div><strong>后端：放进插件目录</strong><p className="muted">AI 服务启动时扫描 <code>ai-engine/plugins/*/manifest.json</code> 自动加载。插件只读取统一事实、输出事件，出错也不影响其他插件。</p></div>
          <pre>{BACKEND_SNIPPET}</pre>
        </div>
        <div className="howto-step panel">
          <span className="howto-no">2</span>
          <div><strong>前端：可选的界面扩展</strong><p className="muted">放进 <code>src/plugins/builtin/</code> 会被自动注册。不写也能用：没有界面扩展的插件会用通用卡片显示它的事件。</p></div>
          <pre>{FRONTEND_SNIPPET}</pre>
        </div>
      </div>

      <h2 className="section-title">规划中 <Pill>尚未实现</Pill></h2>
      <div className="roadmap-grid">
        {ROADMAP.map(({ icon: Icon, title, detail }) => (
          <div key={title} className="roadmap-card">
            <span className="plugin-icon ghost"><Icon size={22} /></span>
            <strong>{title}</strong>
            <span>{detail}</span>
            <small>概念，尚未接入</small>
          </div>
        ))}
      </div>
    </div>
  );
}
