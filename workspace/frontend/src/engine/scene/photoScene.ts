import { clamp01 } from "./poses.ts";
import { COCO17, STAGE_HEIGHT, STAGE_WIDTH, type Joint, type Keypoints, type SceneFact, type SceneFrame, type ScenePerson, type SceneSource } from "./types.ts";

/**
 * `public/demo-scene/scene.json` written by ai-engine/tools/build_privacy_scene.py:
 * a photo with people already removed, plus each person's real COCO17
 * keypoints in photo pixels.
 */
export interface PhotoPerson {
  id: string;
  confidence: number;
  bbox: [number, number, number, number];
  keypoints: Record<string, [number, number, number]>;
  /** Decision from ai-engine render_policy.py; missing means unregistered (fail closed). */
  render?: { mode: string; display_name: string | null; similarity: number | null; alert: boolean };
}

export interface PhotoSceneConfig {
  image: string;
  width: number;
  height: number;
  room?: string;
  source?: string;
  persons: PhotoPerson[];
}

export function isPhotoSceneConfig(value: unknown): value is PhotoSceneConfig {
  const config = value as PhotoSceneConfig;
  return Boolean(config) && typeof config.image === "string" && config.width > 0 && config.height > 0 && Array.isArray(config.persons);
}

/** Same "cover" crop the stage applies to the <image>, so keypoints stay glued to the photo. */
export function photoProjector(width: number, height: number) {
  const scale = Math.max(STAGE_WIDTH / width, STAGE_HEIGHT / height);
  const offsetX = (STAGE_WIDTH - width * scale) / 2;
  const offsetY = (STAGE_HEIGHT - height * scale) / 2;
  return (x: number, y: number): [number, number] => [offsetX + x * scale, offsetY + y * scale];
}

function describePose(keypoints: Keypoints): string {
  const best = (a?: Joint, b?: Joint) => (a && b ? (a[2] >= b[2] ? a : b) : a ?? b);
  const hip = best(keypoints.left_hip, keypoints.right_hip);
  const knee = best(keypoints.left_knee, keypoints.right_knee);
  const shoulder = best(keypoints.left_shoulder, keypoints.right_shoulder);
  if (!hip || !shoulder) return "—";
  if (!knee || knee[2] < 0.3) return "上半身可见";
  const torso = Math.abs(hip[1] - shoulder[1]);
  // Thigh roughly horizontal relative to the torso length means sitting.
  return Math.abs(knee[1] - hip[1]) < torso * 0.45 ? "坐姿" : "站立";
}

export const PHOTO_DURATION = 8;

/**
 * A still photo replayed as an 8-second loop that shows the pipeline on the
 * real keypoints: person detected → skeleton grows → cartoon replaces the person.
 */
export function buildPhotoScene(config: PhotoSceneConfig): SceneSource {
  const project = photoProjector(config.width, config.height);
  const room = config.room ?? "监护区域";
  const persons: ScenePerson[] = config.persons.map((person, index) => {
    const keypoints: Keypoints = {};
    COCO17.forEach((name) => {
      const point = person.keypoints[name];
      if (point) {
        const [x, y] = project(point[0], point[1]);
        keypoints[name] = [x, y, point[2]] satisfies Joint;
      }
    });
    const registered = person.render?.mode === "avatar";
    const label = registered ? person.render?.display_name ?? `人物 ${index + 1}` : "未登记人员";
    return { id: person.id, label, identified: false, render: registered ? "avatar" : "unregistered", keypoints, confidence: person.confidence, opacity: 1, pose: describePose(keypoints), action: "静止", zone: room } satisfies ScenePerson;
  });
  const hasStranger = persons.some((person) => person.render === "unregistered");

  const markers: SceneFact[] = persons.length
    ? [
      { t: 0.8, fact_type: "person_detected", confidence: persons[0].confidence, location: room },
      ...(hasStranger ? [{ t: 3.0, fact_type: "unregistered_person", confidence: persons[0].confidence, location: room }] : []),
    ]
    : [];

  function sample(t: number): SceneFrame {
    const person = persons[0] ?? null;
    const facts = markers.filter((fact) => fact.t <= t);
    return {
      t,
      duration: PHOTO_DURATION,
      phase: !person ? "idle" : t < 1.2 ? "person" : "recognize",
      // "identified" here means the skeleton is locked, not that the person's identity is known.
      person: person ? { ...person, opacity: clamp01(t / 0.5), identified: t >= 2.8, render: t >= 2.8 ? person.render : "pending", action: t >= 2.8 ? person.pose : "识别中" } : null,
      objects: [],
      facts,
      latestFact: facts[facts.length - 1] ?? null,
      skeletonReveal: clamp01((t - 1.2) / 1.6),
      cartoonReveal: clamp01((t - 3.4) / 1.2),
      steps: [],
      eventReady: false,
      alertReady: false,
    };
  }

  return { kind: "mock", duration: PHOTO_DURATION, sample, markers };
}
