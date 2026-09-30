import type { FrontendPlugin } from "./sdk";
import { registerPlugin } from "./registry";

// Auto-discovery, like the backend's ai-engine/plugins/*/manifest.json scan:
// every file in ./builtin that default-exports a definePlugin() is registered.
const modules = import.meta.glob<{ default: FrontendPlugin }>("./builtin/*.tsx", { eager: true });
Object.values(modules).forEach((module) => registerPlugin(module.default));

export { definePlugin } from "./sdk";
export type { FrontendPlugin, PluginContext, PluginSummary } from "./sdk";
export { genericPlugin, lifecycleLabel, registeredPlugins, registerPlugin, resolvePlugin } from "./registry";
export { usePluginHost, type PluginSlot } from "./host";
