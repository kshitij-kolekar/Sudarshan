import React from 'react';
import { Defect } from '../../types';

interface DefectMarkerProps {
  defect: Defect;
  isSelected?: boolean;
  onSelect?: (defect: Defect) => void;
  // Position percentage or coordinate mapped to viewport
  posX?: number;
  posY?: number;
}

export const DefectMarker: React.FC<DefectMarkerProps> = ({
  defect,
  isSelected = false,
  onSelect,
  posX = 50,
  posY = 50,
}) => {
  const severityColors = {
    critical: 'bg-red-600 border-red-800 text-white',
    high: 'bg-orange-500 border-orange-700 text-white',
    medium: 'bg-amber-500 border-amber-700 text-white',
    low: 'bg-slate-500 border-slate-700 text-white',
  };

  return (
    <div
      style={{ left: `${posX}%`, top: `${posY}%` }}
      className="absolute -translate-x-1/2 -translate-y-1/2 z-30 cursor-pointer group"
      onClick={() => onSelect && onSelect(defect)}
    >
      <div className="relative flex items-center justify-center">
        {/* Pulsing ring for critical defects */}
        {defect.severity === 'critical' && (
          <span className="absolute w-8 h-8 rounded-full bg-red-500/30 animate-ping pointer-events-none" />
        )}

        {/* Selected target ring */}
        {isSelected && (
          <span className="absolute w-7 h-7 rounded-full border-2 border-charcoal-900 pointer-events-none" />
        )}

        {/* Defect pin core */}
        <div
          className={`w-4 h-4 rounded-full border-2 shadow-card transition-transform group-hover:scale-125 ${
            severityColors[defect.severity]
          }`}
        />
      </div>

      {/* Hover tooltip */}
      <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 whitespace-nowrap bg-charcoal-900 text-white text-[10px] font-mono px-2 py-1 rounded shadow-elevated z-40 pointer-events-none">
        <div>{defect.roadSection}</div>
        <div className="text-charcoal-300">
          {defect.defectType.toUpperCase()} ({defect.severity})
        </div>
      </div>
    </div>
  );
};
