import { useMemo } from "react";
import { useRuntime } from "../app/runtime";
import { createMockSceneSource } from "../engine/scene/mockScript";
import type { SceneFrame, SceneSource } from "../engine/scene/types";
import { useRealScene, type RealSceneStatus } from "./useRealScene";
import { useSceneBackdrop } from "./useSceneBackdrop";
import { useSceneClock, type SceneClock } from "./useSceneClock";

/** Demo sources: the rehearsed medication story, or an installed real photo scene. */
export type DemoSource = "script" | "photo";

export interface LiveScene {
  source: SceneSource | null;
  frame: SceneFrame | null;
  clock: SceneClock;
  status: RealSceneStatus | "mock";
  reason: string;
  /** Environment photo behind the person (Mock only), or null for the neutral grid. */
  backdropImage: string | null;
  isPhoto: boolean;
  /** Whether a real photo scene is installed and can be selected. */
  photoAvailable: boolean;
  room: string;
}

/**
 * Mock: the rehearsed medication story by default; `demo: "photo"` switches to
 * the installed photo scene with real keypoints. Real: vision-preview geometry,
 * or a closed stage with a reason.
 */
export function useLiveScene(options: { start?: number; demo?: DemoSource } = {}): LiveScene {
  const { mode, connection } = useRuntime();
  const real = useRealScene(mode, connection);
  const backdrop = useSceneBackdrop();
  const usePhoto = options.demo === "photo" && Boolean(backdrop.photo);
  const scripted = useMemo(() => createMockSceneSource(backdrop.layout), [backdrop.layout]);
  const mockSource = usePhoto ? backdrop.photo : scripted;
  const source = mode === "mock" ? (backdrop.ready ? mockSource : null) : real.source;
  const clock = useSceneClock(source?.duration ?? 0, { loop: true, autoplay: true, start: usePhoto ? 0 : options.start ?? 0 });
  const frame = useMemo(() => (source ? source.sample(Math.min(clock.t, source.duration)) : null), [source, clock.t]);
  // A photo that belongs to the photo scene must not sit behind the scripted person.
  const scriptBackdrop = backdrop.photo ? null : backdrop.image;
  return {
    source, frame, clock,
    status: mode === "mock" ? "mock" : real.status,
    reason: mode === "mock" && !backdrop.ready ? "正在加载场景" : real.reason,
    backdropImage: mode === "mock" ? (usePhoto ? backdrop.image : scriptBackdrop) : null,
    isPhoto: mode === "mock" && usePhoto,
    photoAvailable: Boolean(backdrop.photo),
    room: mode === "mock" && usePhoto ? backdrop.room : "客厅",
  };
}
