import type { PluginContract, PluginLifecycleState } from "../contracts";
import type { Plugin } from "../types";

const lifecycleStates = new Set<PluginLifecycleState>(["registered", "enabled", "running", "disabled", "degraded", "error"]);

function normalizeState(plugin: Plugin): PluginLifecycleState {
  if (lifecycleStates.has(plugin.state as PluginLifecycleState)) return plugin.state as PluginLifecycleState;
  return plugin.enabled ? "enabled" : "disabled";
}

/** Convert the legacy repository shape into the frozen Plugin Contract. */
export function toPluginContract(plugin: Plugin): PluginContract {
  const state = normalizeState(plugin);
  return {
    plugin_id: plugin.plugin_id,
    name: plugin.name,
    version: plugin.version,
    description: plugin.description,
    enabled: plugin.enabled,
    state,
    error: plugin.error ?? null,
  };
}
