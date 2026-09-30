import { BONES, type Joint, type JointName, type Keypoints } from "../engine/scene/types";

const MIN_CONF = 0.3;

function joint(keypoints: Keypoints, name: JointName): Joint | null {
  const value = keypoints[name];
  return value && value[2] >= MIN_CONF ? value : null;
}

const mid = (a: Joint, b: Joint): [number, number] => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
const dist = (a: [number, number] | Joint, b: [number, number] | Joint) => Math.hypot(a[0] - b[0], a[1] - b[1]);

export interface AvatarPalette { skin: string; hair: string; top: string; topShade: string; pants: string; shoe: string }

export const GRANDPA: AvatarPalette = { skin: "#f3cba8", hair: "#e4e0db", top: "#6f8fe0", topShade: "#5a78c8", pants: "#3b4556", shoe: "#1f252f" };

/**
 * Cartoon avatar driven purely by COCO17 keypoints. Each body part is drawn
 * only when its joints are present with enough confidence, so partial
 * skeletons degrade gracefully instead of inventing limbs.
 */
export function CartoonAvatar({ keypoints, palette = GRANDPA, opacity = 1 }: { keypoints: Keypoints; palette?: AvatarPalette; opacity?: number }) {
  const ls = joint(keypoints, "left_shoulder");
  const rs = joint(keypoints, "right_shoulder");
  const lh = joint(keypoints, "left_hip");
  const rh = joint(keypoints, "right_hip");
  const shoulderW = ls && rs ? dist(ls, rs) : 0;
  const torsoLen = ls && rs && lh && rh ? dist(mid(ls, rs), mid(lh, rh)) : 0;
  // Body scale from whichever is larger: shoulder width (frontal) or half the torso (side view / sitting).
  const unit = Math.max(shoulderW, torsoLen * 0.5, 12) || 60;
  const frontal = shoulderW > torsoLen * 0.38;

  const limb = (a: JointName, b: JointName, width: number, color: string, key: string) => {
    const p = joint(keypoints, a);
    const q = joint(keypoints, b);
    return p && q ? <line key={key} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke={color} strokeWidth={width} strokeLinecap="round" /> : null;
  };

  // Head: centred between ears when available, otherwise above the nose / shoulders.
  const nose = joint(keypoints, "nose");
  const le = joint(keypoints, "left_ear");
  const re = joint(keypoints, "right_ear");
  const ear = le ?? re;
  let head: [number, number] | null = null;
  let span = 0;
  if (le && re) { head = [(le[0] + re[0]) / 2, (le[1] + re[1]) / 2 - unit * 0.06]; span = dist(le, re) * 0.78; }
  // Profile: one ear visible, the head centre sits between that ear and the nose.
  else if (ear && nose) { head = [(ear[0] + nose[0]) / 2, (ear[1] + nose[1]) / 2 - unit * 0.1]; span = dist(ear, nose) * 0.85; }
  else if (nose) head = [nose[0], nose[1] - unit * 0.08];
  else if (ls && rs) { const m = mid(ls, rs); head = [m[0], m[1] - unit * 0.72]; }
  const headR = Math.max(unit * 0.4, span);
  const faceShift = nose && head ? Math.max(-headR * 0.4, Math.min(headR * 0.4, (nose[0] - head[0]) * 0.9)) : 0;

  let torso: string | null = null;
  // Side views collapse the shoulder line, so the torso becomes a rounded capsule along the spine.
  const capsule = ls && rs && lh && rh && !frontal ? { a: mid(ls, rs), b: mid(lh, rh), w: Math.max(unit * 0.95, shoulderW + unit * 0.3) } : null;
  if (ls && rs && lh && rh && frontal) {
    const pad = unit * 0.12;
    const [lx, ly] = [ls[0] + pad, ls[1]];
    const [rx, ry] = [rs[0] - pad, rs[1]];
    const bottom = Math.max(lh[1], rh[1]) + unit * 0.14;
    torso = `M ${rx} ${ry + unit * 0.06} Q ${rx} ${ry - unit * 0.08} ${rx + unit * 0.2} ${ry - unit * 0.08} L ${lx - unit * 0.2} ${ly - unit * 0.08} Q ${lx} ${ly - unit * 0.08} ${lx} ${ly + unit * 0.06} L ${lh[0] + unit * 0.2} ${bottom} Q ${(lh[0] + rh[0]) / 2} ${bottom + unit * 0.08} ${rh[0] - unit * 0.2} ${bottom} Z`;
  }
  const neck = ls && rs && head ? mid(ls, rs) : null;

  const hand = (name: JointName) => {
    const p = joint(keypoints, name);
    return p ? <circle key={name} cx={p[0]} cy={p[1]} r={unit * 0.12} fill={palette.skin} /> : null;
  };
  const foot = (name: JointName, side: number) => {
    const p = joint(keypoints, name);
    return p ? <ellipse key={name} cx={p[0] + side * unit * 0.1} cy={p[1] + unit * 0.06} rx={unit * 0.2} ry={unit * 0.1} fill={palette.shoe} /> : null;
  };

  return (
    <g opacity={opacity} style={{ transition: "opacity .4s" }}>
      {(() => {
        const ankle = joint(keypoints, "left_ankle") ?? joint(keypoints, "right_ankle");
        return ankle && lh && rh ? <ellipse cx={(lh[0] + rh[0]) / 2} cy={ankle[1] + unit * 0.14} rx={unit * 0.75} ry={unit * 0.12} fill="rgba(90,60,30,0.16)" /> : null;
      })()}
      {limb("right_hip", "right_knee", unit * 0.36, palette.pants, "rt")}
      {limb("right_knee", "right_ankle", unit * 0.3, palette.pants, "rs")}
      {limb("left_hip", "left_knee", unit * 0.36, palette.pants, "lt")}
      {limb("left_knee", "left_ankle", unit * 0.3, palette.pants, "lsn")}
      {foot("right_ankle", -1)}
      {foot("left_ankle", 1)}
      {lh && rh && <line x1={lh[0]} y1={lh[1]} x2={rh[0]} y2={rh[1]} stroke={palette.pants} strokeWidth={unit * 0.4} strokeLinecap="round" />}
      {neck && head && <line x1={neck[0]} y1={neck[1]} x2={head[0] + faceShift * 0.3} y2={head[1] + headR * 0.7} stroke={palette.skin} strokeWidth={unit * 0.2} strokeLinecap="round" />}
      {torso && <path d={torso} fill={palette.top} />}
      {capsule && <line x1={capsule.a[0]} y1={capsule.a[1]} x2={capsule.b[0]} y2={capsule.b[1]} stroke={palette.top} strokeWidth={capsule.w} strokeLinecap="round" />}
      {torso && ls && rs && <path d={`M ${(ls[0] + rs[0]) / 2} ${ls[1] - unit * 0.02} V ${Math.max(lh![1], rh![1]) + unit * 0.12}`} stroke={palette.topShade} strokeWidth={unit * 0.04} />}
      {limb("left_shoulder", "left_elbow", unit * 0.27, palette.top, "lu")}
      {limb("left_elbow", "left_wrist", unit * 0.22, palette.topShade, "lf")}
      {limb("right_shoulder", "right_elbow", unit * 0.27, palette.top, "ru")}
      {limb("right_elbow", "right_wrist", unit * 0.22, palette.topShade, "rf")}
      {hand("left_wrist")}
      {hand("right_wrist")}
      {head && (
        <g>
          <circle cx={head[0]} cy={head[1]} r={headR} fill={palette.skin} />
          <path d={`M ${head[0] - headR * 1.02} ${head[1] - headR * 0.05} Q ${head[0] - headR * 0.95} ${head[1] - headR * 1.12} ${head[0]} ${head[1] - headR * 1.08} Q ${head[0] + headR * 0.95} ${head[1] - headR * 1.12} ${head[0] + headR * 1.02} ${head[1] - headR * 0.05} Q ${head[0] + headR * 0.7} ${head[1] - headR * 0.62} ${head[0]} ${head[1] - headR * 0.66} Q ${head[0] - headR * 0.7} ${head[1] - headR * 0.62} ${head[0] - headR * 1.02} ${head[1] - headR * 0.05} Z`} fill={palette.hair} />
          <circle cx={head[0] - headR * 0.98} cy={head[1] + headR * 0.08} r={headR * 0.17} fill={palette.skin} />
          <circle cx={head[0] + headR * 0.98} cy={head[1] + headR * 0.08} r={headR * 0.17} fill={palette.skin} />
          <g transform={`translate(${faceShift} 0)`}>
            <circle cx={head[0] - headR * 0.34} cy={head[1] + headR * 0.08} r={headR * 0.085} fill="#3b3a44" />
            <circle cx={head[0] + headR * 0.34} cy={head[1] + headR * 0.08} r={headR * 0.085} fill="#3b3a44" />
            <path d={`M ${head[0] - headR * 0.52} ${head[1] - headR * 0.14} q ${headR * 0.18} ${-headR * 0.08} ${headR * 0.32} 0 M ${head[0] + headR * 0.2} ${head[1] - headR * 0.14} q ${headR * 0.18} ${-headR * 0.08} ${headR * 0.32} 0`} stroke={palette.hair} strokeWidth={headR * 0.08} strokeLinecap="round" fill="none" />
            <circle cx={head[0] - headR * 0.56} cy={head[1] + headR * 0.36} r={headR * 0.14} fill="#ff9d8a" opacity="0.45" />
            <circle cx={head[0] + headR * 0.56} cy={head[1] + headR * 0.36} r={headR * 0.14} fill="#ff9d8a" opacity="0.45" />
            <path d={`M ${head[0] - headR * 0.2} ${head[1] + headR * 0.42} Q ${head[0]} ${head[1] + headR * 0.58} ${head[0] + headR * 0.2} ${head[1] + headR * 0.42}`} stroke="#9b5f55" strokeWidth={headR * 0.07} strokeLinecap="round" fill="none" />
          </g>
        </g>
      )}
    </g>
  );
}

