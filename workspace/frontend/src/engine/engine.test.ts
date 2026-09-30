import { test } from "node:test";
import assert from "node:assert/strict";
import { DEMO_ACTS, MOCK_DURATION, sampleMockScene } from "./scene/mockScript.ts";
import { buildRealScene, skeletonOf } from "./scene/realScene.ts";
import { explainEvent, type ExplainableEvent } from "./explain.ts";
import { buildMemory } from "./memory.ts";
import { categoryOf, relativeTime } from "./labels.ts";
import { applyPluginWatch, isPluginRunning, watchedCategories } from "./pluginCore.ts";
import { layoutFromConfig } from "./scene/layout.ts";
import { buildPhotoScene, isPhotoSceneConfig } from "./scene/photoScene.ts";
import { buildTimeline, filterTimeline, groupTimeline } from "./timeline.ts";

test("mock script: empty room first, then a full 17-joint skeleton", () => {
  assert.equal(sampleMockScene(0).person, null);
  const frame = sampleMockScene(10);
  assert.ok(frame.person);
  assert.equal(Object.keys(frame.person.keypoints).length, 17);
  assert.equal(frame.skeletonReveal, 1);
});

test("mock script: acts cover the whole duration without gaps", () => {
  assert.equal(DEMO_ACTS[0].start, 0);
  assert.equal(DEMO_ACTS.at(-1)!.end, MOCK_DURATION);
  DEMO_ACTS.slice(1).forEach((act, index) => assert.equal(act.start, DEMO_ACTS[index].end));
});

test("mock script: pill box is held during hand-to-face and returned afterwards", () => {
  const holding = sampleMockScene(16.5);
  const box = holding.objects.find((item) => item.id === "obj-01")!;
  assert.equal(box.state, "held");
  const wrist = holding.person!.keypoints.right_wrist!;
  assert.ok(Math.hypot(box.x - wrist[0], box.y - wrist[1]) < 20);
  assert.equal(sampleMockScene(20).objects.find((item) => item.id === "obj-01")!.state, "detected");
});

test("mock script: medication steps complete in order and the event follows the chain", () => {
  const early = sampleMockScene(13);
  assert.deepEqual(early.steps.map((step) => step.done), [true, true, false, false, false]);
  const late = sampleMockScene(21);
  assert.ok(late.steps.every((step) => step.done));
  assert.ok(late.eventReady);
  assert.equal(sampleMockScene(99).t, MOCK_DURATION);
});

const medicationEvent: ExplainableEvent = {
  event_id: "e1", plugin_id: "elderly_care", event_type: "suspected_medication", title: "疑似发生服药相关行为", confidence: 0.78,
  started_at: "2026-01-01T08:00:00Z", ended_at: "2026-01-01T08:00:20Z", location: "茶几",
  subject: { label: "爷爷" }, object: { label: "降压药盒" },
  facts: [{ fact_type: "object_picked", confidence: 0.5 }],
  metadata: {
    sequence_complete: true,
    reasoning_chain: [
      { fact_type: "person_entered_zone", confidence: 0.94, location: "客厅" },
      { fact_type: "object_detected", confidence: 0.95 },
      { fact_type: "hand_near_object", confidence: 0.89 },
      { fact_type: "object_picked", confidence: 0.91 },
      { fact_type: "hand_to_face", confidence: 0.74 },
    ],
  },
};

test("explain: medication event maps to the five stages and stays a suspicion", () => {
  const result = explainEvent(medicationEvent);
  assert.deepEqual(result.stages.map((stage) => stage.key), ["person", "object", "interaction", "action", "verdict"]);
  assert.ok(result.stages.every((stage) => stage.status === "passed"));
  assert.equal(result.stages[2].confidence, 0.91);
  assert.match(result.verdict.headline, /疑似/);
  assert.match(result.verdict.disclaimer, /不是医学诊断/);
});

test("explain: incomplete sequence marks the missing action stage", () => {
  const result = explainEvent({ ...medicationEvent, metadata: { sequence_complete: false }, facts: [{ fact_type: "object_detected", confidence: 0.8 }, { fact_type: "object_picked", confidence: 0.7 }] });
  assert.equal(result.stages.find((stage) => stage.key === "action")!.status, "missing");
  assert.equal(result.stages.find((stage) => stage.key === "person")!.status, "missing");
  assert.match(result.verdict.headline, /不完整/);
});

test("explain: non-medication events only show observed stages", () => {
  const result = explainEvent({ ...medicationEvent, plugin_id: "workshop", event_type: "object_removed", title: "电钻离开工具架 A", metadata: {}, facts: [{ fact_type: "object_removed", confidence: 0.88 }] });
  assert.deepEqual(result.stages.map((stage) => stage.key), ["interaction", "verdict"]);
  assert.equal(result.verdict.headline, "电钻离开工具架 A");
});

