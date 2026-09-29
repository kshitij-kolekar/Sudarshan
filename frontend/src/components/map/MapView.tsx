import React, { useEffect, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

import { MapControls, MapLayerMode } from './MapControls';
import { MapLegend } from './MapLegend';
import { Defect } from '../../types';
import { Compass } from 'lucide-react';

interface MapViewProps {
  defects?: Defect[];
  selectedDefect?: Defect | null;
  onSelectDefect?: (defect: Defect) => void;
  className?: string;
}

/* ================================================= */
/* MAP CENTER UPDATER                                */
/* ================================================= */

const MapCenterUpdater: React.FC<{ defects: Defect[] }> = ({
  defects,
}) => {
  const map = useMap();

  useEffect(() => {
    if (!defects || defects.length === 0) {
      return;
    }

    const validCoordinates = defects
      .map((defect) => ({
        latitude: Number(defect.latitude),
        longitude: Number(defect.longitude),
      }))
      .filter(
        (coordinate) =>
          Number.isFinite(coordinate.latitude) &&
          Number.isFinite(coordinate.longitude) &&
          coordinate.latitude >= -90 &&
          coordinate.latitude <= 90 &&
          coordinate.longitude >= -180 &&
          coordinate.longitude <= 180
      );

    console.log(
      'VALID MAP COORDINATES:',
      validCoordinates
    );

    if (validCoordinates.length === 0) {
      console.error(
        'No valid latitude/longitude found in defects'
      );
      return;
    }

    const latitude =
      validCoordinates.reduce(
        (sum, coordinate) =>
          sum + coordinate.latitude,
        0
      ) / validCoordinates.length;

    const longitude =
      validCoordinates.reduce(
        (sum, coordinate) =>
          sum + coordinate.longitude,
        0
      ) / validCoordinates.length;

    console.log('MOVING MAP TO:', {
      latitude,
      longitude,
    });

    map.setView(
      [latitude, longitude],
      13,
      {
        animate: false,
      }
    );
  }, [map, defects]);

  return null;
};

/* ================================================= */
/* DEFECT MARKER ICON                               */
/* ================================================= */

const createDefectIcon = (severity: string) => {
  let color = '#64748b';

  switch (severity?.toLowerCase()) {
    case 'critical':
      color = '#dc2626';
      break;

    case 'high':
      color = '#f97316';
      break;

    case 'medium':
      color = '#f59e0b';
      break;

    case 'low':
      color = '#64748b';
      break;

    default:
      color = '#64748b';
  }

  return L.divIcon({
    className: '',
    html: `
      <div
        style="
          width:18px;
          height:18px;
          background:${color};
          border:3px solid white;
          border-radius:50%;
          box-shadow:0 2px 6px rgba(0,0,0,0.35);
        "
      ></div>
    `,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -10],
  });
};

/* ================================================= */
/* MAP VIEW                                          */
/* ================================================= */

