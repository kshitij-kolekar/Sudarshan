import React from 'react';
import { MapView } from '../components/map/MapView';
import { MapSidebar } from '../components/map/MapSidebar';
import { useDefects } from '../hooks/useDefects';
import { Compass, RefreshCw } from 'lucide-react';

export const MapPage: React.FC = () => {
  const {
    data: defects,
    selectedDefect,
    setSelectedDefectId,
    severityFilter,
    setSeverityFilter,
    refetch,
    isLoading,
  } = useDefects();

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-canvas">
      {/* Top Field Operations HUD Strip */}
      <div className="border-b border-border bg-surface px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-charcoal-900 uppercase tracking-wider">
            <Compass className="w-4 h-4 text-terracotta" />
            <span>Survey Map</span>
          </div>
          <span className="text-charcoal-300">/</span>
          <span className="text-xs text-charcoal-500 font-mono">
            CADASTRE & FIELD TELEMETRY
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="hidden sm:flex items-center gap-2 text-charcoal-500">
            <span>SURVEY LAYER:</span>
            <span className="text-charcoal-800 font-semibold">ORTHO-CAD VECTOR</span>
          </div>

          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-subtle border border-border text-charcoal-700 hover:text-charcoal-900 hover:bg-canvas transition-colors"
            title="Poll survey data stream"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin text-terracotta' : ''}`} />
            <span>SYNC FEED</span>
          </button>
        </div>
      </div>

      {/* Main Map Workspace (Desktop: Map Left, Sidebar Right; Mobile: Map top, Sidebar below) */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0 relative">
        {/* Left: Map View */}
        <div className="flex-1 min-h-[460px] lg:min-h-0 relative">
          <MapView
            defects={defects}
            selectedDefect={selectedDefect}
            onSelectDefect={(d) => setSelectedDefectId(d.id)}
          />
        </div>

        {/* Right: Inspection Sidebar */}
        <MapSidebar
          defects={defects}
          selectedDefect={selectedDefect}
          onSelectDefect={(d) => setSelectedDefectId(d ? d.id : null)}
          severityFilter={severityFilter}
          onSeverityFilterChange={setSeverityFilter}
        />
      </div>
    </div>
  );
};
