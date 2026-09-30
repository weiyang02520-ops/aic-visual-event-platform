import { useEffect, useState } from "react";
import { createInsightsApi } from "../api/insights";
import { AI_API_URL } from "../app/runtime";
import { buildRealScene, type PreviewObservation } from "../engine/scene/realScene";
import type { SceneSource } from "../engine/scene/types";
import type { Mode, RepositoryConnection } from "../types";

export type RealSceneStatus = "inactive" | "unconfigured" | "offline" | "loading" | "ready" | "empty" | "error";

/**
 * Real privacy stage: geometry from `/api/v1/vision/preview` only. Every
 * failure keeps the stage closed with an explicit reason; there is no raw
 * video or Mock fallback.
 */
export function useRealScene(mode: Mode, connection: RepositoryConnection): { source: SceneSource | null; status: RealSceneStatus; reason: string } {
  const previewSource = import.meta.env.VITE_AI_PREVIEW_SOURCE;
  const [state, setState] = useState<{ source: SceneSource | null; status: RealSceneStatus; reason: string }>({ source: null, status: "inactive", reason: "" });

  useEffect(() => {
    if (mode !== "real") { setState({ source: null, status: "inactive", reason: "" }); return; }
    if (connection.status === "offline") { setState({ source: null, status: "offline", reason: connection.reason ?? "AI 服务离线" }); return; }
    if (connection.status !== "online") { setState({ source: null, status: "loading", reason: "正在连接 AI 服务" }); return; }
    if (!previewSource) { setState({ source: null, status: "unconfigured", reason: "未配置 VITE_AI_PREVIEW_SOURCE，隐私渲染流未接入" }); return; }

    let active = true;
    const api = createInsightsApi(AI_API_URL, 20000);
    const load = () => {
      api.visionPreview(previewSource, 32)
        .then((observations) => {
          if (!active) return;
          const source = buildRealScene(observations as PreviewObservation[]);
          setState(source ? { source, status: "ready", reason: "" } : { source: null, status: "empty", reason: "预览没有返回骨骼或物品几何" });
        })
        .catch((error: unknown) => {
          if (active) setState({ source: null, status: "error", reason: error instanceof Error ? error.message : "预览请求失败" });
        });
    };
    setState({ source: null, status: "loading", reason: "正在读取视觉预览" });
    load();
    const timer = window.setInterval(load, 30000);
    return () => { active = false; window.clearInterval(timer); };
  }, [mode, connection.status, connection.reason, previewSource]);

  return state;
}
