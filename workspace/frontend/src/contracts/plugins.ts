export type PluginLifecycleState = "registered" | "enabled" | "running" | "disabled" | "degraded" | "error";

/** Stable plugin status consumed by the frontend runtime registry. */
export interface PluginContract {
  plugin_id: string;
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  state: PluginLifecycleState;
  error?: string | null;
}
