export function BrandEmblem() {
  return (
    <svg
      className="brand-emblem"
      viewBox="0 0 72 72"
      role="img"
      aria-label="MIA 보호소 심볼"
    >
      <defs>
        <linearGradient id="emblem-gold" x1="12" y1="8" x2="60" y2="64">
          <stop offset="0" stopColor="#fff0ae" />
          <stop offset="0.42" stopColor="#f4c45f" />
          <stop offset="1" stopColor="#a86b1e" />
        </linearGradient>
        <radialGradient id="emblem-core" cx="50%" cy="44%" r="58%">
          <stop offset="0" stopColor="#52c9ff" stopOpacity="0.42" />
          <stop offset="0.54" stopColor="#24578d" stopOpacity="0.1" />
          <stop offset="1" stopColor="#071222" stopOpacity="0" />
        </radialGradient>
        <filter id="emblem-glow" x="-35%" y="-35%" width="170%" height="170%">
          <feGaussianBlur stdDeviation="1.7" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <circle cx="36" cy="36" r="32.5" fill="rgba(4, 15, 29, .78)" />
      <circle cx="36" cy="36" r="31.5" fill="none" stroke="url(#emblem-gold)" strokeWidth="1.4" />
      <circle cx="36" cy="36" r="26.5" fill="url(#emblem-core)" stroke="#d89f3f" strokeOpacity="0.3" strokeWidth="0.7" />

      <path className="emblem-orbit" d="M13 42A24 24 0 0 0 30 58" />
      <path className="emblem-orbit" d="M59 30A24 24 0 0 0 42 14" />
      <path className="emblem-ray" d="M36 8V18M31.8 12.5 36 18l4.2-5.5" />

      <g filter="url(#emblem-glow)">
        <path className="emblem-diamond outer" d="M36 18 53 35 36 54 19 35Z" />
        <path className="emblem-diamond inner" d="M36 25.5 45.5 35 36 45.5 26.5 35Z" />
        <path className="emblem-path" d="m24 48 12 8 12-8M29 53.5 36 62l7-8.5" />
      </g>

      <circle cx="11.5" cy="35.5" r="1.4" fill="#f5ce70" />
      <circle cx="60.5" cy="35.5" r="1.4" fill="#f5ce70" />
    </svg>
  )
}
