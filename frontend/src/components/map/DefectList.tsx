import React from 'react';
import { Defect, Severity } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { EmptyState } from '../common/EmptyState';
import { AlertCircle, ChevronRight, MapPin } from 'lucide-react';

interface DefectListProps {
  defects?: Defect[];
  selectedDefectId?: string | null;
  onSelectDefect?: (defect: Defect) => void;
  severityFilter?: Severity;
  onSeverityFilterChange?: (filter?: Severity) => void;
  className?: string;
}

export const DefectList: React.FC<DefectListProps> = ({
  defects = [],
  selectedDefectId,
  onSelectDefect,
  severityFilter,
  onSeverityFilterChange,
  className = '',
}) => {
  const filtered = severityFilter
    ? defects.filter((d) => d.severity === severityFilter)
    : defects;

  const severityOptions: { id?: Severity; label: string }[] = [
    { id: undefined, label: 'All' },
    { id: 'critical', label: 'Critical' },
    { id: 'high', label: 'High' },
    { id: 'medium', label: 'Medium' },
    { id: 'low', label: 'Low' },
  ];

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Severity Filter Tabs */}
      <div className="p-3 border-b border-border bg-surface-subtle/50 flex items-center gap-1.5 overflow-x-auto text-[11px] font-mono">
        <span className="text-charcoal-400 mr-1 text-[10px] uppercase">SEVERITY:</span>
        {severityOptions.map((opt) => (
          <button
            key={opt.label}
            onClick={() => onSeverityFilterChange && onSeverityFilterChange(opt.id)}
            className={`px-2 py-0.5 rounded transition-colors whitespace-nowrap ${
              severityFilter === opt.id
                ? 'bg-charcoal-900 text-white font-medium shadow-xs'
                : 'text-charcoal-600 hover:bg-surface-subtle hover:text-charcoal-900'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* List Content */}
      <div className="flex-1 overflow-y-auto p-3">
        {filtered.length > 0 ? (
          // Ready for real defect items once backend is wired
          <div className="space-y-2">
            {filtered.map((item) => {
              const isSelected = selectedDefectId === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => onSelectDefect && onSelectDefect(item)}
                  className={`p-3 rounded-lg border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-surface border-terracotta shadow-subtle ring-1 ring-terracotta/20'
                      : 'bg-surface border-border hover:border-charcoal-300'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-xs font-semibold text-charcoal-900">
                      {item.roadSection}
                    </span>
                    <StatusBadge severity={item.severity} />
                  </div>

                  <div className="text-[11px] text-charcoal-500 font-mono flex items-center justify-between">
                    <span className="capitalize">{item.defectType.replace('_', ' ')}</span>
                    {item.depthMm && <span>Depth: {item.depthMm}mm</span>}
                  </div>

                  <div className="mt-2 pt-2 border-t border-border/50 text-[10px] font-mono text-charcoal-400 flex items-center justify-between">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}
                    </span>
                    <ChevronRight className="w-3.5 h-3.5 text-charcoal-400" />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Empty State strictly matching Requirement 13 */
          <div className="h-full flex items-center justify-center py-8">
            <EmptyState
              title="No defects detected"
              description="Detected road defects will appear here after survey data is available."
              icon={AlertCircle}
              compact
            />
          </div>
        )}
      </div>

      {/* Footer Status */}
      <div className="p-3 border-t border-border bg-surface-subtle/50 text-[11px] font-mono text-charcoal-500 flex items-center justify-between">
        <span>DEFECTS FOUND: {filtered.length}</span>
        <span className="text-charcoal-400">INDEX: EMPTY</span>
      </div>
    </div>
  );
};
