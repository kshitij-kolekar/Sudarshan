import React from 'react';

export const HeroVisual: React.FC = () => {
  return (
    <div className="relative w-full rounded-xl border border-border bg-surface shadow-card overflow-hidden">
      {/* Top Engineering Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-surface-subtle border-b border-border text-[11px] font-mono text-charcoal-500">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-forest" />
          <span className="font-semibold text-charcoal-700">GEODESIC SURVEY ENGINE</span>
          <span className="text-charcoal-300">|</span>
          <span>CORRIDOR SCANNER V2</span>
        </div>
        <div className="hidden sm:flex items-center gap-3 text-charcoal-400">
          <span>GSD: 1.2 CM/PX</span>
          <span>•</span>
          <span>CRS: EPSG:4326</span>
        </div>
      </div>

      {/* Main Vector GIS CAD Canvas */}
      <div className="relative aspect-[16/10] sm:aspect-[16/9] w-full bg-canvas bg-cad-grid p-6 flex flex-col justify-between">
        
        {/* Coordinate HUD Overlay - Top Left */}
        <div className="absolute top-4 left-4 z-10 bg-surface/90 backdrop-blur-xs border border-border/80 rounded px-3 py-1.5 shadow-subtle font-mono text-[11px] text-charcoal-600 space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="text-charcoal-400">DATUM:</span>
            <span className="font-semibold text-charcoal-800">WGS84 / EGM96</span>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-charcoal-400">
            <span>GRID: LAT/LON 100M</span>
          </div>
        </div>

        {/* Status Chip - Top Right */}
        <div className="absolute top-4 right-4 z-10 bg-surface/90 backdrop-blur-xs border border-border/80 rounded px-3 py-1.5 shadow-subtle font-mono text-[11px] text-charcoal-600 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-terracotta" />
          <span className="text-charcoal-700">SURVEY TELEMETRY READY</span>
        </div>

        {/* Detailed SVG Engineering Diagram */}
        <svg
          className="w-full h-full"
          viewBox="0 0 800 450"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Linear gradients */}
            <linearGradient id="corridorGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#C4542E" stopOpacity="0.08" />
              <stop offset="50%" stopColor="#C4542E" stopOpacity="0.03" />
              <stop offset="100%" stopColor="#2B5840" stopOpacity="0.06" />
            </linearGradient>

            <pattern id="cadGridSmall" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#E5E3DC" strokeWidth="0.5" />
            </pattern>
          </defs>

          {/* Survey CAD Grid */}
          <rect width="800" height="450" fill="url(#cadGridSmall)" opacity="0.6" />

          {/* Contour elevation isolines (subtle civil topography) */}
          <path
            d="M 0 100 Q 200 60 400 130 T 800 90"
            stroke="#D2CEC4"
            strokeWidth="0.75"
            strokeDasharray="4 4"
            fill="none"
          />
          <path
            d="M 0 180 Q 220 140 420 220 T 800 170"
            stroke="#D2CEC4"
            strokeWidth="0.75"
            strokeDasharray="4 4"
            fill="none"
          />
          <path
            d="M 0 280 Q 240 240 440 320 T 800 270"
            stroke="#D2CEC4"
            strokeWidth="0.75"
            strokeDasharray="4 4"
            fill="none"
          />

          {/* Survey Corridor Area */}
          <path
            d="M 80 430 C 220 380, 240 260, 360 210 S 580 160, 720 30"
            stroke="#C4542E"
            strokeWidth="56"
            strokeLinecap="round"
            strokeOpacity="0.12"
            fill="none"
          />

          {/* Road Right-of-Way Left Boundary */}
          <path
            d="M 64 420 C 204 370, 224 250, 344 200 S 564 150, 704 20"
            stroke="#A5C5B2"
            strokeWidth="1.5"
            strokeDasharray="6 3"
            fill="none"
          />

          {/* Road Right-of-Way Right Boundary */}
          <path
            d="M 96 440 C 236 390, 256 270, 376 220 S 596 170, 736 40"
            stroke="#A5C5B2"
            strokeWidth="1.5"
            strokeDasharray="6 3"
            fill="none"
          />

          {/* Road Centerline (Chainage Alignment) */}
          <path
            d="M 80 430 C 220 380, 240 260, 360 210 S 580 160, 720 30"
            stroke="#1D1F22"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />

          {/* Centerline Dash Marking */}
          <path
            d="M 80 430 C 220 380, 240 260, 360 210 S 580 160, 720 30"
            stroke="#F8F7F4"
            strokeWidth="1"
            strokeDasharray="8 6"
            fill="none"
          />

          {/* Chainage Cross-Sections & Station Marks */}
          {/* Station 0+000 */}
          <g transform="translate(130, 400)">
            <line x1="-15" y1="-8" x2="15" y2="8" stroke="#636873" strokeWidth="1.5" />
            <text x="22" y="5" fill="#636873" fontSize="9" fontFamily="monospace" fontWeight="600">CH 0+000</text>
          </g>

          {/* Station 0+500 */}
          <g transform="translate(250, 305)">
            <line x1="-16" y1="-10" x2="16" y2="10" stroke="#636873" strokeWidth="1.5" />
            <text x="24" y="5" fill="#636873" fontSize="9" fontFamily="monospace" fontWeight="600">CH 0+500</text>
          </g>

          {/* Station 1+000 (Inspection Focus) */}
          <g transform="translate(360, 210)">
            <line x1="-18" y1="-12" x2="18" y2="12" stroke="#C4542E" strokeWidth="2" />
            <circle cx="0" cy="0" r="16" stroke="#C4542E" strokeWidth="1" strokeDasharray="3 3" />
            <circle cx="0" cy="0" r="3" fill="#C4542E" />
            <text x="26" y="4" fill="#C4542E" fontSize="9" fontFamily="monospace" fontWeight="700">CH 1+000 [SURVEY CORRIDOR]</text>
          </g>

          {/* Station 1+500 */}
          <g transform="translate(500, 160)">
            <line x1="-16" y1="-8" x2="16" y2="8" stroke="#636873" strokeWidth="1.5" />
            <text x="24" y="5" fill="#636873" fontSize="9" fontFamily="monospace" fontWeight="600">CH 1+500</text>
          </g>

          {/* Station 2+000 */}
          <g transform="translate(650, 80)">
            <line x1="-16" y1="-10" x2="16" y2="10" stroke="#636873" strokeWidth="1.5" />
            <text x="24" y="5" fill="#636873" fontSize="9" fontFamily="monospace" fontWeight="600">CH 2+000</text>
          </g>

          {/* Drone Aerial Flight Vector Path */}
          <path
            d="M 60 410 L 210 330 L 370 230 L 520 130 L 680 50"
            stroke="#2B5840"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            fill="none"
          />

          {/* Drone Inspection Sensor Swath Crosshairs */}
          <g transform="translate(480, 150)">
            <circle cx="0" cy="0" r="28" stroke="#2B5840" strokeWidth="1" opacity="0.6" />
            <circle cx="0" cy="0" r="44" stroke="#2B5840" strokeWidth="0.75" strokeDasharray="3 3" opacity="0.4" />
            <line x1="-34" y1="0" x2="34" y2="0" stroke="#2B5840" strokeWidth="1" opacity="0.7" />
            <line x1="0" y1="-34" x2="0" y2="34" stroke="#2B5840" strokeWidth="1" opacity="0.7" />
            <polygon points="0,-4 3,3 -3,3" fill="#2B5840" />
            <text x="36" y="-12" fill="#2B5840" fontSize="9" fontFamily="monospace" fontWeight="600">DRONE SWATH: 32M</text>
            <text x="36" y="2" fill="#636873" fontSize="8" fontFamily="monospace">FOV 84° / 4K EO SENSOR</text>
          </g>

          {/* Scale Bar Vector */}
          <g transform="translate(50, 420)">
            <line x1="0" y1="0" x2="100" y2="0" stroke="#1D1F22" strokeWidth="2" />
            <line x1="0" y1="-4" x2="0" y2="4" stroke="#1D1F22" strokeWidth="2" />
            <line x1="50" y1="-3" x2="50" y2="3" stroke="#1D1F22" strokeWidth="1.5" />
            <line x1="100" y1="-4" x2="100" y2="4" stroke="#1D1F22" strokeWidth="2" />
            <text x="36" y="-8" fill="#1D1F22" fontSize="9" fontFamily="monospace">100 METERS</text>
          </g>

          {/* True North Arrow */}
          <g transform="translate(740, 410)">
            <circle cx="0" cy="0" r="18" fill="#FFFFFF" stroke="#D2CEC4" strokeWidth="1" />
            <polygon points="0,-14 5,4 0,0 -5,4" fill="#C4542E" />
            <polygon points="0,0 5,4 0,14 -5,4" fill="#D2CEC4" />
            <text x="-4" y="-18" fill="#1D1F22" fontSize="9" fontFamily="monospace" fontWeight="bold">N</text>
          </g>
        </svg>

        {/* Bottom Metadata Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-border/80 font-mono text-[10px] text-charcoal-400">
          <div className="flex items-center gap-3">
            <span>SURFACE: ASPHALTIC CONCRETE</span>
            <span>•</span>
            <span>LANE WIDTH: 3.75M</span>
            <span>•</span>
            <span>TOTAL RIGHT-OF-WAY: 30M</span>
          </div>
          <div className="text-charcoal-600 font-medium">
            FIELD READY — READY FOR SURVEY INGESTION
          </div>
        </div>

      </div>
    </div>
  );
};
