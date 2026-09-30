import { POSES, blendPose, clamp01, easeInOut, placePose, type LocalPose, type PoseName } from "./poses.ts";
import type { MedicationStep, SceneFact, SceneFrame, SceneObject, ScenePhase, SceneSource } from "./types.ts";
import { DEFAULT_LAYOUT, type SceneLayout } from "./layout.ts";

/**
 * Deterministic 26-second medication-assist script used by the Mock data source
 * and the competition Demo. It is a rehearsed fixture, not model output, and
 * every page that renders it labels it as demo data.
 */
export const MOCK_DURATION = 26;

export interface DemoAct {
  key: ScenePhase;
  index: number;
  title: string;
  caption: string;
  start: number;
  end: number;
}

export const DEMO_ACTS: DemoAct[] = [
  { key: "person", index: 1, title: "人物出现", caption: "早上八点，爷爷走进客厅。", start: 0, end: 4.5 },
  { key: "recognize", index: 2, title: "AI 识别", caption: "通过身体关键点认出爷爷，并换成卡通形象显示，真实画面不会出现在界面上。", start: 4.5, end: 8 },
  { key: "object", index: 3, title: "物品发现", caption: "看到茶几上的降压药盒和水杯，还有沙发扶手上的老花镜。", start: 8, end: 11.5 },
  { key: "action", index: 4, title: "动作分析", caption: "伸手、拿起药盒、手靠近嘴边、放回，每个动作都被记下来。", start: 11.5, end: 19 },
  { key: "event", index: 5, title: "事件生成", caption: "把这些动作连起来，得出“疑似完成服药”的判断。", start: 19, end: 22.5 },
  { key: "alert", index: 6, title: "智能提醒", caption: "通知家属确认。机器人只做提醒，不替人下结论。", start: 22.5, end: 26 },
];

export { DEFAULT_LAYOUT } from "./layout.ts";

const FACTS: SceneFact[] = [
  { t: 4.6, fact_type: "person_entered_zone", confidence: 0.94, location: "客厅" },
  { t: 8.9, fact_type: "object_detected", confidence: 0.95, location: "客厅茶几" },
  { t: 12.8, fact_type: "hand_near_object", confidence: 0.89, location: "药箱区域" },
  { t: 14.1, fact_type: "object_picked", confidence: 0.91, location: "药箱区域" },
  { t: 16.2, fact_type: "hand_to_face", confidence: 0.74, location: "客厅茶几" },
  { t: 18.6, fact_type: "object_put_down", confidence: 0.86, location: "客厅茶几" },
];

const POSE_KEYS: Array<[number, PoseName]> = [
  [4.5, "stand"], [11.5, "stand"], [12.8, "reach"], [13.6, "reach"], [14.6, "hold"],
  [15.0, "hold"], [16.2, "handToFace"], [17.6, "handToFace"], [18.6, "reach"], [19.2, "stand"],
];

const BASE_OBJECTS: Array<Omit<SceneObject, "state" | "lock" | "x" | "y" | "w" | "h"> & { lockAt: number }> = [
  { id: "obj-01", label: "降压药盒", glyph: "pillbox", category: "medicine", medication: true, confidence: 0.95, lockAt: 8.3 },
  { id: "obj-04", label: "水杯", glyph: "cup", category: "daily", medication: false, confidence: 0.9, lockAt: 9.0 },
  { id: "obj-06", label: "老花镜", glyph: "glasses", category: "daily", medication: false, confidence: 0.82, lockAt: 9.7 },
];

function poseAt(t: number, layout: SceneLayout): { pose: LocalPose; rootX: number; rootY: number } {
  const { enterX, stopX, rootY } = layout;
  if (t < 4.5) {
    const walk = clamp01((t - 1) / 3.5);
    const rootX = enterX + (stopX - enterX) * easeInOut(walk);
    const cycle = (t - 1) / 0.45;
    const swing = (Math.sin(Math.PI * cycle) + 1) / 2;
    const settle = clamp01((t - 4.1) / 0.4);
    const pose = blendPose(blendPose(POSES.walkA, POSES.walkB, swing), POSES.stand, settle);
    return { pose, rootX, rootY: rootY - Math.abs(Math.sin(Math.PI * cycle)) * 6 * (1 - settle) };
  }
  for (let index = 0; index < POSE_KEYS.length - 1; index += 1) {
    const [start, from] = POSE_KEYS[index];
    const [end, to] = POSE_KEYS[index + 1];
    if (t >= start && t < end) return { pose: blendPose(POSES[from], POSES[to], easeInOut((t - start) / (end - start))), rootX: stopX, rootY };
  }
  return { pose: POSES.stand, rootX: stopX, rootY };
}

