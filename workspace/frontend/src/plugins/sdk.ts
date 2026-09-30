import type { ComponentType } from "react";
import type { LucideIcon } from "lucide-react";
import type { ObjectCategory } from "../engine/labels";
import type { SceneFrame } from "../engine/scene/types";
import type { Tone } from "../design/ui";
import type { Mode, Plugin, RegisteredObject, UnifiedEvent } from "../types";

/**
 * Frontend half of a scene plugin. The backend half (manifest.json + plugin.py
 * under ai-engine/plugins/) turns facts into events; this half decides how the
 * plugin shows up in the UI. Both are keyed by the same `id` / `plugin_id`.
 */
export interface PluginContext {
  plugin: Plugin;
  mode: Mode;
  frame: SceneFrame | null;
  /** Events emitted by this plugin only. */
  events: UnifiedEvent[];
  objects: RegisteredObject[];
}

export interface PluginSummary {
  headline: string;
  detail: string;
  tone: Tone;
}

export interface FrontendPlugin {
  id: string;
  label: string;
  scene: string;
  icon: LucideIcon;
  description: string;
  /** Fact types the backend plugin consumes. */
  inputs: string[];
  /** Event kinds the plugin produces. */
  outputs: string[];
  /** Object categories marked on the privacy stage while the plugin runs. */
  watches: ObjectCategory[];
  /** Live card on the privacy monitor page. */
  Panel: ComponentType<PluginContext>;
  /** One-line status for the dashboard. */
  summarize: (context: PluginContext) => PluginSummary;
}

export function definePlugin(plugin: FrontendPlugin): FrontendPlugin {
  return plugin;
}
