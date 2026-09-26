import type { PluginRuntimeDefinition } from "./types";
import { registerPlugin } from "./registry";

/** Extension point for a plugin package to register its UI definition. */
export function loadPluginDefinition(definition: PluginRuntimeDefinition): PluginRuntimeDefinition {
  registerPlugin(definition);
  return definition;
}
