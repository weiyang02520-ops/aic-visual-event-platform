import { categoryOf, glyphOf } from "../labels.ts";
import { COCO17, STAGE_HEIGHT, STAGE_WIDTH, type Joint, type Keypoints, type SceneFact, type SceneFrame, type SceneObject, type SceneSource } from "./types.ts";

/** Subset of `ObservationView` from `/api/v1/vision/preview`. */
export interface PreviewObservation {
  source_id: string;
  timestamp: string;
  fact_type: string;
  confidence: number;
  subject?: Record<string, unknown> | null;
  object?: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
}

type Raw = { keypoints: Record<string, Joint>; bboxes: Array<{ label: string; bbox: [number, number, number, number]; confidence: number }> };

const STANDARD_SIZES: Array<[number, number]> = [[640, 480], [1280, 720], [1920, 1080], [2560, 1440], [3840, 2160]];

function isJoint(value: unknown): value is Joint {
  return Array.isArray(value) && value.length >= 3 && value.slice(0, 3).every((item) => typeof item === "number" && Number.isFinite(item));
}

function isBbox(value: unknown): value is [number, number, number, number] {
  return Array.isArray(value) && value.length === 4 && value.every((item) => typeof item === "number" && Number.isFinite(item));
}

/** Only canonical `metadata.skeleton.keypoints` (or flat `metadata.keypoints`) are read; malformed joints are dropped. */
export function skeletonOf(observation: PreviewObservation): Record<string, Joint> | null {
  const skeleton = observation.metadata?.skeleton as Record<string, unknown> | undefined;
  const raw = (skeleton?.keypoints ?? observation.metadata?.keypoints) as Record<string, unknown> | undefined;
  if (!raw || typeof raw !== "object") return null;
  const result: Record<string, Joint> = {};
  COCO17.forEach((name) => {
    if (isJoint(raw[name])) result[name] = raw[name] as Joint;
  });
  return Object.keys(result).length ? result : null;
}

function frameSize(frames: Raw[], metadata: Record<string, unknown> | undefined): [number, number] {
  const width = Number(metadata?.frame_width ?? metadata?.width);
  const height = Number(metadata?.frame_height ?? metadata?.height);
  if (width > 0 && height > 0) return [width, height];
  let maxX = 1;
  let maxY = 1;
  frames.forEach((frame) => {
    Object.values(frame.keypoints).forEach(([x, y]) => { maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); });
    frame.bboxes.forEach(({ bbox: [x, y, w, h] }) => { maxX = Math.max(maxX, x + w); maxY = Math.max(maxY, y + h); });
  });
  return STANDARD_SIZES.find(([w, h]) => maxX <= w && maxY <= h) ?? [maxX, maxY];
}

/**
 * Build a replayable scene from real preview observations. Frames are grouped
 * by timestamp and projected into the stage with "contain" scaling. The result
 * carries only geometry and labels; there are no pixels to fall back to.
 */
export function buildRealScene(observations: PreviewObservation[]): SceneSource | null {
  const groups = new Map<string, PreviewObservation[]>();
  observations.forEach((item) => {
    const list = groups.get(item.timestamp) ?? [];
    list.push(item);
    groups.set(item.timestamp, list);
  });
  const timestamps = [...groups.keys()].sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
  if (!timestamps.length) return null;

  const raw: Raw[] = timestamps.map((timestamp) => {
    const items = groups.get(timestamp)!;
    const keypoints = items.map(skeletonOf).find(Boolean) ?? {};
    const bboxes = items.flatMap((item) => {
      const box = item.object?.bbox;
      if (!isBbox(box)) return [];
      const label = String(item.subject?.label ?? item.object?.label ?? "object");
      return label === "person" ? [] : [{ label, bbox: box, confidence: item.confidence }];
    });
    return { keypoints, bboxes };
  });

  const [width, height] = frameSize(raw, observations[0]?.metadata);
  const scale = Math.min(STAGE_WIDTH / width, STAGE_HEIGHT / height);
  const offsetX = (STAGE_WIDTH - width * scale) / 2;
  const offsetY = (STAGE_HEIGHT - height * scale) / 2;
  const project = (x: number, y: number): [number, number] => [offsetX + x * scale, offsetY + y * scale];

  const start = new Date(timestamps[0]).getTime();
  const times = timestamps.map((timestamp) => Math.max(0, (new Date(timestamp).getTime() - start) / 1000));
  const duration = Math.max(1, times[times.length - 1] + 1);
  const markers: SceneFact[] = observations
    .filter((item) => item.fact_type !== "object_detected" || item.object)
    .map((item) => ({ t: (new Date(item.timestamp).getTime() - start) / 1000, fact_type: item.fact_type, confidence: item.confidence, location: String(item.metadata?.zone_id ?? item.subject?.label ?? "") }));

  function sample(t: number): SceneFrame {
    let index = 0;
    while (index < times.length - 1 && times[index + 1] <= t) index += 1;
    const frame = raw[index];
    const keypoints: Keypoints = {};
    Object.entries(frame.keypoints).forEach(([name, [x, y, confidence]]) => {
      const [px, py] = project(x, y);
      keypoints[name as keyof Keypoints] = [px, py, confidence];
    });
    const hasPerson = Object.keys(keypoints).length > 0;
    const objects: SceneObject[] = frame.bboxes.map(({ label, bbox: [x, y, w, h], confidence }, objectIndex) => {
      const [cx, cy] = project(x + w / 2, y + h / 2);
      const category = categoryOf(label);
      return { id: `${label}-${objectIndex}`, label, glyph: glyphOf(label), category, medication: category === "medicine", x: cx, y: cy, w: w * scale, h: h * scale, confidence, state: "detected", lock: 1 };
    });
    const facts = markers.filter((fact) => fact.t <= t);
    return {
      t, duration, phase: hasPerson ? "action" : "idle",
      // The preview endpoint carries no registry decision yet, so every real person fails closed as unregistered.
      person: hasPerson ? { id: "track", label: "未登记人员", identified: false, render: "unregistered", keypoints, confidence: 0.8, opacity: 1, pose: "—", action: facts[facts.length - 1] ? facts[facts.length - 1].fact_type : "—", zone: "—" } : null,
      objects, facts, latestFact: facts[facts.length - 1] ?? null,
      skeletonReveal: 1, cartoonReveal: 1, steps: [], eventReady: false, alertReady: false,
    };
  }

  return { kind: "real", duration, sample, markers };
}
