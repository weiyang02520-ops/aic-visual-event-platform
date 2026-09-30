import { useEffect, useState } from "react";
import { DEFAULT_LAYOUT, layoutFromConfig, type SceneConfig, type SceneLayout } from "../engine/scene/layout";
import { buildPhotoScene, isPhotoSceneConfig } from "../engine/scene/photoScene";
import type { SceneSource } from "../engine/scene/types";

export interface SceneBackdrop {
  /** URL of the environment photo (people already removed), or null when none is configured. */
  image: string | null;
  /** Layout for the rehearsed medication script. */
  layout: SceneLayout;
  /** A photo scene with real keypoints, when scene.json carries `persons`. */
  photo: SceneSource | null;
  room: string;
  ready: boolean;
}

const BASE = `${import.meta.env.BASE_URL}demo-scene/`;
const EMPTY: SceneBackdrop = { image: null, layout: DEFAULT_LAYOUT, photo: null, room: "客厅", ready: true };
let cache: Promise<SceneBackdrop> | null = null;

function load(): Promise<SceneBackdrop> {
  cache ??= fetch(`${BASE}scene.json`)
    .then((response) => (response.ok ? response.json() : Promise.reject(new Error(String(response.status)))))
    .then((config: unknown): SceneBackdrop => {
      if (isPhotoSceneConfig(config)) {
        return { image: `${BASE}${config.image}`, layout: DEFAULT_LAYOUT, photo: buildPhotoScene(config), room: config.room ?? "监护区域", ready: true };
      }
      const scripted = config as SceneConfig;
      return { image: `${BASE}${scripted.image}`, layout: layoutFromConfig(scripted), photo: null, room: "客厅", ready: true };
    })
    .catch(() => EMPTY);
  return cache;
}

/**
 * Environment for the privacy stage. The room stays as photographed; only
 * people are replaced by a skeleton or cartoon drawn from keypoints.
 */
export function useSceneBackdrop(): SceneBackdrop {
  const [state, setState] = useState<SceneBackdrop>({ ...EMPTY, ready: false });
  useEffect(() => {
    let active = true;
    void load().then((value) => { if (active) setState(value); });
    return () => { active = false; };
  }, []);
  return state;
}