/** Canonical skeleton overlay. `reveal` grows bones from the torso outwards. */
export function SkeletonLayer({ keypoints, reveal = 1, opacity = 1, color = "var(--skeleton)" }: { keypoints: Keypoints; reveal?: number; opacity?: number; color?: string }) {
  const shown = Math.ceil(BONES.length * Math.min(1, Math.max(0, reveal)));
  const joints = Object.entries(keypoints).filter(([, value]) => value && value[2] >= MIN_CONF) as Array<[JointName, Joint]>;
  return (
    <g opacity={opacity} style={{ transition: "opacity .4s" }}>
      <g stroke={color} strokeLinecap="round" fill="none">
        {BONES.slice(0, shown).map(([a, b]) => {
          const p = joint(keypoints, a);
          const q = joint(keypoints, b);
          return p && q ? <line key={`${a}-${b}`} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} strokeWidth={5} opacity={0.35 + Math.min(p[2], q[2]) * 0.6} /> : null;
        })}
      </g>
      {reveal > 0 && joints.map(([name, [x, y, confidence]], index) => (
        <circle key={name} cx={x} cy={y} r={name === "nose" ? 8 : 7} fill="#ffffff" stroke={color} strokeWidth={3.5} opacity={index / joints.length <= reveal ? 0.5 + confidence * 0.5 : 0} />
      ))}
    </g>
  );
}

export function keypointBounds(keypoints: Keypoints): { x: number; y: number; w: number; h: number } | null {
  const points = Object.values(keypoints).filter((value): value is Joint => Boolean(value));
  if (!points.length) return null;
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const x = Math.min(...xs);
  const y = Math.min(...ys);
  return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y };
}
