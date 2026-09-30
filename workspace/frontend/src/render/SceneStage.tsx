import type { SceneFrame, SceneObject } from "../engine/scene/types";
import { STAGE_HEIGHT, STAGE_WIDTH } from "../engine/scene/types";
import { CartoonAvatar, SkeletonLayer, keypointBounds } from "./Avatar";
import { SpatialGrid } from "./SpatialGrid";
import "./scene.css";

export type ViewMode = "cartoon" | "skeleton" | "fusion";

function Brackets({ x, y, w, h, color, size = 18 }: { x: number; y: number; w: number; h: number; color: string; size?: number }) {
  const s = Math.min(size, w / 2.5, h / 2.5);
  const d = `M ${x} ${y + s} V ${y} H ${x + s} M ${x + w - s} ${y} H ${x + w} V ${y + s} M ${x + w} ${y + h - s} V ${y + h} H ${x + w - s} M ${x + s} ${y + h} H ${x} V ${y + h - s}`;
  return <path d={d} fill="none" stroke={color} strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" />;
}

function Tag({ x, y, text, sub, color }: { x: number; y: number; text: string; sub?: string; color: string }) {
  // CJK glyphs are ~1em wide, Latin/digits ~0.6em.
  const measure = (value: string, size: number) => [...value].reduce((sum, char) => sum + (/[　-鿿＀-￯]/.test(char) ? size : size * 0.6), 0);
  const width = measure(text, 24) + (sub ? measure(sub, 20) + 10 : 0) + 40;
  const left = x - width / 2;
  return (
    <g className="scene-tag">
      <rect x={left} y={y - 24} width={width} height={44} rx={22} fill="rgba(255,255,255,0.95)" stroke="rgba(60,50,40,0.12)" strokeWidth={1.5} style={{ filter: "drop-shadow(0 4px 10px rgba(60,40,20,0.18))" }} />
      <circle cx={left + 18} cy={y - 2} r={5} fill={color} />
      <text x={left + 32} y={y + 6} fontSize={24} fontWeight={600} fill="#22252a">{text}{sub && <tspan dx={10} fontSize={20} fontWeight={500} fill={color}>{sub}</tspan>}</text>
    </g>
  );
}

/**
 * Objects are never redrawn: the real object is in the environment image, so
 * the stage only adds a detection frame and a label on top of it.
 */
function ObjectMarker({ object, showTag }: { object: SceneObject; showTag: boolean }) {
  if (object.state === "hidden") return null;
  const color = object.medication ? "#3a73e8" : "#5d636c";
  const pad = 12 + (1 - object.lock) * 60;
  return (
    <g opacity={Math.min(1, object.lock * 1.4)}>
      <Brackets x={object.x - object.w / 2 - pad} y={object.y - object.h / 2 - pad} w={object.w + pad * 2} h={object.h + pad * 2} color={color} />
      {object.lock >= 1 && showTag && <Tag x={object.x} y={object.y - object.h / 2 - 38} text={object.label} sub={object.state === "held" ? "手持中" : `${Math.round(object.confidence * 100)}%`} color={color} />}
    </g>
  );
}

/**
 * Privacy stage. Only the person is transformed (skeleton or cartoon from
 * keypoints); the environment is either an empty-room photo or a neutral grid.
 */
export function SceneStage({ frame, view, backdropImage = null, showTags = true, className = "" }: { frame: SceneFrame | null; view: ViewMode; backdropImage?: string | null; showTags?: boolean; className?: string }) {
  const person = frame?.person ?? null;
  const skeletonReveal = frame?.skeletonReveal ?? 0;
  const cartoonReveal = frame?.cartoonReveal ?? 0;
  // Only registered people get an avatar; unregistered people stay a skeleton whatever the view.
  const unregistered = person?.render === "unregistered";
  const avatarAllowed = person?.render !== "unregistered";
  const cartoonOpacity = !avatarAllowed || view === "skeleton" ? 0 : view === "fusion" ? cartoonReveal * 0.88 : cartoonReveal;
  const skeletonOpacity = !avatarAllowed ? (skeletonReveal > 0 ? 1 : 0) : view === "cartoon" ? (skeletonReveal > 0 ? Math.max(0, 1 - cartoonReveal) : 0) : skeletonReveal > 0 ? 1 : 0;
  const bounds = person ? keypointBounds(person.keypoints) : null;
  const detecting = person && skeletonReveal === 0;
  const heldObjects = frame?.objects.filter((object) => object.state === "held") ?? [];
  const restObjects = frame?.objects.filter((object) => object.state !== "held") ?? [];

  return (
    <svg className={`scene-stage ${className}`} viewBox={`0 0 ${STAGE_WIDTH} ${STAGE_HEIGHT}`} preserveAspectRatio="xMidYMid slice" role="img" aria-label="隐私画面：环境保持原样，只有人物换成骨骼或卡通形象">
      {backdropImage ? <image href={backdropImage} x={0} y={0} width={STAGE_WIDTH} height={STAGE_HEIGHT} preserveAspectRatio="xMidYMid slice" /> : <SpatialGrid />}
      {restObjects.map((object) => <ObjectMarker key={object.id} object={object} showTag={showTags} />)}

      {person && bounds && (
        <g opacity={person.opacity}>
          {detecting && (
            <g>
              <rect x={bounds.x - 50} y={bounds.y - 70} width={bounds.w + 100} height={bounds.h + 110} rx={24} fill="rgba(245,243,239,0.55)" stroke="#3a73e8" strokeOpacity={0.6} strokeWidth={3} strokeDasharray="12 12" />
              {showTags && <Tag x={bounds.x + bounds.w / 2} y={bounds.y - 96} text="有人进入" sub="识别中" color="#3a73e8" />}
            </g>
          )}
          <CartoonAvatar keypoints={person.keypoints} opacity={cartoonOpacity} />
          {heldObjects.map((object) => <ObjectMarker key={object.id} object={object} showTag={showTags} />)}
          {unregistered && skeletonReveal > 0 && <rect x={bounds.x - 30} y={bounds.y - 40} width={bounds.w + 60} height={bounds.h + 70} rx={18} fill="rgba(214,69,69,0.08)" stroke="#d64545" strokeWidth={3} strokeDasharray="10 8" />}
          <SkeletonLayer keypoints={person.keypoints} reveal={skeletonReveal} opacity={skeletonOpacity} color={unregistered ? "#d64545" : undefined} />
          {!detecting && showTags && <Tag x={bounds.x + bounds.w / 2} y={bounds.y - 96} text={person.label} sub={unregistered ? "需要确认" : person.identified ? person.action : "识别中"} color={unregistered ? "#d64545" : person.identified ? "#1f9d63" : "#3a73e8"} />}
        </g>
      )}
    </svg>
  );
}
