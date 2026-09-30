/** Neutral environment used when no empty-room photo is configured. Nothing here pretends to be the room. */
export function SpatialGrid() {
  return (
    <g aria-hidden="true">
      <rect width="1600" height="1000" fill="#eeebe5" />
      <g stroke="rgba(60,50,40,0.05)">
        {Array.from({ length: 33 }, (_, i) => <line key={`x${i}`} x1={i * 50} y1="0" x2={i * 50} y2="1000" />)}
        {Array.from({ length: 21 }, (_, i) => <line key={`y${i}`} x1="0" y1={i * 50} x2="1600" y2={i * 50} />)}
      </g>
      <g stroke="rgba(60,50,40,0.1)">
        {Array.from({ length: 9 }, (_, i) => <line key={`X${i}`} x1={i * 200} y1="0" x2={i * 200} y2="1000" />)}
        {Array.from({ length: 6 }, (_, i) => <line key={`Y${i}`} x1="0" y1={i * 200} x2="1600" y2={i * 200} />)}
      </g>
    </g>
  );
}