function phaseAt(t: number): ScenePhase {
  if (t < 1) return "idle";
  return DEMO_ACTS.find((act) => t >= act.start && t < act.end)?.key ?? "alert";
}

function actionAt(t: number): { action: string; pose: string } {
  if (t < 4.5) return { action: "进入客厅", pose: "行走" };
  if (t < 11.5) return { action: "站立 · 停留", pose: "站立" };
  if (t < 13.6) return { action: "伸手靠近药盒", pose: "前倾" };
  if (t < 15.8) return { action: "拿起药盒", pose: "站立" };
  if (t < 17.6) return { action: "手靠近面部", pose: "站立" };
  if (t < 19.2) return { action: "放回药盒", pose: "前倾" };
  return { action: "站立 · 停留", pose: "站立" };
}

function steps(t: number): MedicationStep[] {
  const fact = (type: string) => FACTS.find((item) => item.fact_type === type)!;
  return [
    { key: "person", label: "发现人物", done: t >= fact("person_entered_zone").t, confidence: 0.94 },
    { key: "object", label: "检测药盒", done: t >= fact("object_detected").t, confidence: 0.95 },
    { key: "pickup", label: "检测拿取", done: t >= fact("object_picked").t, confidence: 0.91 },
    { key: "action", label: "检测动作", done: t >= fact("hand_to_face").t, confidence: 0.74 },
    { key: "verdict", label: "生成判断", done: t >= 19.2, confidence: 0.78 },
  ].map((step) => ({ ...step, confidence: step.done ? step.confidence : null }));
}

export function sampleMockScene(rawT: number, layout: SceneLayout = DEFAULT_LAYOUT): SceneFrame {
  const t = Math.min(MOCK_DURATION, Math.max(0, rawT));
  const { pose, rootX, rootY } = poseAt(t, layout);
  const keypoints = placePose(pose, rootX, rootY, layout.scale);
  const visible = t >= 1;
  const { action, pose: poseLabel } = actionAt(t);
  const wrist = keypoints.right_wrist!;
  const held = t >= 14.1 && t < 18.6;

  const objects: SceneObject[] = BASE_OBJECTS.filter((object) => layout.objects[object.id]).map(({ lockAt, ...object }) => {
    const box = layout.objects[object.id];
    const lock = clamp01((t - lockAt) / 0.7);
    if (object.id === "obj-01" && held) return { ...object, ...box, x: wrist[0] - 6, y: wrist[1] + 8, state: "held", lock: 1 };
    return { ...object, ...box, state: lock > 0 ? "detected" : "hidden", lock };
  });

  const facts = FACTS.filter((fact) => fact.t <= t);
  return {
    t,
    duration: MOCK_DURATION,
    phase: phaseAt(t),
    person: visible ? {
      id: "person_01",
      label: t >= 6.8 ? "爷爷" : "Person 01",
      identified: t >= 6.8,
      // The rehearsed resident is a registered household member.
      render: t >= 6.8 ? "avatar" : "pending",
      keypoints,
      confidence: t >= 6.2 ? 0.92 : 0.8,
      opacity: clamp01((t - 1) / 0.8),
      pose: poseLabel,
      action,
      zone: t < 4 ? "客厅入口" : "客厅 · 茶几旁",
    } : null,
    objects,
    facts,
    latestFact: facts[facts.length - 1] ?? null,
    skeletonReveal: clamp01((t - 4.6) / 1.6),
    cartoonReveal: clamp01((t - 6.4) / 1.2),
    steps: steps(t),
    eventReady: t >= 19.2,
    alertReady: t >= 22.8,
  };
}

export function createMockSceneSource(layout: SceneLayout = DEFAULT_LAYOUT): SceneSource {
  return { kind: "mock", duration: MOCK_DURATION, sample: (t) => sampleMockScene(t, layout), markers: FACTS };
}
