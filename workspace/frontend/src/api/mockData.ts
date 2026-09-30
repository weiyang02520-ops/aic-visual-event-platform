import type { Plugin, RegisteredObject, RegisteredPerson, UnifiedEvent } from "../types";

export const mockPlugins: Plugin[] = [
  { plugin_id: "elderly_care", name: "智慧养老辅助判断", version: "0.1.0", description: "把药盒、人物和动作事实组合成可复核的疑似服药事件。", enabled: true, state: "running" },
  { plugin_id: "workshop", name: "工作室物品管理", version: "0.1.0", description: "追踪工具离开登记区域、归还和最后出现位置。", enabled: true, state: "running" },
];

const minutesAgo = (minutes: number, seconds = 0) => new Date(Date.now() - minutes * 60_000 - seconds * 1000).toISOString();

export function createMockEvents(): UnifiedEvent[] {
  const medicationChain = [
    { fact_type: "person_entered_zone", confidence: 0.94, location: "客厅" },
    { fact_type: "object_detected", confidence: 0.95, location: "客厅茶几" },
    { fact_type: "hand_near_object", confidence: 0.89, location: "药箱区域" },
    { fact_type: "object_picked", confidence: 0.91, location: "药箱区域" },
    { fact_type: "hand_to_face", confidence: 0.74, location: "客厅茶几" },
  ];
  return [
    {
      event_id: "evt-demo-001", plugin_id: "elderly_care", plugin_version: "0.1.0", event_type: "suspected_medication",
      title: "疑似发生服药相关行为", description: "同一人物与药品对象出现拿取/接近后手部接近面部的时序事实；仅作为辅助判断，需人工复核。",
      source_id: "living-room-cam-01", started_at: minutesAgo(8), ended_at: minutesAgo(7, 30),
      confidence: 0.78, severity: "medium", review_status: "pending",
      subject: { id: "person_01", label: "爷爷", identity_status: "identified", privacy_mode: "cartoon", pose: "standing", action: "hand_to_face", confidence: 0.92 },
      object: { id: "obj-01", label: "降压药盒", category: "medicine", bbox: [320, 248, 86, 62], state: "tracked", confidence: 0.95 },
      location: "客厅茶几",
      evidence: [{ source_id: "living-room-cam-01", started_at: minutesAgo(8, 3), ended_at: minutesAgo(7, 27), resolver: "hls-evidence-resolver", status: "designed" }],
      facts: medicationChain,
      metadata: { interpretation: "辅助判断，不是医学诊断", needs_review: true, sequence_complete: true, plan_cue: "plan_match_candidate", plan_entry: "早间 · 降压药", reasoning_chain: medicationChain },
    },
    {
      event_id: "evt-demo-004", plugin_id: "elderly_care", plugin_version: "0.1.0", event_type: "incomplete_medication_sequence",
      title: "服药相关序列不完整", description: "检测到同一人物与药品对象的拿取线索，但缺少匹配的后续手部接近面部事实；仅作为待复核线索。",
      source_id: "living-room-cam-01", started_at: minutesAgo(26), ended_at: minutesAgo(25, 40),
      confidence: 0.61, severity: "low", review_status: "pending",
      subject: { id: "person_01", label: "爷爷", identity_status: "identified", privacy_mode: "cartoon", pose: "standing", action: "object_picked" },
      object: { id: "obj-03", label: "维生素瓶", category: "medicine", state: "tracked", confidence: 0.83 },
      location: "餐边柜",
      evidence: [{ source_id: "living-room-cam-01", started_at: minutesAgo(26, 3), ended_at: minutesAgo(25, 37), resolver: "hls-evidence-resolver", status: "designed" }],
      facts: [
        { fact_type: "person_entered_zone", confidence: 0.9, location: "餐厅" },
        { fact_type: "object_detected", confidence: 0.83, location: "餐边柜" },
        { fact_type: "object_picked", confidence: 0.72, location: "餐边柜" },
      ],
      metadata: { interpretation: "辅助判断，不是医学诊断", needs_review: true, sequence_complete: false, plan_cue: "unresolved_candidate" },
    },
    {
      event_id: "evt-demo-002", plugin_id: "workshop", plugin_version: "0.1.0", event_type: "object_removed",
      title: "电钻离开工具架 A", description: "检测到关注物品离开登记区域，最后出现位置已记录。", source_id: "workbench-cam-02",
      started_at: minutesAgo(34), ended_at: minutesAgo(34), confidence: 0.88, severity: "low", review_status: "confirmed",
      subject: { id: "person_02", label: "工作人员" }, object: { id: "obj-02", label: "电钻", category: "tool" }, location: "工具架 A", evidence: [],
      facts: [
        { fact_type: "object_in_zone", confidence: 0.9, location: "工具架 A", timestamp: minutesAgo(34, 20), metadata: { source_id: "workbench-cam-02", continuity_segment: 0 } },
        { fact_type: "hand_near_object", confidence: 0.84, location: "工具架 A", timestamp: minutesAgo(34, 10), metadata: { source_id: "workbench-cam-02", continuity_segment: 0 } },
        { fact_type: "object_removed", confidence: 0.88, location: "工具架 A", timestamp: minutesAgo(34), metadata: { source_id: "workbench-cam-02", continuity_segment: 0 } },
      ], metadata: {},
    },
    {
      event_id: "evt-demo-003", plugin_id: "workshop", plugin_version: "0.1.0", event_type: "object_returned",
      title: "电钻回到工具架 A", description: "检测到关注物品重新进入登记区域，保留移出与回归两段证据。", source_id: "workbench-cam-02",
      started_at: minutesAgo(16), ended_at: minutesAgo(15), confidence: 0.84, severity: "info", review_status: "confirmed",
      subject: { id: "person_02", label: "工作人员" }, object: { id: "obj-02", label: "电钻", category: "tool" }, location: "工具架 A",
      evidence: [{ source_id: "workbench-cam-02", started_at: minutesAgo(17), ended_at: minutesAgo(15), resolver: "fixture-evidence", status: "fixture" }],
      // Segment 1: the camera had an observation gap after the drill left, so this is a new continuity segment.
      facts: [
        { fact_type: "object_removed", confidence: 0.82, location: "工作台", timestamp: minutesAgo(16, 30), metadata: { source_id: "workbench-cam-02", continuity_segment: 1 } },
        { fact_type: "entered_zone", confidence: 0.84, location: "工具架 A", timestamp: minutesAgo(15), metadata: { source_id: "workbench-cam-02", continuity_segment: 1 } },
      ], metadata: { review_required: false },
    },
    {
      // Only a label, and two registered cups share it: memory must keep both as candidates.
      event_id: "evt-demo-006", plugin_id: "workshop", plugin_version: "0.1.0", event_type: "object_picked",
      title: "水杯被拿起", description: "检测到手靠近并拿起一只水杯；登记库里有两只同名水杯，无法确定是哪一只。", source_id: "living-room-cam-01",
      started_at: minutesAgo(41), ended_at: minutesAgo(40, 50), confidence: 0.76, severity: "info", review_status: "pending",
      subject: { id: "person_01", label: "爷爷" }, object: { label: "水杯", category: "daily" }, location: "餐边柜",
      evidence: [],
      facts: [
        { fact_type: "hand_near_object", confidence: 0.81, location: "餐边柜", timestamp: minutesAgo(41), metadata: { source_id: "living-room-cam-01", continuity_segment: 2 } },
        { fact_type: "pickup_candidate", confidence: 0.76, location: "餐边柜", timestamp: minutesAgo(40, 52), metadata: { source_id: "living-room-cam-01", continuity_segment: 2 } },
      ],
      metadata: {},
    },
    {
      event_id: "evt-demo-005", plugin_id: "workshop", plugin_version: "0.1.0", event_type: "object_removed",
      title: "螺丝刀离开工作台", description: "关注物品离开登记区域，最近已知位置为工作台右侧。", source_id: "workbench-cam-02",
      started_at: minutesAgo(52), ended_at: minutesAgo(52), confidence: 0.8, severity: "low", review_status: "pending",
      subject: { id: "person_02", label: "工作人员" }, object: { id: "obj-05", label: "螺丝刀", category: "tool" }, location: "工作台",
      evidence: [], facts: [{ fact_type: "object_in_zone", confidence: 0.86, location: "工作台" }, { fact_type: "left_zone", confidence: 0.8, location: "工作台" }], metadata: {},
    },
  ];
}

