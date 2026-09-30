import { useMemo } from "react";
import { useRuntime } from "../app/runtime";
import { applyPluginWatch, isPluginRunning, watchedCategories } from "../engine/pluginCore";
import type { ObjectCategory } from "../engine/labels";
import type { SceneFrame } from "../engine/scene/types";
import type { Plugin, UnifiedEvent } from "../types";
import { resolvePlugin } from "./registry";
import type { FrontendPlugin, PluginContext } from "./sdk";

export interface PluginSlot {
  plugin: Plugin;
  def: FrontendPlugin;
  /** True when the plugin ships a frontend definition; false means the generic card is used. */
  builtin: boolean;
  running: boolean;
  events: UnifiedEvent[];
}

/**
 * The plugin host joins the backend plugin list (source of truth for what is
 * installed and enabled) with frontend definitions (how each one is shown).
 */
export function usePluginHost() {
  const { plugins, events, objects, mode } = useRuntime();
  const slots = useMemo<PluginSlot[]>(() => plugins.map((plugin) => {
    const { def, builtin } = resolvePlugin(plugin, events);
    return { plugin, def, builtin, running: isPluginRunning(plugin), events: events.filter((event) => event.plugin_id === plugin.plugin_id) };
  }), [plugins, events]);
  const running = useMemo(() => slots.filter((slot) => slot.running), [slots]);
  const watched = useMemo<Set<ObjectCategory>>(() => watchedCategories(plugins, slots.map((slot) => ({ plugin_id: slot.plugin.plugin_id, watches: slot.def.watches }))), [plugins, slots]);

  return {
    slots,
    running,
    watched,
    /** Filter a scene frame down to what running plugins are allowed to mark. */
    filterFrame: (frame: SceneFrame | null) => applyPluginWatch(frame, watched),
    contextFor: (slot: PluginSlot, frame: SceneFrame | null): PluginContext => ({ plugin: slot.plugin, mode, frame, events: slot.events, objects }),
    labelOf: (pluginId: string) => slots.find((slot) => slot.plugin.plugin_id === pluginId)?.def.label ?? pluginId,
  };
}
