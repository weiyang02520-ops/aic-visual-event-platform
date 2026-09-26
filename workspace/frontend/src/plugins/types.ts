import type { PluginContract } from "../contracts";

export type PluginKind = "medicine" | "object" | "generic";
export type PluginIcon = "medicine" | "object" | "generic";
export type RuntimeTimelineKind = "person" | "medicine" | "object" | "status";

export interface RuntimeTimelineEntry {
  id: string;
  time: string;
  title: string;
  detail: string;
  kind: RuntimeTimelineKind;
}

export interface PluginRuntimeDefinition {
  plugin_id: string;
  kind: PluginKind;
  icon: PluginIcon;
  label?: string;
  mockTimeline?: RuntimeTimelineEntry[];
}

export interface PluginRegistration {
  plugin: PluginContract;
  definition: PluginRuntimeDefinition;
}
