import { STAGE_HEIGHT, STAGE_WIDTH } from "./types.ts";

export interface ObjectBox { x: number; y: number; w: number; h: number }

/**
 * Where the rehearsed person walks and where the real objects sit, in stage
 * coordinates (1600×1000, box x/y are centres).
 */
export interface SceneLayout {
  enterX: number;
  stopX: number;
  rootY: number;
  scale: number;
  objects: Record<string, ObjectBox>;
}

// Local pose geometry (see poses.ts): the reaching right wrist sits 190 px left
// of and 72 px above the hip; ankles are 212 px below the hip.
const REACH_DX = 190;
const REACH_DY = -72;
const ANKLE_DY = 212;

export const MEDICATION_OBJECT_ID = "obj-01";

/**
 * Derive walk target, hip height and body scale from two facts about the
 * scene: where the pill box sits and where the floor is. The person then
 * stands on the floor and the reaching hand lands on the pill box, whatever
 * photo is used as the background.
 */
export function fitLayout(objects: Record<string, ObjectBox>, floorY: number, enterX?: number): SceneLayout {
  const pill = objects[MEDICATION_OBJECT_ID];
  if (!pill) throw new Error(`layout needs the pill box "${MEDICATION_OBJECT_ID}"`);
  const handY = pill.y - pill.h * 0.4;
  const scale = Math.max(0.4, (floorY - handY) / (ANKLE_DY - REACH_DY));
  const rootY = floorY - ANKLE_DY * scale;
  const stopX = pill.x + REACH_DX * scale + 2;
  return { enterX: enterX ?? Math.min(STAGE_WIDTH - 100, stopX + 500), stopX, rootY, scale, objects };
}

export const DEFAULT_LAYOUT: SceneLayout = fitLayout({
  "obj-01": { x: 780, y: 592, w: 74, h: 46 },
  "obj-04": { x: 884, y: 586, w: 42, h: 58 },
  "obj-06": { x: 517, y: 534, w: 64, h: 28 },
}, 900, 1500);

/** `public/demo-scene/scene.json`: coordinates are pixels in the photo, boxes are [left, top, width, height]. */
export interface SceneConfig {
  image: string;
  width: number;
  height: number;
  floorY: number;
  enterX?: number;
  objects: Record<string, [number, number, number, number]>;
}

/** Map photo pixels to stage coordinates using the same "cover" crop the stage applies to the image. */
export function layoutFromConfig(config: SceneConfig): SceneLayout {
  const scale = Math.max(STAGE_WIDTH / config.width, STAGE_HEIGHT / config.height);
  const offsetX = (STAGE_WIDTH - config.width * scale) / 2;
  const offsetY = (STAGE_HEIGHT - config.height * scale) / 2;
  const objects: Record<string, ObjectBox> = {};
  Object.entries(config.objects).forEach(([id, [left, top, width, height]]) => {
    objects[id] = { x: offsetX + (left + width / 2) * scale, y: offsetY + (top + height / 2) * scale, w: width * scale, h: height * scale };
  });
  const enterX = typeof config.enterX === "number" ? offsetX + config.enterX * scale : undefined;
  return fitLayout(objects, offsetY + config.floorY * scale, enterX);
}