export const MapView: React.FC<MapViewProps> = ({
  defects = [],
  selectedDefect = null,
  onSelectDefect,
  className = '',
}) => {
  const [zoom, setZoom] = useState(1);

  const [currentLayer, setCurrentLayer] =
    useState<MapLayerMode>('vector');

  const [showGrid, setShowGrid] = useState(true);

  const [showCrosshairs, setShowCrosshairs] =
    useState(true);

  const [mousePos, setMousePos] = useState({
    lat: 19.0760,
    lon: 72.8777,
    x: 0,
    y: 0,
  });

  /* ================================================= */
  /* MAP CONTROLS                                      */
  /* ================================================= */

  const handleZoomIn = () => {
    setZoom((prev) =>
      Math.min(prev + 0.5, 4)
    );
  };

  const handleZoomOut = () => {
    setZoom((prev) =>
      Math.max(prev - 0.5, 0.5)
    );
  };

  const handleResetLocation = () => {
    setZoom(1);
  };

  /* ================================================= */
  /* MOUSE POSITION                                    */
  /* ================================================= */

  const handleMouseMove = (
    e: React.MouseEvent<HTMLDivElement>
  ) => {
    const rect =
      e.currentTarget.getBoundingClientRect();

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    /*
     * These are only used for the coordinate HUD.
     * The actual map position comes from Leaflet GPS
     * coordinates.
     */

    const lat =
      19.0760 +
      (rect.height / 2 - y) * 0.00015;

    const lon =
      72.8777 +
      (x - rect.width / 2) * 0.00015;

    setMousePos({
      lat,
      lon,
      x,
      y,
    });
  };

  return (
    <div
      className={`relative w-full h-full min-h-[500px] lg:min-h-[600px] bg-canvas overflow-hidden select-none border-b lg:border-b-0 border-border ${className}`}
      onMouseMove={handleMouseMove}
    >

      {/* ================================================= */}
      {/* REAL OPENSTREETMAP MAP                            */}
      {/* ================================================= */}

      <div className="absolute inset-0 z-0">

        <MapContainer
          /*
           * Mumbai fallback.
           *
           * Once defects arrive from the API,
           * MapCenterUpdater moves the map to the
           * actual pothole coordinates.
           */
          center={[19.0760, 72.8777]}
          zoom={13}
          minZoom={5}
          maxZoom={19}
          scrollWheelZoom={true}
          zoomControl={false}
          style={{
            width: '100%',
            height: '100%',
          }}
        >

          {/* ================================================= */}
          {/* AUTOMATIC POTHOLE CENTERING                       */}
          {/* ================================================= */}

          <MapCenterUpdater defects={defects} />

          {/* ================================================= */}
          {/* OPENSTREETMAP TILES                              */}
          {/* ================================================= */}

          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap contributors"
            maxZoom={19}
          />

          {/* ================================================= */}
          {/* POTHOLE MARKERS                                  */}
          {/* ================================================= */}

          {defects.map((defect) => {

            const latitude = Number(
              defect.latitude
            );

            const longitude = Number(
              defect.longitude
            );

            /*
             * Don't render a marker if the backend
             * returned invalid coordinates.
             */

            if (
              !Number.isFinite(latitude) ||
              !Number.isFinite(longitude) ||
              latitude < -90 ||
              latitude > 90 ||
              longitude < -180 ||
              longitude > 180
            ) {
              return null;
            }

            return (
              <Marker
                key={defect.id}
                position={[
                  latitude,
                  longitude,
                ]}
                icon={createDefectIcon(
                  defect.severity
                )}
                eventHandlers={{
                  click: () => {
                    onSelectDefect?.(
                      defect
                    );
                  },
                }}
              >

                <Popup>

                  <div className="text-sm">

                    <div className="font-semibold mb-2">
                      Pothole
                    </div>

                    <div>
                      <strong>
                        Severity:
                      </strong>{' '}
                      {defect.severity}
                    </div>

                    <div>
                      <strong>
                        Depth:
                      </strong>{' '}
                      {defect.depth}
                    </div>

                    <div>
                      <strong>
                        Area:
                      </strong>{' '}
                      {defect.area}
                    </div>

                    <div>
                      <strong>
                        Material:
                      </strong>{' '}
                      {defect.material}
                    </div>

                    <div>
                      <strong>
                        Latitude:
                      </strong>{' '}
                      {latitude.toFixed(6)}
                    </div>

                    <div>
                      <strong>
                        Longitude:
                      </strong>{' '}
                      {longitude.toFixed(6)}
                    </div>

                  </div>

                </Popup>

              </Marker>
            );
          })}

        </MapContainer>

      </div>

      {/* ================================================= */}
      {/* CADASTRAL GRID                                    */}
      {/* ================================================= */}

      {showGrid && (
        <div
          className={`absolute inset-0 z-10 pointer-events-none ${
            currentLayer === 'vector'
              ? 'bg-cad-grid opacity-20'
              : 'bg-cad-grid-dense opacity-15'
          }`}
        />
      )}

      {/* ================================================= */}
      {/* DEFECT MARKERS                                    */}
      {/* ================================================= */}

      {defects.length > 0 && (
        <div className="absolute inset-0 z-20 pointer-events-none">
          {/*
            Actual geographic markers are rendered
            inside the Leaflet MapContainer above.
          */}
        </div>
      )}

      {/* ================================================= */}
      {/* CENTER CROSSHAIRS                                 */}
      {/* ================================================= */}

      {showCrosshairs && (
        <div className="absolute inset-0 z-20 pointer-events-none flex items-center justify-center">

          <div className="relative w-12 h-12">

            <div className="absolute inset-x-0 top-1/2 h-[1px] bg-charcoal-400/40 -translate-y-1/2" />

            <div className="absolute inset-y-0 left-1/2 w-[1px] bg-charcoal-400/40 -translate-x-1/2" />

            <div className="absolute inset-2 border border-charcoal-400/30 rounded-full" />

          </div>

        </div>
      )}

      {/* ================================================= */}
      {/* MAP CONTROLS                                     */}
      {/* ================================================= */}

      <div className="absolute top-4 left-4 z-30">

        <MapControls
          zoom={zoom}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onResetLocation={handleResetLocation}
          currentLayer={currentLayer}
          onLayerChange={setCurrentLayer}
          showGrid={showGrid}
          onToggleGrid={() =>
            setShowGrid(!showGrid)
          }
          showCrosshairs={showCrosshairs}
          onToggleCrosshairs={() =>
            setShowCrosshairs(
              !showCrosshairs
            )
          }
        />

      </div>

      {/* ================================================= */}
      {/* MAP LEGEND                                       */}
      {/* ================================================= */}

      <div className="absolute bottom-4 left-4 z-30">
        <MapLegend />
      </div>

      {/* ================================================= */}
      {/* COORDINATE HUD                                   */}
      {/* ================================================= */}

      <div className="absolute top-4 right-4 z-30 pointer-events-none hidden sm:flex items-center gap-2 bg-surface/95 backdrop-blur-md border border-border px-3 py-1.5 rounded-lg shadow-card text-[11px] font-mono text-charcoal-600">

        <div className="flex items-center gap-1.5">

          <Compass className="w-3.5 h-3.5 text-terracotta" />

          <span>
            LAT: {mousePos.lat.toFixed(5)}°N
          </span>

          <span className="text-charcoal-300">
            |
          </span>

          <span>
            LON: {mousePos.lon.toFixed(5)}°E
          </span>

        </div>

        <span className="text-charcoal-300">
          |
        </span>

        <span className="text-forest font-medium">
          GPS LOCK
        </span>

      </div>

      {/* ================================================= */}
      {/* SCALE / DATUM                                    */}
      {/* ================================================= */}

      <div className="absolute bottom-4 right-4 z-30 pointer-events-none bg-surface/95 backdrop-blur-md border border-border px-3 py-1.5 rounded-lg shadow-card text-[10px] font-mono text-charcoal-500 flex items-center gap-3">

        <div className="flex items-center gap-1">

          <div className="w-12 h-1 bg-charcoal-800" />

          <span>
            250 M
          </span>

        </div>

        <span className="text-charcoal-300">
          •
        </span>

        <span>
          EPSG:4326
        </span>

        <span className="text-charcoal-300">
          •
        </span>

        <span>
          1:5,000
        </span>

      </div>

    </div>
  );
};