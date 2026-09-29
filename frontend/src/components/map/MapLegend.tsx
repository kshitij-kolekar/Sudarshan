import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Layers } from 'lucide-react';

export const MapLegend: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="absolute bottom-4 left-4 z-20 pointer-events-auto">
      <div className="bg-surface/95 backdrop-blur-md border border-border rounded-lg shadow-card text-charcoal-700 w-56 sm:w-64 transition-all duration-200">
        {/* Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-3 py-2 flex items-center justify-between text-left text-xs font-mono font-medium border-b border-border/60 hover:bg-surface-subtle transition-colors rounded-t-lg"
        >
          <div className="flex items-center gap-1.5 text-charcoal-700">
            <Layers className="w-3.5 h-3.5 text-terracotta" />
            <span className="font-semibold uppercase tracking-wider text-[10px]">Survey Legend</span>
          </div>
          {isExpanded ? <ChevronDown className="w-3 h-3 text-charcoal-400" /> : <ChevronUp className="w-3 h-3 text-charcoal-400" />}
        </button>

        {/* Legend Items */}
        {isExpanded && (
          <div className="p-3 space-y-2 text-[11px] font-sans">
            <div className="flex items-center gap-2.5">
              <span className="w-3 h-3 rounded-full bg-red-600 border border-white shadow-xs shrink-0" />
              <span className="text-charcoal-700 font-medium">Critical Defect (&gt;50mm depth)</span>
            </div>

            <div className="flex items-center gap-2.5">
              <span className="w-3 h-3 rounded-full bg-orange-500 border border-white shadow-xs shrink-0" />
              <span className="text-charcoal-600">High / Medium Severity</span>
            </div>

            <div className="flex items-center gap-2.5">
              <span className="w-3 h-3 rounded-full bg-amber-400 border border-white shadow-xs shrink-0" />
              <span className="text-charcoal-600">Low / Surface Ravelling</span>
            </div>

            <div className="h-[1px] bg-border/60 my-1" />

            <div className="flex items-center gap-2.5">
              <span className="w-5 h-0.5 bg-charcoal-900 shrink-0" />
              <span className="text-charcoal-600">Road Centerline / Chainage</span>
            </div>

            <div className="flex items-center gap-2.5">
              <span className="w-5 h-2 bg-terracotta/20 border border-dashed border-terracotta/60 shrink-0" />
              <span className="text-charcoal-600">Survey Corridor Buffer (50m)</span>
            </div>

            <div className="flex items-center gap-2.5">
              <span className="w-5 h-0.5 border-t border-dashed border-forest shrink-0" />
              <span className="text-charcoal-600">Aerial Drone Swath Path</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
