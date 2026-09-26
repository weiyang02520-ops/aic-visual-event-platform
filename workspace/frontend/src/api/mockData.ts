import type { Plugin, RegisteredObject, RegisteredPerson, UnifiedEvent } from "../types";

export const mockPlugins: Plugin[] = [
  { plugin_id: "elderly_care", name: "智慧养老辅助判断", version: "0.1.0", description: "把药盒、人物和动作事实组合成可复核的疑似服药事件。", enabled: true, state: "running" },
  { plugin_id: "workshop", name: "工作室物品管理", version: "0.1.0", description: "追踪工具离开登记区域、归还和最后出现位置。", enabled: true, state: "running" },
];

export function createMockEvents(): UnifiedEvent[] {
  return [
    {
      event_id: "evt-demo-001", plugin_id: "elderly_care", plugin_version: "0.1.0", event_type: "suspected_medication",
      title: "疑似发生服药相关行为", description: "检测到药盒拿起与手部接近面部的连续事实，建议结合历史视频人工复核。",
      source_id: "living-room-cam-01", started_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(), ended_at: new Date(Date.now() - 1000 * 60 * 7).toISOString(),
      confidence: 0.78, severity: "medium", review_status: "pending", subject: { id: "person_01", label: "爷爷" }, object: { id: "medicine_box_01", label: "降压药盒" }, location: "客厅桌面",
      evidence: [{ source_id: "living-room-cam-01", started_at: new Date(Date.now() - 1000 * 60 * 8 - 3000).toISOString(), ended_at: new Date(Date.now() - 1000 * 60 * 7 + 3000).toISOString(), resolver: "hls-evidence-resolver", status: "designed" }],
      facts: [{ fact_type: "object_picked", confidence: 0.91, location: "药箱区域" }, { fact_type: "hand_to_face", confidence: 0.74, location: "客厅桌面" }], metadata: { interpretation: "辅助判断，不是医学诊断" },
    },
    {
      event_id: "evt-demo-002", plugin_id: "workshop", plugin_version: "0.1.0", event_type: "object_removed",
      title: "电钻离开工具架 A", description: "检测到关注物品离开登记区域，最后出现位置已记录。", source_id: "workbench-cam-02",
      started_at: new Date(Date.now() - 1000 * 60 * 34).toISOString(), ended_at: new Date(Date.now() - 1000 * 60 * 34).toISOString(), confidence: 0.88, severity: "low", review_status: "confirmed",
      subject: { id: "person_02", label: "工作人员" }, object: { id: "drill_01", label: "电钻" }, location: "工具架 A", evidence: [], facts: [{ fact_type: "object_removed", confidence: 0.88, location: "工具架 A" }], metadata: {},
    },
    {
      event_id: "evt-demo-003", plugin_id: "workshop", plugin_version: "0.1.0", event_type: "object_returned",
      title: "电钻回到工具架 A", description: "检测到关注物品重新进入登记区域，保留移出与回归两段证据。", source_id: "workbench-cam-02",
      started_at: new Date(Date.now() - 1000 * 60 * 16).toISOString(), ended_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(), confidence: 0.84, severity: "info", review_status: "confirmed",
      subject: { id: "person_02", label: "工作人员" }, object: { id: "drill_01", label: "电钻" }, location: "工具架 A",
      evidence: [{ source_id: "workbench-cam-02", started_at: new Date(Date.now() - 1000 * 60 * 17).toISOString(), ended_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(), resolver: "fixture-evidence", status: "fixture" }],
      facts: [{ fact_type: "object_removed", confidence: 0.82, location: "工作台" }, { fact_type: "entered_zone", confidence: 0.84, location: "工具架 A" }], metadata: { review_required: false },
    },
  ];
}

export const mockObjects: RegisteredObject[] = [
  { object_id: "obj-01", name: "降压药盒", description: "爷爷每日药盒", reference_uris: [], status: "active" },
  { object_id: "obj-02", name: "电钻", description: "工具架 A 关注物品", reference_uris: [], status: "active" },
];

export const mockPersons: RegisteredPerson[] = [
  { person_id: "person-01", display_name: "爷爷", role: "resident", reference_uris: [], status: "active" },
  { person_id: "person-02", display_name: "工作人员", role: "staff", reference_uris: [], status: "active" },
];
