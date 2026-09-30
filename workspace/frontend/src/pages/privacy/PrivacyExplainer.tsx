import { AlertCircle, CheckCircle, Info, Shield, ShieldAlert } from "lucide-react";
import { Panel, Pill } from "../../design/ui";
import "./privacy.css";

export type PrivacyMode = "skeleton-only" | "rgb-local";

export interface PrivacyExplainerProps {
  /** Current mode: skeleton-only (edge device outputs skeleton), or rgb-local (RGB stays local, converted to skeleton). */
  mode: PrivacyMode;
  /** True when pose model is loaded and running. */
  poseAvailable: boolean;
  /** True when object detection model is loaded. */
  objectAvailable: boolean;
}

/**
 * Explains the two privacy pipeline modes and clearly states which one is
 * active. From the frozen contract and development direction: never imply
 * skeleton-only is ready when RGB→pose happens locally.
 */
export function PrivacyExplainer({ mode, poseAvailable, objectAvailable }: PrivacyExplainerProps) {
  const target = mode === "skeleton-only";
  return (
    <Panel className="privacy-explainer" title="隐私保护说明" icon={<Shield size={18} />}>
      <div className="privacy-modes">
        <div className={`privacy-mode ${target ? "target" : "current"}`}>
          <div className="privacy-mode-head">
            <span className="privacy-icon">{target ? <Shield size={20} /> : <Info size={20} />}</span>
            <div>
              <strong>目标方案：边缘端只输出骨骼</strong>
              <Pill tone={target ? "ok" : "neutral"}>{target ? "当前模式" : "未启用"}</Pill>
            </div>
          </div>
          <p>摄像头端（机器人或边缘设备）运行姿态模型，只向服务器发送 17 个关键点坐标，原始画面不离开设备。这是产品的最终隐私方案。</p>
          {target ? (
            <div className="privacy-status ok"><CheckCircle size={16} />原始画面未传输到本系统</div>
          ) : (
            <div className="privacy-status neutral"><AlertCircle size={16} />需要硬件支持，当前环境未配置</div>
          )}
        </div>

        <div className={`privacy-mode ${!target ? "current" : ""}`}>
          <div className="privacy-mode-head">
            <span className="privacy-icon"><ShieldAlert size={20} /></span>
            <div>
              <strong>当前方案：本地 RGB → 姿态 → 骨骼</strong>
              <Pill tone={!target ? "warn" : "neutral"}>{!target ? "当前模式" : "未启用"}</Pill>
            </div>
          </div>
          <p>服务器接收 RGB 视频流，在本地运行姿态模型提取骨骼，然后丢弃原始帧。前端只接收骨骼数据。这是开发和演示阶段的过渡方案。</p>
          {!target && (
            <>
              <div className="privacy-status warn"><ShieldAlert size={16} />RGB 帧到达本服务器，但不会存储或转发</div>
              <dl className="privacy-models">
                <div><dt>姿态模型</dt><dd className={poseAvailable ? "ok" : "neutral"}>{poseAvailable ? "✓ 已加载" : "× 未加载"}</dd></div>
                <div><dt>物品检测模型</dt><dd className={objectAvailable ? "ok" : "neutral"}>{objectAvailable ? "✓ 已加载" : "× 未加载"}</dd></div>
              </dl>
            </>
          )}
        </div>
      </div>
      <p className="privacy-note faint">当前展示的骨骼和卡通形象都是从关键点重建的，不含原始画面。演示模式用的是预先抹掉人的照片，也符合这个原则。</p>
    </Panel>
  );
}
