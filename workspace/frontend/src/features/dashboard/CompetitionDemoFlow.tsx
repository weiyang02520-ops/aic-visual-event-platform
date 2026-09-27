import { Activity, Box, Check, ClipboardCheck, Eye, UserRound } from "lucide-react";
import type { RuntimeSnapshot } from "../../api/ai-runtime-adapter";

function factLabel(value: string) {
  const labels: Record<string, string> = {
    person_entered_zone: "人物进入监控区",
    object_detected: "检测到药盒",
    hand_near_object: "手靠近药盒",
    object_picked: "检测拿取动作",
    hand_to_face: "动作链完成",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

export function CompetitionDemoFlow({ runtime }: { runtime: RuntimeSnapshot }) {
  const event = runtime.events[0];
  const person = runtime.persons[0];
  const object = runtime.objects[0];
  const plugin = event ? runtime.plugins.find((item) => item.plugin_id === event.plugin_id) : runtime.plugins[0];
  const reasoning = Array.isArray(event?.metadata.reasoning_chain) ? event?.metadata.reasoning_chain as Array<{ fact_type?: unknown; confidence?: unknown }> : [];
  const action = String(reasoning.find((step) => step.fact_type === "hand_near_object")?.fact_type ?? event?.facts[0]?.fact_type ?? "");
  const evidence = event?.evidence[0];
  const subject = event?.subject ?? {};
  const runtimeObject = event?.object ?? {};
  const stages = [
    { key: "person", icon: UserRound, label: "人物", value: person?.display_name ?? "等待人物", detail: person ? `${String(subject.identity_status ?? person.role)} · ${String(subject.privacy_mode ?? person.status)}` : "等待 runtime 数据" },
    { key: "object", icon: Box, label: "对象", value: object?.name ?? "等待药盒", detail: object ? `${String(runtimeObject.category ?? object.description)} · ${String(runtimeObject.state ?? object.status)}` : "等待对象检测" },
    { key: "action", icon: Activity, label: "动作", value: action ? factLabel(action) : "等待动作", detail: event ? `${Math.round(Number(runtimeObject.confidence ?? event.confidence) * 100)}% confidence` : "等待事实链" },
    { key: "event", icon: Eye, label: "事件", value: event?.title ?? "等待事件", detail: event?.review_status === "pending" ? "待人工复核" : event?.review_status ?? "等待事件生成" },
    { key: "plugin", icon: ClipboardCheck, label: "插件", value: plugin?.name ?? "等待插件", detail: plugin?.state ?? "等待插件响应" },
    { key: "evidence", icon: Check, label: "证据", value: evidence?.status ?? "等待证据", detail: evidence?.source_id ?? "等待证据时间窗" },
  ];
  return <section className="panel competition-demo-flow"><div className="panel-heading"><div><span className="panel-kicker">COMPETITION DEMO / ELDERLY CARE</span><h2>老人用药辅助演示链路</h2><p className="competition-demo-lead">人物 → 药盒 → 动作事实 → 事件 → 插件 → 证据</p></div><span className="competition-demo-source">{runtime.events.length ? "runtime ready" : "等待 runtime"}</span></div><div className="competition-demo-stages">{stages.map((stage) => { const Icon = stage.icon; const ready = stage.key === "person" ? Boolean(person) : stage.key === "object" ? Boolean(object) : stage.key === "action" ? Boolean(action) : stage.key === "event" ? Boolean(event) : stage.key === "plugin" ? Boolean(plugin) : Boolean(evidence); return <div className={`competition-demo-stage ${ready ? "ready" : "pending"}`} key={stage.key}><span className="competition-demo-icon"><Icon size={16} /></span><div><small>{stage.label}</small><strong>{stage.value}</strong><span>{stage.detail}</span></div></div>; })}</div></section>;
}
