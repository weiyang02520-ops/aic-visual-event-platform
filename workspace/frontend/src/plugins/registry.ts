import type { PluginContract } from "../contracts";
import type { UnifiedEvent } from "../types";
import type { PluginKind, PluginRegistration, PluginRuntimeDefinition, RuntimeTimelineEntry, RuntimeTimelineKind } from "./types";

const builtInDefinitions: PluginRuntimeDefinition[] = [
  {
    plugin_id: "elderly_care",
    kind: "medicine",
    icon: "medicine",
    label: "用药辅助",
    mockTimeline: [
      { id: "medicine-pick", time: "07:58", title: "拿起药盒", detail: "手接触药盒", kind: "medicine" },
      { id: "medicine-face", time: "08:01", title: "手靠近面部", detail: "疑似服药行为", kind: "medicine" },
      { id: "medicine-return", time: "08:05", title: "放回药盒", detail: "回到桌面区域", kind: "medicine" },
    ],
  },
  {
    plugin_id: "workshop",
    kind: "object",
    icon: "object",
    label: "物品看护",
    mockTimeline: [
      { id: "object-change", time: "08:04", title: "物品状态变化", detail: "关注区域位置更新", kind: "object" },
    ],
  },
];

const genericDefinition: PluginRuntimeDefinition = { plugin_id: "*", kind: "generic", icon: "generic" };

export class PluginRegistry {
  private readonly definitions = new Map<string, PluginRuntimeDefinition>();

  constructor(definitions: PluginRuntimeDefinition[] = []) {
    definitions.forEach((definition) => this.register(definition));
  }

  register(definition: PluginRuntimeDefinition): void {
    this.definitions.set(definition.plugin_id, { ...definition });
  }

  resolve(pluginId: string): PluginRuntimeDefinition {
    return this.definitions.get(pluginId) ?? genericDefinition;
  }

  entries(plugins: PluginContract[]): PluginRegistration[] {
    return plugins.map((plugin) => ({ plugin, definition: this.resolve(plugin.plugin_id) }));
  }

  enabled(plugins: PluginContract[]): PluginRegistration[] {
    return this.entries(plugins).filter(({ plugin }) => plugin.enabled && plugin.state !== "disabled" && plugin.state !== "error");
  }
}

export const pluginRegistry = new PluginRegistry(builtInDefinitions);

export function registerPlugin(definition: PluginRuntimeDefinition): void {
  pluginRegistry.register(definition);
}

export function getPluginPresentation(plugin: PluginContract) {
  const definition = pluginRegistry.resolve(plugin.plugin_id);
  return { ...definition, label: definition.label ?? plugin.name };
}

export function pluginLifecycleLabel(state: PluginContract["state"]): string {
  const labels: Record<PluginContract["state"], string> = {
    registered: "已注册",
    enabled: "已启用",
    running: "运行中",
    disabled: "已停用",
    degraded: "降级",
    error: "异常",
  };
  return labels[state];
}

export function pluginEventsFor(plugin: PluginContract, events: UnifiedEvent[]): UnifiedEvent[] {
  return events.filter((event) => event.plugin_id === plugin.plugin_id).slice(0, 2);
}

export function sceneSignals(plugins: PluginContract[]) {
  const active = pluginRegistry.enabled(plugins);
  const hasKind = (kind: PluginKind) => active.some(({ definition }) => definition.kind === kind);
  return {
    medicineEnabled: hasKind("medicine"),
    objectEnabled: hasKind("object"),
    primaryAction: hasKind("medicine") ? "手靠近药盒" : "基础轨迹",
  };
}

function factLabel(factType: string): string {
  const labels: Record<string, string> = {
    hand_near_object: "手靠近物品",
    hand_to_face: "手靠近面部",
    pickup_candidate: "拿起物品",
    putdown_candidate: "放回物品",
    entered_zone: "进入区域",
    left_zone: "离开区域",
    motion: "发生移动",
    object_in_zone: "物品位于区域",
    object_detected: "检测到物品",
  };
  return labels[factType] ?? factType.replaceAll("_", " ");
}

export function buildRuntimeTimeline(mode: "mock" | "real", events: UnifiedEvent[], plugins: PluginContract[]): RuntimeTimelineEntry[] {
  if (mode === "mock") {
    const entries: RuntimeTimelineEntry[] = [
      { id: "enter", time: "07:42", title: "进入客厅", detail: "连续轨迹建立", kind: "person" },
      { id: "settle", time: "08:12", title: "在沙发就座", detail: "持续静止", kind: "status" },
    ];
    const extras = pluginRegistry.enabled(plugins).flatMap(({ definition }) => definition.mockTimeline ?? []);
    return [...entries.slice(0, 1), ...extras, ...entries.slice(1)];
  }

  return events.flatMap((event) => {
    const definition = pluginRegistry.resolve(event.plugin_id);
    const kind: RuntimeTimelineKind = definition.kind === "medicine" ? "medicine" : definition.kind === "object" ? "object" : "status";
    return event.facts.map((fact, index) => ({
      id: `${event.event_id}-${index}`,
      time: new Date(event.started_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
      title: factLabel(fact.fact_type),
      detail: event.location ?? event.title,
      kind,
    }));
  }).slice(0, 8);
}
