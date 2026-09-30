import type { ObjectCategory } from "./labels.ts";
import type { SceneFrame } from "./scene/types.ts";

/** Pure plugin rules shared by the React plugin host and the unit tests. */

export interface PluginStateLike {
  plugin_id: string;
  enabled: boolean;
  state: string;
}

/** Mirrors the backend: a plugin evaluates facts only when enabled and not broken. */
export function isPluginRunning(plugin: PluginStateLike): boolean {
  return plugin.enabled && plugin.state !== "disabled" && plugin.state !== "error";
}

export interface WatchDeclaration {
  plugin_id: string;
  watches: ObjectCategory[];
}

export function watchedCategories(plugins: PluginStateLike[], declarations: WatchDeclaration[]): Set<ObjectCategory> {
  const running = new Set(plugins.filter(isPluginRunning).map((plugin) => plugin.plugin_id));
  return new Set(declarations.filter((item) => running.has(item.plugin_id)).flatMap((item) => item.watches));
}

/**
 * The person skeleton is a base capability and is always rendered. Object
 * markers only appear for categories that a running plugin watches; unwatched
 * objects stay in the room drawing but are not marked as recognised.
 */
export function applyPluginWatch(frame: SceneFrame | null, watched: Set<ObjectCategory>): SceneFrame | null {
  if (!frame) return frame;
  return {
    ...frame,
    objects: frame.objects.map((object) => (watched.has(object.category) ? object : { ...object, state: "hidden" as const, lock: 0 })),
  };
}
