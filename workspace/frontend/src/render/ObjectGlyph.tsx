import type { GlyphKind } from "../engine/labels";

/** Stylised object illustrations drawn in a 100×100 box. */
export function GlyphShape({ kind }: { kind: GlyphKind }) {
  switch (kind) {
    case "pillbox":
      return <g>
        <rect x="12" y="30" width="76" height="46" rx="9" fill="#ffffff" stroke="#c9d3df" strokeWidth="2" />
        <rect x="12" y="30" width="76" height="15" rx="7" fill="#5ab8ff" />
        <rect x="12" y="38" width="76" height="7" fill="#5ab8ff" />
        {[31, 50, 69].map((x) => <line key={x} x1={x} y1="49" x2={x} y2="72" stroke="#c3cfdc" strokeWidth="2" />)}
        <rect x="20" y="55" width="7" height="12" rx="3.5" fill="#ff8c7a" />
        <rect x="39" y="55" width="7" height="12" rx="3.5" fill="#ffd166" />
        <rect x="58" y="55" width="7" height="12" rx="3.5" fill="#7fd8a8" />
      </g>;
    case "bottle":
      return <g>
        <rect x="35" y="12" width="30" height="15" rx="4" fill="#eef2f7" />
        <path d="M30 34 Q30 26 38 26 H62 Q70 26 70 34 V84 Q70 90 64 90 H36 Q30 90 30 84 Z" fill="#f2a03d" opacity="0.92" />
        <rect x="30" y="46" width="40" height="24" fill="#fff6e8" />
        <path d="M44 58 H56 M50 52 V64" stroke="#f2a03d" strokeWidth="4" strokeLinecap="round" />
      </g>;
    case "cup":
      return <g>
        <path d="M70 40 Q88 40 86 56 Q84 70 68 68" fill="none" stroke="#bcd9f5" strokeWidth="6" />
        <path d="M22 22 H74 L68 86 Q67 90 62 90 H34 Q29 90 28 86 Z" fill="#e6f1fc" stroke="#9fc0e0" strokeWidth="2" />
        <path d="M26 44 H71 L67 86 Q66 89 62 89 H34 Q30 89 29 86 Z" fill="#5ab8ff" opacity="0.45" />
      </g>;
    case "glasses":
      return <g fill="none" stroke="#4b5563" strokeWidth="5" strokeLinecap="round">
        <circle cx="29" cy="54" r="17" fill="rgba(143,190,230,0.3)" />
        <circle cx="71" cy="54" r="17" fill="rgba(143,190,230,0.3)" />
        <path d="M46 52 Q50 46 54 52" />
        <path d="M12 50 L4 40 M88 50 L96 40" />
      </g>;
    case "keys":
      return <g>
        <circle cx="32" cy="36" r="17" fill="none" stroke="#8a929c" strokeWidth="6" />
        <path d="M44 48 L80 84 M66 70 L74 62 M74 78 L82 70" stroke="#e0a830" strokeWidth="7" strokeLinecap="round" />
      </g>;
    case "drill":
      return <g>
        <rect x="16" y="26" width="54" height="26" rx="8" fill="#ffb547" />
        <rect x="70" y="34" width="14" height="10" rx="2" fill="#9aa5b4" />
        <rect x="84" y="37" width="12" height="4" rx="2" fill="#cfd6df" />
        <path d="M30 52 L26 84 Q26 88 30 88 H46 Q50 88 50 84 L50 52 Z" fill="#3a4454" />
        <rect x="24" y="80" width="30" height="10" rx="3" fill="#ffb547" />
      </g>;
    case "screwdriver":
      return <g transform="rotate(-35 50 50)">
        <rect x="14" y="40" width="36" height="20" rx="9" fill="#ff6b6b" />
        <rect x="18" y="44" width="28" height="4" rx="2" fill="#ff9a9a" />
        <rect x="50" y="46" width="34" height="8" rx="2" fill="#c9d1dc" />
        <path d="M84 46 L94 50 L84 54 Z" fill="#9aa5b4" />
      </g>;
    default:
      return <g>
        <path d="M50 14 L84 32 V70 L50 88 L16 70 V32 Z" fill="#e3d2bd" stroke="#b08a62" strokeWidth="3" strokeLinejoin="round" />
        <path d="M16 32 L50 50 L84 32 M50 50 V88" fill="none" stroke="#b08a62" strokeWidth="3" strokeLinejoin="round" opacity="0.7" />
      </g>;
  }
}

export function ObjectGlyph({ kind, size = 48 }: { kind: GlyphKind; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true"><GlyphShape kind={kind} /></svg>;
}