export const mockObjects: RegisteredObject[] = [
  { object_id: "obj-01", name: "降压药盒", description: "medicine · 爷爷每日早间药盒 · 客厅茶几", reference_uris: [], status: "active" },
  { object_id: "obj-03", name: "维生素瓶", description: "medicine · 餐边柜第二层", reference_uris: [], status: "active" },
  { object_id: "obj-04", name: "水杯", description: "daily · 茶几 · 饮水用", reference_uris: [], status: "active" },
  { object_id: "obj-08", name: "水杯", description: "daily · 餐边柜 · 第二只水杯", reference_uris: [], status: "active" },
  { object_id: "obj-06", name: "老花镜", description: "daily · 常放沙发扶手", reference_uris: [], status: "active" },
  { object_id: "obj-07", name: "钥匙", description: "daily · 玄关挂钩", reference_uris: [], status: "active" },
  { object_id: "obj-02", name: "电钻", description: "tool · 工具架 A 关注物品", reference_uris: [], status: "active" },
  { object_id: "obj-05", name: "螺丝刀", description: "tool · 工作台", reference_uris: [], status: "active" },
];

export const mockPersons: RegisteredPerson[] = [
  { person_id: "person-01", display_name: "爷爷", role: "resident", reference_uris: [], status: "active" },
  { person_id: "person-02", display_name: "工作人员", role: "staff", reference_uris: [], status: "active" },
];