test("memory: links events by id or label and keeps the newest location", () => {
  const objects = [{ object_id: "obj-1", name: "电钻", description: "工具架", reference_uris: [], status: "active" }, { object_id: "obj-2", name: "水杯", description: "", reference_uris: [], status: "active" }];
  const base = { plugin_id: "workshop", review_status: "confirmed", title: "t" };
  const [drill, cup] = buildMemory(objects, [
    { ...base, event_id: "a", started_at: "2026-01-01T08:00:00Z", ended_at: "2026-01-01T08:00:00Z", location: "工具架 A", object: { id: "obj-1" } },
    { ...base, event_id: "b", started_at: "2026-01-01T09:00:00Z", ended_at: "2026-01-01T09:00:00Z", location: "工作台", object: { label: "电钻" } },
  ]);
  assert.equal(drill.appearances.length, 2);
  assert.equal(drill.lastLocation, "工作台");
  assert.equal(drill.category, "tool");
  assert.equal(cup.lastSeen, null);
  assert.equal(cup.glyph, "cup");
});

test("real scene: reads canonical skeleton, drops malformed joints, projects into the stage", () => {
  const observation = { source_id: "s", timestamp: "2026-01-01T08:00:00Z", fact_type: "person_detected", confidence: 0.9, metadata: { skeleton: { keypoints: { nose: [320, 100, 0.9], left_wrist: [300, "x", 0.5], right_ankle: [330, 460, 0.8] } } } };
  assert.deepEqual(Object.keys(skeletonOf(observation)!), ["nose", "right_ankle"]);
  const scene = buildRealScene([observation])!;
  const nose = scene.sample(0).person!.keypoints.nose!;
  assert.ok(nose[0] > 0 && nose[0] < 1600 && nose[1] > 0 && nose[1] < 1000);
  assert.equal(buildRealScene([]), null);
});

test("plugins: only running plugins mark their object categories; skeleton is always kept", () => {
  const declarations = [{ plugin_id: "elderly_care", watches: ["medicine" as const] }, { plugin_id: "workshop", watches: ["tool" as const, "daily" as const] }];
  const frame = sampleMockScene(12);
  const both = watchedCategories([{ plugin_id: "elderly_care", enabled: true, state: "running" }, { plugin_id: "workshop", enabled: true, state: "running" }], declarations);
  assert.equal(applyPluginWatch(frame, both)!.objects.filter((object) => object.state !== "hidden").length, 3);

  const medicationOnly = watchedCategories([{ plugin_id: "elderly_care", enabled: true, state: "running" }, { plugin_id: "workshop", enabled: false, state: "disabled" }], declarations);
  const filtered = applyPluginWatch(frame, medicationOnly)!;
  assert.deepEqual(filtered.objects.filter((object) => object.state !== "hidden").map((object) => object.label), ["降压药盒"]);
  assert.equal(Object.keys(filtered.person!.keypoints).length, 17);

  assert.equal(isPluginRunning({ plugin_id: "x", enabled: true, state: "error" }), false);
  assert.equal(watchedCategories([], declarations).size, 0);
});

test("layout: a photo config puts the feet on its floor and the reaching hand on its pill box", () => {
  const layout = layoutFromConfig({ image: "room.jpg", width: 1920, height: 1080, floorY: 1000, objects: { "obj-01": [700, 640, 90, 50], "obj-04": [820, 620, 50, 70] } });
  const reach = sampleMockScene(13.2, layout);
  const pill = layout.objects["obj-01"];
  const wrist = reach.person!.keypoints.right_wrist!;
  assert.ok(Math.hypot(wrist[0] - pill.x, wrist[1] - pill.y) < pill.h, "hand reaches the pill box");
  const ankle = sampleMockScene(10, layout).person!.keypoints.left_ankle!;
  const floorOnStage = (1000 * (1000 / 1080)) + (1000 - 1080 * (1000 / 1080)) / 2;
  assert.ok(Math.abs(ankle[1] - floorOnStage) < 8, "feet stand on the photo floor");
  assert.equal(reach.objects.length, 2, "only objects present in the photo are tracked");
});

test("photo scene: real keypoints are projected with the same cover crop as the photo", () => {
  const config = { image: "office.jpg", width: 1280, height: 960, room: "实验室", persons: [{ id: "person-1", confidence: 0.64, bbox: [171, 543, 97, 172] as [number, number, number, number], keypoints: { nose: [239.5, 574.6, 0.79] as [number, number, number], left_hip: [193.5, 674.7, 0.8] as [number, number, number] } }] };
  assert.ok(isPhotoSceneConfig(config));
  const frame = buildPhotoScene(config).sample(6);
  const nose = frame.person!.keypoints.nose!;
  // 1280×960 covers 1600×1000 at scale 1.25 with a 100 px vertical crop.
  assert.ok(Math.abs(nose[0] - 239.5 * 1.25) < 0.01 && Math.abs(nose[1] - (574.6 * 1.25 - 100)) < 0.01);
  assert.equal(frame.cartoonReveal, 1);
  assert.equal(buildPhotoScene(config).sample(0.2).skeletonReveal, 0);
  assert.equal(isPhotoSceneConfig({ image: "x.jpg", width: 10, height: 10, floorY: 5, objects: {} }), false);
});

