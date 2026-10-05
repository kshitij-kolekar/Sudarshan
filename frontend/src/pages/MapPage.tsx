import React from 'react';
import { MapView } from '../components/map/MapView';
import { MapSidebar } from '../components/map/MapSidebar';
import { useDefects } from '../hooks/useDefects';

export const MapPage: React.FC = () => {
  const {
    data: defects,
    selectedDefect,
    setSelectedDefectId,
    severityFilter,
    setSeverityFilter,
  } = useDefects();

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-canvas">
     

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
