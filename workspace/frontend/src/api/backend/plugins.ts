import type { PluginContract } from "../../contracts";
import type { BackendApiClient } from "./client";

export function createPluginsApi(client: BackendApiClient) {
  return {
    list: () => client.get<PluginContract[]>("/api/v1/plugins"),
    toggle: (pluginId: string, enabled: boolean) => client.post<PluginContract>(`/api/v1/plugins/${encodeURIComponent(pluginId)}/${enabled ? "enable" : "disable"}`),
  };
}
