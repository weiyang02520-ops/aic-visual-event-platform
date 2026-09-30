import { Puzzle } from "lucide-react";
import { Empty } from "../design/ui";
import { relativeTime } from "../engine/labels";
import type { Plugin } from "../types";
import { definePlugin, type FrontendPlugin, type PluginContext } from "./sdk";

const definitions = new Map<string, FrontendPlugin>();

export function registerPlugin(plugin: FrontendPlugin): void {
  definitions.set(plugin.id, plugin);
}

export function registeredPlugins(): FrontendPlugin[] {
  return [...definitions.values()];
}

function GenericPanel({ plugin, events }: PluginContext) {
  if (!events.length) return <Empty icon={<Puzzle size={20} />} title="插件运行中，还没有输出">{plugin.description}</Empty>;
  return (
    <ul className="fact-feed">
      {events.slice(0, 4).map((event) => <li key={event.event_id}><span>{relativeTime(event.started_at)}</span><strong>{event.title}</strong><b className="num">{Math.round(event.confidence * 100)}%</b></li>)}
    </ul>
  );
}

/**
 * A backend plugin without a frontend definition still works: it gets a
 * generic card built from its manifest and the events it emits, so a new
 * plugin shows up in the UI without any frontend change.
 */
export function genericPlugin(plugin: Plugin, events: Array<{ facts: Array<{ fact_type: string }>; event_type: string }> = []): FrontendPlugin {
  return definePlugin({
    id: plugin.plugin_id,
    label: plugin.name,
    scene: "自定义场景",
    icon: Puzzle,
    description: plugin.description,
    inputs: [...new Set(events.flatMap((event) => event.facts.map((fact) => fact.fact_type)))],
    outputs: [...new Set(events.map((event) => event.event_type))],
    watches: [],
    Panel: GenericPanel,
    summarize: ({ events: own }) => own[0]
      ? { headline: own[0].title, detail: relativeTime(own[0].started_at), tone: "accent" }
      : { headline: "等待插件输出", detail: plugin.description, tone: "neutral" },
  });
}

export function resolvePlugin(plugin: Plugin, events: UnifiedEventLike[] = []): { def: FrontendPlugin; builtin: boolean } {
  const def = definitions.get(plugin.plugin_id);
  return def ? { def, builtin: true } : { def: genericPlugin(plugin, events.filter((event) => event.plugin_id === plugin.plugin_id)), builtin: false };
}

type UnifiedEventLike = { plugin_id: string; event_type: string; facts: Array<{ fact_type: string }> };

export function lifecycleLabel(state: string): string {
  const labels: Record<string, string> = { registered: "已注册", enabled: "已启用", running: "运行中", disabled: "已停用", degraded: "降级运行", error: "加载失败" };
  return labels[state] ?? state;
}
