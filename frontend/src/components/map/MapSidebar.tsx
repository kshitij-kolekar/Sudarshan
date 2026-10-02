import React, { useState } from 'react';
import { Defect, Severity } from '../../types';
import { DefectList } from './DefectList';
import { Search, MapPin, Info, X } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';

interface MapSidebarProps {
  defects?: Defect[];
  selectedDefect?: Defect | null;
  onSelectDefect?: (defect: Defect | null) => void;
  severityFilter?: Severity;
  onSeverityFilterChange?: (filter?: Severity) => void;
  className?: string;
}

export const MapSidebar: React.FC<MapSidebarProps> = ({
  defects = [],
  selectedDefect = null,
  onSelectDefect,
  severityFilter,
  onSeverityFilterChange,
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<'defects' | 'metadata'>('defects');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDefects = defects.filter((d) => {
    const matchesSearch =
      d.roadSection.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.defectType.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <aside
      className={`w-full lg:w-96 bg-surface border-t lg:border-t-0 lg:border-l border-border flex flex-col h-full overflow-hidden shadow-subtle ${className}`}
      aria-label="Survey inspection sidebar"
    >
      {/* Sidebar Header */}
      <div className="p-4 border-b border-border bg-surface-subtle/70">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-forest" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-charcoal-900">
              Survey Telemetry Feed
            </h2>
          </div>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface border border-border text-charcoal-500">
            0 DEFECTS
          </span>
        </div>

        {/* Tab switchers */}
        <div className="grid grid-cols-2 gap-1 p-0.5 bg-canvas border border-border rounded text-xs font-mono">
          <button
            type="button"
            onClick={() => setActiveTab('defects')}
            className={`py-1.5 rounded transition-all font-medium ${
              activeTab === 'defects'
                ? 'bg-surface text-charcoal-900 shadow-xs'
                : 'text-charcoal-500 hover:text-charcoal-800'
            }`}
          >
            Defects (0)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('metadata')}
            className={`py-1.5 rounded transition-all font-medium ${
              activeTab === 'metadata'
                ? 'bg-surface text-charcoal-900 shadow-xs'
                : 'text-charcoal-500 hover:text-charcoal-800'
            }`}
          >
            Survey Metadata
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="p-3 border-b border-border bg-surface">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-charcoal-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search road section, chainage..."
            className="w-full pl-8 pr-3 py-1.5 bg-canvas border border-border rounded text-xs text-charcoal-800 placeholder-charcoal-400 focus:outline-none focus:border-terracotta focus:ring-1 focus:ring-terracotta"
          />
        </div>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {selectedDefect ? (
          /* Detailed Defect Inspector View */
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <StatusBadge severity={selectedDefect.severity} />
                <span className="text-xs font-mono font-bold text-charcoal-800">
                  {selectedDefect.id}
                </span>
              </div>
              <button
                type="button"
                onClick={() => onSelectDefect && onSelectDefect(null)}
                className="p-1 rounded text-charcoal-400 hover:text-charcoal-700 hover:bg-surface-subtle"
                title="Close Inspector"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[10px] font-mono text-charcoal-400 uppercase">Road Section</label>
                <div className="text-sm font-semibold text-charcoal-900">{selectedDefect.roadSection}</div>
              </div>

              <div className="grid grid-cols-2 gap-2 p-3 bg-surface-subtle rounded border border-border/80 font-mono text-xs">
                <div>
                  <span className="text-charcoal-400 block text-[10px]">DEFECT TYPE</span>
                  <span className="font-medium capitalize text-charcoal-800">
                    {selectedDefect.defectType.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="text-charcoal-400 block text-[10px]">MEASURED DEPTH</span>
                  <span className="font-medium text-charcoal-800">
                    {selectedDefect.depthMm ? `${selectedDefect.depthMm} mm` : '—'}
                  </span>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-mono text-charcoal-400 uppercase">Geographic Fix (WGS84)</label>
                <div className="font-mono text-xs text-charcoal-700 flex items-center gap-1.5 mt-0.5">
                  <MapPin className="w-3.5 h-3.5 text-terracotta" />
                  <span>{selectedDefect.latitude.toFixed(6)}, {selectedDefect.longitude.toFixed(6)}</span>
                </div>
              </div>
            </div>
          </div>
        ) : activeTab === 'defects' ? (
          <DefectList
            defects={filteredDefects}
            selectedDefectId={selectedDefect ? (selectedDefect as Defect).id : null}
            onSelectDefect={onSelectDefect}
            severityFilter={severityFilter}
            onSeverityFilterChange={onSeverityFilterChange}
          />
        ) : (
          /* Survey Metadata Tab */
          <div className="p-4 space-y-4 overflow-y-auto text-xs font-sans">
            <div className="space-y-1">
              <h3 className="font-semibold text-charcoal-900 text-sm">
                Survey Configuration
              </h3>
              <p className="text-charcoal-500 text-xs">
                Spatial reference system and sensor calibration parameters.
              </p>
            </div>

            <div className="space-y-2.5 font-mono text-xs">
              <div className="p-2.5 bg-canvas border border-border rounded flex items-center justify-between">
                <span className="text-charcoal-500">Datum:</span>
                <span className="font-semibold text-charcoal-800">WGS84 (EPSG:4326)</span>
              </div>
              <div className="p-2.5 bg-canvas border border-border rounded flex items-center justify-between">
                <span className="text-charcoal-500">Projection:</span>
                <span className="font-semibold text-charcoal-800">UTM Zone 43N</span>
              </div>
              <div className="p-2.5 bg-canvas border border-border rounded flex items-center justify-between">
                <span className="text-charcoal-500">Sensor Type:</span>
                <span className="font-semibold text-charcoal-800">Calibrated Stereo EO / LiDAR</span>
              </div>
              <div className="p-2.5 bg-canvas border border-border rounded flex items-center justify-between">
                <span className="text-charcoal-500">Telemetry Stream:</span>
                <span className="text-forest font-semibold">Active Listening</span>
              </div>
            </div>

            <div className="p-3 bg-surface-subtle border border-border rounded space-y-1.5">
              <div className="flex items-center gap-1.5 font-mono font-semibold text-charcoal-700 text-[11px]">
                <Info className="w-3.5 h-3.5 text-terracotta" />
                <span>Operational Pipeline Status</span>
              </div>
              <p className="text-[11px] text-charcoal-500 leading-relaxed">
                Connect external drone telemetry or vehicle-mounted sensor units to begin automated defect attribution and PCI score computation.
              </p>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
