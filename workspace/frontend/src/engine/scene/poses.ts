import { COCO17, type Joint, type JointName, type Keypoints } from "./types.ts";

/** Local pose: hip centre at (0,0), +y downwards, COCO "left" is the person's left (image right). */
export type LocalPose = Record<JointName, [number, number]>;

const STAND: LocalPose = {
  nose: [0, -262], left_eye: [10, -272], right_eye: [-10, -272], left_ear: [24, -264], right_ear: [-24, -264],
  left_shoulder: [50, -196], right_shoulder: [-50, -196],
  left_elbow: [62, -112], right_elbow: [-62, -112],
  left_wrist: [66, -34], right_wrist: [-66, -34],
  left_hip: [30, 0], right_hip: [-30, 0],
  left_knee: [33, 108], right_knee: [-33, 108],
  left_ankle: [33, 212], right_ankle: [-33, 212],
};

function derive(changes: Partial<LocalPose>): LocalPose {
  return { ...STAND, ...changes };
}

export const POSES = {
  stand: STAND,
  walkA: derive({
    left_elbow: [70, -118], left_wrist: [88, -44], right_elbow: [-50, -114], right_wrist: [-34, -38],
    left_knee: [18, 106], left_ankle: [-6, 206], right_knee: [-40, 102], right_ankle: [-62, 204],
  }),
  walkB: derive({
    left_elbow: [52, -114], left_wrist: [36, -38], right_elbow: [-70, -118], right_wrist: [-88, -44],
    left_knee: [42, 102], left_ankle: [64, 204], right_knee: [-18, 106], right_ankle: [6, 206],
  }),
  /** Lean and reach towards the table on the image-left side. */
  reach: derive({
    nose: [-26, -250], left_eye: [-16, -260], right_eye: [-36, -258], left_ear: [-2, -254], right_ear: [-46, -250],
    left_shoulder: [34, -188], right_shoulder: [-64, -182],
    right_elbow: [-128, -128], right_wrist: [-190, -72],
    left_elbow: [50, -108], left_wrist: [54, -32],
  }),
  hold: derive({
    right_elbow: [-104, -132], right_wrist: [-128, -150],
  }),
  handToFace: derive({
    nose: [-4, -260], right_elbow: [-76, -148], right_wrist: [-22, -236],
  }),
} satisfies Record<string, LocalPose>;

export type PoseName = keyof typeof POSES;

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
export const clamp01 = (t: number) => Math.min(1, Math.max(0, t));

export function blendPose(a: LocalPose, b: LocalPose, t: number): LocalPose {
  const result = {} as LocalPose;
  COCO17.forEach((joint) => {
    result[joint] = [lerp(a[joint][0], b[joint][0], t), lerp(a[joint][1], b[joint][1], t)];
  });
  return result;
}

/** Place a local pose at a world root with a uniform scale; confidence can taper per joint. */
export function placePose(pose: LocalPose, rootX: number, rootY: number, scale = 1, confidence = 0.92): Keypoints {
  const keypoints: Keypoints = {};
  COCO17.forEach((joint, index) => {
    const [x, y] = pose[joint];
    const jitter = ((index * 37) % 7) / 100;
    keypoints[joint] = [rootX + x * scale, rootY + y * scale, Math.min(0.99, confidence + jitter - 0.03)] satisfies Joint;
  });
  return keypoints;
}