test("render policy: photo persons follow the AI decision and fail closed without one", () => {
  const base = { image: "o.jpg", width: 1280, height: 960, persons: [] as Array<Record<string, unknown>> };
  const kp = { nose: [10, 10, 0.9] as [number, number, number] };
  const scene = buildPhotoScene({ ...base, persons: [
    { id: "p1", confidence: 0.9, bbox: [0, 0, 1, 1], keypoints: kp, render: { mode: "avatar", display_name: "爷爷", similarity: 0.95, alert: false } },
    { id: "p2", confidence: 0.9, bbox: [0, 0, 1, 1], keypoints: kp },
  ] } as never);
  assert.equal(scene.sample(0.5).person!.render, "pending");
  const locked = scene.sample(5).person!;
  assert.equal(locked.render, "avatar");
  assert.equal(locked.label, "爷爷");
  const stranger = buildPhotoScene({ ...base, persons: [{ id: "p2", confidence: 0.9, bbox: [0, 0, 1, 1], keypoints: kp }] } as never);
  assert.equal(stranger.sample(5).person!.render, "unregistered");
  assert.ok(stranger.markers.some((fact) => fact.fact_type === "unregistered_person"));
  assert.equal(sampleMockScene(10).person!.render, "avatar");
});

test("memory: same-name objects stay separate candidates; name-only evidence never sets their location", () => {
  const cups = [
    { object_id: "cup-a", name: "水杯", description: "茶几", reference_uris: [], status: "active" },
    { object_id: "cup-b", name: "水杯", description: "餐边柜", reference_uris: [], status: "active" },
  ];
  const base = { plugin_id: "workshop", review_status: "pending", title: "t" };
  const [a, b] = buildMemory(cups, [
    { ...base, event_id: "named", started_at: "2026-01-01T08:00:00Z", ended_at: "2026-01-01T08:00:00Z", location: "餐边柜", object: { label: "水杯" } },
    { ...base, event_id: "exact", started_at: "2026-01-01T07:00:00Z", ended_at: "2026-01-01T07:00:00Z", location: "茶几", object: { id: "cup-a" } },
  ]);
  assert.deepEqual(a.sameLabel, ["cup-b"]);
  assert.equal(a.status, "known");
  assert.equal(a.lastLocation, "茶几", "only the id-matched event sets the location");
  assert.equal(a.appearances.find((item) => item.event_id === "named")!.ambiguous, true);
  assert.equal(b.status, "ambiguous");
  assert.equal(b.lastLocation, null);
  assert.ok(!b.appearances.some((item) => item.event_id === "exact"), "an event for cup-a is not attributed to cup-b");
});

test("timeline: newest first, skips detections, groups by source and continuity segment", () => {
  const entries = buildTimeline([
    { event_id: "e1", title: "a", source_id: "cam-1", started_at: "2026-01-01T08:00:00Z", ended_at: "2026-01-01T08:00:10Z", facts: [
      { fact_type: "object_detected", confidence: 0.9 },
      { fact_type: "hand_near_object", confidence: 0.8, timestamp: "2026-01-01T08:00:02Z", object: { label: "药盒" }, metadata: { continuity_segment: 0 } },
      { fact_type: "hand_to_face", confidence: 0.7, timestamp: "2026-01-01T08:00:09Z", metadata: { continuity_segment: 1 } },
    ] },
    { event_id: "e2", title: "b", source_id: "cam-2", started_at: "2026-01-01T09:00:00Z", ended_at: "2026-01-01T09:00:00Z", subject: { label: "爷爷" }, facts: [{ fact_type: "left_zone", confidence: 0.6 }] },
  ]);
  assert.deepEqual(entries.map((entry) => entry.fact_type), ["left_zone", "hand_to_face", "hand_near_object"]);
  assert.equal(entries[0].exactTime, false);
  assert.equal(entries[0].subject, "爷爷");
  assert.equal(groupTimeline(entries).length, 3, "cam-2, cam-1#1 and cam-1#0 are separate sequences");
  assert.deepEqual(filterTimeline(entries, { object: "药盒" }).map((entry) => entry.fact_type), ["hand_near_object"]);
  assert.equal(filterTimeline(entries, { factTypes: new Set(["left_zone", "hand_to_face"]) }).length, 2);
});

test("labels: category and relative time", () => {
  assert.equal(categoryOf("降压药盒"), "medicine");
  assert.equal(categoryOf("钥匙"), "daily");
  assert.equal(relativeTime(new Date(Date.now() - 5 * 60000).toISOString()), "5 分钟前");
});
