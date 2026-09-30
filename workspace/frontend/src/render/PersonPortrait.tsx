import type { Keypoints, PersonRenderMode } from "../engine/scene/types";
import { CartoonAvatar, SkeletonLayer, keypointBounds } from "./Avatar";

/** Cropped avatar view centred on the person's keypoints. */
export function PersonPortrait({ keypoints, mode: requested = "cartoon", size = 160, cartoonOpacity = 1, render }: { keypoints: Keypoints | null; mode?: "cartoon" | "skeleton"; size?: number; cartoonOpacity?: number; render?: PersonRenderMode }) {
  // Unregistered people never get an avatar, not even in the thumbnail.
  const mode = render === "unregistered" ? "skeleton" : requested;
  const bounds = keypoints ? keypointBounds(keypoints) : null;
  if (!keypoints || !bounds) {
    return (
      <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="38" r="16" fill="none" stroke="var(--line-strong)" strokeWidth="2" strokeDasharray="4 5" />
        <path d="M22 88 Q22 60 50 60 Q78 60 78 88" fill="none" stroke="var(--line-strong)" strokeWidth="2" strokeDasharray="4 5" />
      </svg>
    );
  }
  const side = Math.max(bounds.w, bounds.h) + 140;
  const cx = bounds.x + bounds.w / 2;
  const cy = bounds.y + bounds.h / 2 - 20;
  return (
    <svg width={size} height={size} viewBox={`${cx - side / 2} ${cy - side / 2} ${side} ${side}`} role="img" aria-label="人物卡漫形象">
      {mode === "cartoon" ? <CartoonAvatar keypoints={keypoints} opacity={cartoonOpacity} /> : null}
      {(mode === "skeleton" || cartoonOpacity < 1) && <SkeletonLayer keypoints={keypoints} opacity={mode === "skeleton" ? 1 : 1 - cartoonOpacity} />}
    </svg>
  );
}
