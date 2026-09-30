import type { GlyphKind, ObjectCategory } from "../labels.ts";

export const STAGE_WIDTH = 1600;
export const STAGE_HEIGHT = 1000;

export const COCO17 = [
  "nose", "left_eye", "right_eye", "left_ear", "right_ear",
  "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
  "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle",
] as const;

export type JointName = (typeof COCO17)[number];
/** `[x, y, confidence]` in stage coordinates, the same shape as the backend skeleton contract. */
export type Joint = [number, number, number];
export type Keypoints = Partial<Record<JointName, Joint>>;

export const BONES: Array<[JointName, JointName]> = [
  ["left_shoulder", "right_shoulder"], ["left_hip", "right_hip"],
  ["left_shoulder", "left_hip"], ["right_shoulder", "right_hip"],
  ["left_shoulder", "left_elbow"], ["left_elbow", "left_wrist"],
  ["right_shoulder", "right_elbow"], ["right_elbow", "right_wrist"],
  ["left_hip", "left_knee"], ["left_knee", "left_ankle"],
  ["right_hip", "right_knee"], ["right_knee", "right_ankle"],
  ["nose", "left_eye"], ["nose", "right_eye"], ["left_eye", "left_ear"], ["right_eye", "right_ear"],
];

export type ObjectState = "hidden" | "detected" | "held";

export interface SceneObject {
  id: string;
  label: string;
  glyph: GlyphKind;
  /** Plugins declare which categories they watch; the stage only marks watched objects. */
  category: ObjectCategory;
  medication: boolean;
  x: number;
  y: number;
  w: number;
  h: number;
  confidence: number;
  state: ObjectState;
  /** 0..1 lock-on animation progress of the detection frame. */
  lock: number;
}

/**
 * From the AI render policy (ai-engine render_policy.py): registered people are
 * shown as a cartoon avatar, unregistered people as skeleton only with an alert.
 * "pending" means identity has not been decided yet.
 */
export type PersonRenderMode = "avatar" | "unregistered" | "pending";

export interface ScenePerson {
  id: string;
  label: string;
  identified: boolean;
  render: PersonRenderMode;
  keypoints: Keypoints;
  confidence: number;
  opacity: number;
  pose: string;
  action: string;
  zone: string;
}

export interface SceneFact {
  t: number;
  fact_type: string;
  confidence: number;
  location: string;
}

export interface MedicationStep {
  key: string;
  label: string;
  done: boolean;
  confidence: number | null;
}

export type ScenePhase = "idle" | "person" | "recognize" | "object" | "action" | "event" | "alert";

export interface SceneFrame {
  t: number;
  duration: number;
  phase: ScenePhase;
  person: ScenePerson | null;
  objects: SceneObject[];
  facts: SceneFact[];
  latestFact: SceneFact | null;
  /** 0..1 progress of skeleton growth; 1 means the full skeleton is locked. */
  skeletonReveal: number;
  /** 0..1 progress of the cartoon avatar replacing the skeleton-only view. */
  cartoonReveal: number;
  steps: MedicationStep[];
  eventReady: boolean;
  alertReady: boolean;
}

export interface SceneSource {
  kind: "mock" | "real";
  duration: number;
  sample(t: number): SceneFrame;
  /** Timeline markers used by scrubbers. */
  markers: SceneFact[];
}
