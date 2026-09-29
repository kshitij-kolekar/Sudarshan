import React, { useState } from 'react';
import { 
  Plus, 
  Minus, 
  Crosshair, 
  Layers, 
  SlidersHorizontal, 
  Check
} from 'lucide-react';

export type MapLayerMode = 'vector' | 'ortho' | 'contour';

interface MapControlsProps {
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetLocation: () => void;
  currentLayer: MapLayerMode;
  onLayerChange: (layer: MapLayerMode) => void;
  showGrid: boolean;
  onToggleGrid: () => void;
  showCrosshairs: boolean;
  onToggleCrosshairs: () => void;
}

export const MapControls: React.FC<MapControlsProps> = ({
  zoom,
  onZoomIn,
  onZoomOut,
  onResetLocation,
  currentLayer,
  onLayerChange,
  showGrid,
  onToggleGrid,
  showCrosshairs,
  onToggleCrosshairs,
}) => {
  const [layersOpen, setLayersOpen] = useState(false);
  const [optionsOpen, setOptionsOpen] = useState(false);

  const layerOptions: { id: MapLayerMode; label: string; desc: string }[] = [
    { id: 'vector', label: 'Vector Cadastral', desc: 'Road right-of-way & centerline geometry' },
    { id: 'ortho', label: 'Aerial Orthomosaic', desc: 'High-res multispectral survey imagery' },
    { id: 'contour', label: 'LIDAR Topography', desc: 'Elevation isocontours & slope gradients' },
  ];

  return (
    <div className="absolute top-4 left-4 z-20 flex flex-col gap-2 pointer-events-auto">
      {/* Zoom Controls Card */}
      <div className="bg-surface/95 backdrop-blur-md border border-border rounded-lg shadow-card p-1 flex flex-col items-center">
        <button
          type="button"
          onClick={onZoomIn}
          className="p-2 rounded text-charcoal-700 hover:text-charcoal-900 hover:bg-surface-subtle transition-colors focus:outline-none focus:ring-1 focus:ring-terracotta"
          title="Zoom In"
          aria-label="Zoom in"
        >
          <Plus className="w-4 h-4" />
        </button>

        <div className="w-6 h-[1px] bg-border my-0.5" />

        <div className="text-[10px] font-mono text-charcoal-500 font-semibold px-1 py-0.5 select-none">
          {zoom}x
        </div>

        <div className="w-6 h-[1px] bg-border my-0.5" />

        <button
          type="button"
          onClick={onZoomOut}
          className="p-2 rounded text-charcoal-700 hover:text-charcoal-900 hover:bg-surface-subtle transition-colors focus:outline-none focus:ring-1 focus:ring-terracotta"
          title="Zoom Out"
          aria-label="Zoom out"
        >
          <Minus className="w-4 h-4" />
        </button>
      </div>

      {/* Geolocation / Target Recenter */}
      <div className="bg-surface/95 backdrop-blur-md border border-border rounded-lg shadow-card p-1">
        <button
          type="button"
          onClick={onResetLocation}
          className="p-2 rounded text-charcoal-700 hover:text-charcoal-900 hover:bg-surface-subtle transition-colors focus:outline-none focus:ring-1 focus:ring-terracotta flex items-center justify-center"
          title="Reset to Survey Base Datum"
          aria-label="Current location"
        >
          <Crosshair className="w-4 h-4 text-terracotta" />
        </button>
      </div>

      {/* Layer Selector & Map Options Menus */}
      <div className="relative">
        <div className="bg-surface/95 backdrop-blur-md border border-border rounded-lg shadow-card p-1 flex flex-col gap-1">
          <button
            type="button"
            onClick={() => {
              setLayersOpen(!layersOpen);
              setOptionsOpen(false);
            }}
            className={`p-2 rounded transition-colors focus:outline-none focus:ring-1 focus:ring-terracotta ${
              layersOpen ? 'bg-surface-subtle text-terracotta' : 'text-charcoal-700 hover:bg-surface-subtle'
            }`}
            title="Layer Switcher"
            aria-label="Map layers"
          >
            <Layers className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={() => {
              setOptionsOpen(!optionsOpen);
              setLayersOpen(false);
            }}
            className={`p-2 rounded transition-colors focus:outline-none focus:ring-1 focus:ring-terracotta ${
              optionsOpen ? 'bg-surface-subtle text-terracotta' : 'text-charcoal-700 hover:bg-surface-subtle'
            }`}
            title="Map Display Options"
            aria-label="Map options"
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        </div>

        {/* Layers Flyout */}
        {layersOpen && (
          <div className="absolute left-12 top-0 w-64 bg-surface border border-border rounded-lg shadow-elevated p-3 z-30 space-y-2">
            <div className="text-[11px] font-mono font-semibold text-charcoal-500 uppercase tracking-wider">
              Basemap Layers
            </div>
            <div className="space-y-1">
              {layerOptions.map((layer) => (
                <button
                  key={layer.id}
                  onClick={() => {
                    onLayerChange(layer.id);
                    setLayersOpen(false);
                  }}
                  className={`w-full text-left p-2 rounded text-xs flex items-start justify-between transition-colors ${
                    currentLayer === layer.id
                      ? 'bg-surface-subtle text-charcoal-900 border border-border font-medium'
                      : 'text-charcoal-600 hover:bg-canvas hover:text-charcoal-900'
                  }`}
                >
                  <div>
                    <div className="font-sans font-medium text-xs">{layer.label}</div>
                    <div className="text-[10px] text-charcoal-400 mt-0.5">{layer.desc}</div>
                  </div>
                  {currentLayer === layer.id && (
                    <Check className="w-3.5 h-3.5 text-terracotta shrink-0 mt-0.5" />
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Options Flyout */}
        {optionsOpen && (
          <div className="absolute left-12 top-10 w-56 bg-surface border border-border rounded-lg shadow-elevated p-3 z-30 space-y-2">
            <div className="text-[11px] font-mono font-semibold text-charcoal-500 uppercase tracking-wider">
              Display Overlays
            </div>
            <div className="space-y-1.5 text-xs">
              <label className="flex items-center justify-between p-1.5 rounded hover:bg-surface-subtle cursor-pointer select-none">
                <span className="text-charcoal-700 font-sans">Cadastral Grid</span>
                <input
                  type="checkbox"
                  checked={showGrid}
                  onChange={onToggleGrid}
                  className="rounded border-border text-terracotta focus:ring-terracotta h-3.5 w-3.5"
                />
              </label>
              <label className="flex items-center justify-between p-1.5 rounded hover:bg-surface-subtle cursor-pointer select-none">
                <span className="text-charcoal-700 font-sans">Survey Crosshair</span>
                <input
                  type="checkbox"
                  checked={showCrosshairs}
                  onChange={onToggleCrosshairs}
                  className="rounded border-border text-terracotta focus:ring-terracotta h-3.5 w-3.5"
                />
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
