/** Presentation vocabulary shared by every page. Pure data, no React. */

export const FACT_LABELS: Record<string, string> = {
  person_entered_zone: "人物进入监控区",
  person_detected: "检测到人物",
  person_present: "人物持续在场",
  entered_zone: "进入区域",
  left_zone: "离开区域",
  motion: "检测到移动",
  object_detected: "识别到物品",
  object_in_zone: "物品位于区域",
  hand_near_object: "手靠近物品",
  pickup_candidate: "拿取候选",
  object_picked: "拿起物品",
  hand_to_face: "手靠近面部",
  putdown_candidate: "放回候选",
  object_put_down: "放下物品",
  object_removed: "物品离开区域",
  object_returned: "物品回到区域",
  unregistered_person: "出现未登记人员",
};

export function factLabel(factType: string): string {
  return FACT_LABELS[factType] ?? factType.replaceAll("_", " ");
}

export type ReviewState = "pending" | "confirmed" | "rejected";

export function reviewLabel(status: string): string {
  return status === "pending" ? "待复核" : status === "confirmed" ? "已确认" : status === "rejected" ? "已驳回" : status;
}

export function severityLabel(severity: string): string {
  return severity === "high" ? "高" : severity === "medium" ? "中" : severity === "low" ? "低" : "提示";
}

/** The five medication-plan review cues from the frozen contract. None of them is proof of intake. */
export const PLAN_CUE_LABELS: Record<string, string> = {
  plan_match_candidate: "与计划时间匹配（候选）",
  early_candidate: "早于计划时间（候选）",
  late_candidate: "晚于计划时间（候选）",
  wrong_item_candidate: "疑似拿错药品（候选）",
  unresolved_candidate: "无法对应计划（待复核）",
};

export function planCueLabel(cue: unknown): string | null {
  return typeof cue === "string" ? PLAN_CUE_LABELS[cue] ?? cue : null;
}

export type ObjectCategory = "medicine" | "tool" | "daily";
export type GlyphKind = "pillbox" | "bottle" | "cup" | "glasses" | "keys" | "drill" | "screwdriver" | "generic";

export const CATEGORY_LABELS: Record<ObjectCategory, string> = { medicine: "药品", tool: "工具", daily: "生活用品" };

export function categoryOf(text: string): ObjectCategory {
  const value = text.toLowerCase();
  if (/药|维生素|medicine|pill|drug|vitamin/.test(value)) return "medicine";
  if (/工具|电钻|螺丝|扳手|锤|tool|drill|screw|wrench/.test(value)) return "tool";
  return "daily";
}

export function glyphOf(text: string): GlyphKind {
  const value = text.toLowerCase();
  if (/杯|cup|mug/.test(value)) return "cup";
  if (/瓶|bottle|vitamin|维生素/.test(value)) return "bottle";
  if (/药|pill|medicine/.test(value)) return "pillbox";
  if (/镜|glasses/.test(value)) return "glasses";
  if (/钥匙|key/.test(value)) return "keys";
  if (/电钻|drill/.test(value)) return "drill";
  if (/螺丝|screw/.test(value)) return "screwdriver";
  return "generic";
}

export function percent(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
}

export function clockTime(value: string | number | Date): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

export function shortTime(value: string | number | Date): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", hour12: false });
}

export function relativeTime(value: string | null | undefined, now = Date.now()): string {
  if (!value) return "—";
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return "—";
  const minutes = Math.round(Math.max(0, now - time) / 60000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  const hours = Math.round(minutes / 60);
  return hours < 24 ? `${hours} 小时前` : `${Math.round(hours / 24)} 天前`;
}
