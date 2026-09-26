import type { LucideIcon } from "lucide-react";

export function StatisticCard({ icon: Icon, label, value, detail, tone }: { icon: LucideIcon; label: string; value: string; detail: string; tone: string }) {
  return <article className={`ai-stat-card ${tone}`}><div className="ai-stat-top"><span className="ai-stat-icon"><Icon size={17} /></span><span>{detail}</span></div><strong>{value}</strong><label>{label}</label></article>;
}
