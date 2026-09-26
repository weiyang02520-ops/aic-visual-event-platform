import { Activity, AlertTriangle, BrainCircuit, Camera, Network, Server, UsersRound } from "lucide-react";
import type { DashboardSnapshotContract, HealthStatus } from "../../contracts";
import { StatisticCard } from "./StatisticCard";

const statusLabels: Record<HealthStatus, string> = { healthy: "healthy", warning: "warning", offline: "offline" };

function statusTone(status: HealthStatus) {
  return status === "healthy" ? "healthy" : status === "warning" ? "warning" : "offline";
}

const healthIcons = { camera: Camera, ai_model: BrainCircuit, plugin_runtime: Network, backend: Server };

export function AIDashboardOverview({ snapshot }: { snapshot: DashboardSnapshotContract }) {
  const sourceLabel = snapshot.source === "mock" ? "Mock 演示数据" : "Real API 数据源";
  const stats = [
    { icon: UsersRound, label: "当前检测人数", value: String(snapshot.stats.detected_people), detail: sourceLabel, tone: "cyan" },
    { icon: Activity, label: "今日事件数量", value: String(snapshot.stats.event_count).padStart(2, "0"), detail: "事件 Contract", tone: "violet" },
    { icon: Network, label: "运行插件数量", value: `${snapshot.stats.running_plugins}/${snapshot.stats.total_plugins}`, detail: "Plugin Contract", tone: "green" },
    { icon: AlertTriangle, label: "异常数量", value: String(snapshot.stats.exception_count).padStart(2, "0"), detail: snapshot.stats.exception_count ? "需要关注" : "当前无异常", tone: snapshot.stats.exception_count ? "amber" : "blue" },
  ];
  return <section className="ai-dashboard-overview">
    <div className="ai-dashboard-heading"><div><span className="panel-kicker">AI RUNTIME / OVERVIEW</span><h2>AI 总览</h2><p>当前数据源下的检测、事件、插件和系统健康状态。</p></div><span className={`ai-overall-status ${statusTone(snapshot.status)}`}><i />{statusLabels[snapshot.status]}</span></div>
    <div className="ai-stat-grid">{stats.map((stat) => <StatisticCard key={stat.label} {...stat} />)}</div>
    <section className="panel ai-health-panel"><div className="panel-heading"><div><span className="panel-kicker">SYSTEM HEALTH / PROVIDERS</span><h2>系统健康状态</h2></div><span className="ai-health-source">{sourceLabel}</span></div><div className="ai-health-grid">{snapshot.health.map((check) => { const Icon = healthIcons[check.id as keyof typeof healthIcons] ?? Server; return <div className="ai-health-row" key={check.id}><span className={`ai-health-icon ${statusTone(check.status)}`}><Icon size={17} /></span><div><strong>{check.label}</strong><small>{check.detail}</small></div><em className={statusTone(check.status)}><i />{statusLabels[check.status]}</em></div>; })}</div></section>
  </section>;
}
