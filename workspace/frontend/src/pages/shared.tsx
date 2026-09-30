import { useMemo } from "react";
import { explainEvent, type EventExplanation } from "../engine/explain";
import { resolvePlugin } from "../plugins";
import { isPluginRunning } from "../engine/pluginCore";
import type { Runtime } from "../app/runtime";
import type { Tone } from "../design/ui";
import type { Plugin, UnifiedEvent } from "../types";

export function useExplanations(events: UnifiedEvent[]): Map<string, EventExplanation> {
  return useMemo(() => new Map(events.map((event) => [event.event_id, explainEvent(event)])), [events]);
}

export function pluginLabel(plugins: Plugin[], pluginId: string): string {
  const plugin = plugins.find((item) => item.plugin_id === pluginId);
  return plugin ? resolvePlugin(plugin).def.label : pluginId;
}

export const isRunning = isPluginRunning;

export interface SystemRow { id: string; label: string; detail: string; tone: Tone; value: string }

/**
 * System status rows. Mock rows say they are demo fixtures; Real rows only
 * repeat what `/health`, `/ready` and the detector provider list reported.
 */
export function systemRows(runtime: Pick<Runtime, "mode" | "connection" | "health" | "readiness" | "detectors" | "plugins">): SystemRow[] {
  const { mode, connection, health, readiness, detectors, plugins } = runtime;
  const running = plugins.filter(isRunning).length;
  const pluginRow: SystemRow = { id: "plugins", label: "插件运行时", value: `${running}/${plugins.length}`, detail: plugins.length ? `${running} 个插件运行中` : "没有已注册插件", tone: running ? "ok" : "warn" };

  if (mode === "mock") {
    return [
      { id: "camera", label: "摄像头", value: "演示", detail: "演示画面，不是真实摄像头", tone: "accent" },
      { id: "pose", label: "人体识别", value: "演示", detail: "演示用身体关键点", tone: "accent" },
      { id: "object", label: "物品识别", value: "演示", detail: "演示用物品数据", tone: "accent" },
      pluginRow,
      { id: "backend", label: "AI 服务", value: "演示", detail: "本地演示数据", tone: connection.status === "offline" ? "risk" : "ok" },
    ];
  }

  if (connection.status !== "online") {
    const tone: Tone = connection.status === "offline" ? "risk" : "warn";
    const detail = connection.status === "offline" ? connection.reason ?? "无法连接" : "连接中";
    return ["视觉源", "姿态模型", "物品识别", "插件运行时", "AI 服务"].map((label, index) => ({ id: `r${index}`, label, value: "—", detail, tone }));
  }

  const selected = detectors?.find((item) => item.selected) ?? null;
  const previewSource = import.meta.env.VITE_AI_PREVIEW_SOURCE;
  return [
    { id: "camera", label: "视觉源", value: previewSource ? "已配置" : "未接入", detail: previewSource ?? "未配置 VITE_AI_PREVIEW_SOURCE", tone: previewSource ? "ok" : "warn" },
    { id: "pose", label: "姿态模型", value: selected ? (selected.pose_available ?? selected.available ? "可用" : "不可用") : "—", detail: selected ? `${selected.provider_id} ${selected.version}${selected.reason ? ` · ${selected.reason}` : ""}` : detectors ? "没有选中的检测器" : "检测器状态未返回", tone: selected ? (selected.pose_available ?? selected.available ? "ok" : "risk") : "warn" },
    { id: "object", label: "物品识别", value: selected?.object_available == null ? "—" : selected.object_available ? "可用" : "不可用", detail: selected?.object_reason ?? (selected?.object_available ? selected.object_model_path ?? "语义物品模型" : "未提供语义物品模型状态"), tone: selected?.object_available ? "ok" : "warn" },
    pluginRow,
    { id: "backend", label: "AI 服务", value: readiness?.status ?? String(health.status ?? "ok"), detail: readiness ? `数据库 ${readiness.database ?? "—"} · 检测器 ${readiness.detector ?? "—"} · 跟踪 ${readiness.tracker ?? "—"}` : `${String(health.service ?? "visual-event-ai")} ${String(health.version ?? "")}`, tone: readiness?.status === "degraded" ? "warn" : "ok" },
  ];
}

export function isToday(value: string): boolean {
  const date = new Date(value);
  const now = new Date();
  return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate();
}
