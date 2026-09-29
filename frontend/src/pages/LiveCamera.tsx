import React, { useEffect, useRef, useState } from 'react';
import {
  Camera,
  Radio,
  Wifi,
  MapPin,
  Gauge,
  Satellite,
  Activity,
  AlertTriangle,
  Maximize2,
  Video,
  VideoOff,
} from 'lucide-react';

export const LiveCamera: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [fullscreen, setFullscreen] = useState(false);

  /* ================================================= */
  /* START BROWSER CAMERA                              */
  /* ================================================= */

  const startCamera = async () => {
    try {
      setCameraError('');

      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError(
          'Camera access is not supported by this browser.'
        );
        return;
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            width: {
              ideal: 1280,
            },
            height: {
              ideal: 720,
            },
            facingMode: 'environment',
          },
          audio: false,
        });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setCameraActive(true);
    } catch (error) {
      console.error('Camera error:', error);

      setCameraActive(false);

      if (
        error instanceof DOMException &&
        error.name === 'NotAllowedError'
      ) {
        setCameraError(
          'Camera permission was denied. Please allow camera access in your browser.'
        );
      } else if (
        error instanceof DOMException &&
        error.name === 'NotFoundError'
      ) {
        setCameraError(
          'No camera was found on this device.'
        );
      } else {
        setCameraError(
          'Unable to access the camera.'
        );
      }
    }
  };

  /* ================================================= */
  /* STOP CAMERA                                       */
  /* ================================================= */

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current
        .getTracks()
        .forEach((track) => track.stop());

      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraActive(false);
  };

  /* ================================================= */
  /* CLEANUP                                           */
  /* ================================================= */

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) => track.stop());
      }
    };
  }, []);

  /* ================================================= */
  /* FULLSCREEN                                        */
  /* ================================================= */

  const toggleFullscreen = () => {
    setFullscreen((prev) => !prev);
  };

  return (
    <div className="w-full min-h-screen bg-canvas">

      {/* ================================================= */}
      {/* HEADER                                            */}
      {/* ================================================= */}

      <div className="border-b border-border bg-surface">

        <div className="mx-auto max-w-[1600px] px-5 py-5 md:px-8">

          <div className="flex flex-wrap items-end justify-between gap-4">

            <div>

              <div className="flex items-center gap-2 mb-2">

                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-terracotta/10 border border-terracotta/20">

                  <Camera
                    className="w-4 h-4 text-terracotta"
                  />

                </div>

                <span className="text-[10px] uppercase tracking-[0.18em] text-charcoal-500 font-medium">
                  Field Camera
                </span>

              </div>

              <h1 className="text-3xl md:text-4xl font-light tracking-tight text-charcoal-900">
                Live Camera
                <span className="text-terracotta">
                  {' '}Feed
                </span>
              </h1>

              <p className="mt-2 text-sm text-charcoal-500">
                Real-time camera feed for pothole detection.
              </p>

            </div>

            {/* STATUS */}

            <div
              className={`flex items-center gap-2 rounded-lg border px-3 py-2 ${
                cameraActive
                  ? 'border-forest/30 bg-forest/5'
                  : 'border-border bg-surface'
              }`}
            >

              <span
                className={`w-2 h-2 rounded-full ${
                  cameraActive
                    ? 'bg-forest animate-pulse'
                    : 'bg-charcoal-400'
                }`}
              />

              <span
                className={`text-[11px] font-medium ${
                  cameraActive
                    ? 'text-forest'
                    : 'text-charcoal-500'
                }`}
              >
                {cameraActive
                  ? 'CAMERA ONLINE'
                  : 'CAMERA OFFLINE'}
              </span>

            </div>

          </div>

        </div>

      </div>

      {/* ================================================= */}
      {/* MAIN                                             */}
      {/* ================================================= */}

      <main className="mx-auto max-w-[1600px] px-5 py-6 md:px-8">

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">

          {/* ================================================= */}
          {/* CAMERA                                           */}
          {/* ================================================= */}

          <section className="relative overflow-hidden rounded-xl border border-border bg-black shadow-card">

            {/* CAMERA TOP BAR */}

            <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-4 py-3 bg-black/60 backdrop-blur-sm">

              <div className="flex items-center gap-2">

                <Radio
                  className={`w-3.5 h-3.5 ${
                    cameraActive
                      ? 'text-forest'
                      : 'text-charcoal-400'
                  }`}
                />

                <span className="text-[11px] text-white/80 font-mono">
                 CAMERA 01
                </span>

              </div>

              <div className="flex items-center gap-3">

                <span className="text-[10px] text-white/50 font-mono">
                  {cameraActive
                    ? 'STREAM ACTIVE'
                    : 'NO SIGNAL'}
                </span>

                <button
                  type="button"
                  onClick={toggleFullscreen}
                  className="p-1.5 rounded-md bg-white/10 hover:bg-white/20 transition-colors"
                >
                  <Maximize2
                    className="w-3.5 h-3.5 text-white"
                  />
                </button>

              </div>

            </div>

            {/* ================================================= */}
            {/* VIDEO                                            */}
            {/* ================================================= */}

            <div
              className={`relative flex items-center justify-center bg-[#101010] ${
                fullscreen
                  ? 'fixed inset-0 z-[100] w-screen h-screen'
                  : 'aspect-video'
              }`}
            >

              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-contain"
              />

              {/* CAMERA OFF / ERROR */}

              {!cameraActive && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#101010]">

                  <div className="flex flex-col items-center gap-4 text-center max-w-sm px-6">

                    <div className="flex items-center justify-center w-14 h-14 rounded-full border border-border bg-surface">

                      {cameraError ? (
                        <VideoOff className="w-6 h-6 text-charcoal-400" />
                      ) : (
                        <Camera className="w-6 h-6 text-charcoal-400" />
                      )}

                    </div>

                    <div>

                      <p className="text-sm text-white/80 font-medium">
                        {cameraError
                          ? 'Camera unavailable'
                          : 'Camera not started'}
                      </p>

                      <p className="mt-1 text-[11px] text-white/40">
                        {cameraError ||
                          'Start the browser camera to begin the live feed.'}
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={startCamera}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-terracotta text-white text-xs font-medium hover:bg-terracotta/90 transition-colors"
                    >
                      <Video className="w-3.5 h-3.5" />
                      Start Camera
                    </button>

                  </div>

                </div>
              )}

              {/* LIVE INDICATOR */}

              {cameraActive && (
                <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded-md bg-black/60 backdrop-blur-sm px-2.5 py-1.5">

                  <span className="relative flex w-1.5 h-1.5">

                    <span className="absolute inline-flex w-full h-full rounded-full bg-red-500 animate-ping opacity-75" />

                    <span className="relative inline-flex w-1.5 h-1.5 rounded-full bg-red-500" />

                  </span>

                  <span className="text-[9px] text-white font-mono tracking-wider">
                    LIVE
                  </span>

                </div>
              )}

            </div>

          </section>

          {/* ================================================= */}
          {/* RIGHT SIDEBAR                                    */}
          {/* ================================================= */}

          <aside className="space-y-4">

            {/* CAMERA STATUS */}

            <div className="rounded-xl border border-border bg-surface overflow-hidden">

              <div className="px-4 py-3 border-b border-border">

                <h2 className="text-sm font-medium text-charcoal-800">
                  Camera Status
                </h2>

                <p className="mt-0.5 text-[10px] text-charcoal-400">
                  Current camera state
                </p>

              </div>

              <div className="p-4 space-y-4">

                <StatusRow
                  icon={<Camera size={13} />}
                  label="Camera"
                  value={
                    cameraActive
                      ? 'Connected'
                      : 'Disconnected'
                  }
                  ok={cameraActive}
                />

                <StatusRow
                  icon={<Wifi size={13} />}
                  label="Stream"
                  value={
                    cameraActive
                      ? 'Active'
                      : 'No signal'
                  }
                  ok={cameraActive}
                />

                <StatusRow
                  icon={<Activity size={13} />}
                  label="Pipeline"
                  value="Ready"
                  ok={true}
                />

              </div>

            </div>

            {/* CONTROLS */}

            <div className="rounded-xl border border-border bg-surface overflow-hidden">

              <div className="px-4 py-3 border-b border-border">

                <h2 className="text-sm font-medium text-charcoal-800">
                  Camera Controls
                </h2>

                <p className="mt-0.5 text-[10px] text-charcoal-400">
                  Demo camera controls
                </p>

              </div>

              <div className="p-4">

                {!cameraActive ? (
                  <button
                    type="button"
                    onClick={startCamera}
                    className="w-full flex items-center justify-center gap-2 rounded-lg bg-terracotta px-4 py-2.5 text-xs font-medium text-white hover:bg-terracotta/90 transition-colors"
                  >
                    <Video className="w-3.5 h-3.5" />
                    Start Camera
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="w-full flex items-center justify-center gap-2 rounded-lg border border-border bg-canvas px-4 py-2.5 text-xs font-medium text-charcoal-700 hover:bg-charcoal-50 transition-colors"
                  >
                    <VideoOff className="w-3.5 h-3.5" />
                    Stop Camera
                  </button>
                )}

              </div>

            </div>

            {/* GPS */}

            <div className="rounded-xl border border-border bg-surface overflow-hidden">

              <div className="px-4 py-3 border-b border-border">

                <h2 className="text-sm font-medium text-charcoal-800">
                  GPS Status
                </h2>

                <p className="mt-0.5 text-[10px] text-charcoal-400">
                  Inspection vehicle position
                </p>

              </div>

              <div className="p-4 space-y-4">

                <StatusRow
                  icon={<Satellite size={13} />}
                  label="GPS link"
                  value="Waiting"
                  ok={false}
                />

                <StatusRow
                  icon={<MapPin size={13} />}
                  label="Latitude"
                  value="—"
                  ok={false}
                />

                <StatusRow
                  icon={<MapPin size={13} />}
                  label="Longitude"
                  value="—"
                  ok={false}
                />

              </div>

            </div>

            {/* AI */}

            <div className="rounded-xl border border-border bg-surface overflow-hidden">

              <div className="px-4 py-3 border-b border-border">

                <h2 className="text-sm font-medium text-charcoal-800">
                  AI Detection
                </h2>

              </div>

              <div className="p-4">

                <div className="flex items-center gap-3 rounded-lg border border-border bg-canvas p-3">

                  <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-charcoal-100">

                    <AlertTriangle
                      className="w-4 h-4 text-charcoal-400"
                    />

                  </div>

                  <div>

                    <p className="text-[11px] font-medium text-charcoal-700">
                      No detection data
                    </p>

                    <p className="mt-0.5 text-[10px] text-charcoal-400">
                      AI results will appear here
                    </p>

                  </div>

                </div>

              </div>

            </div>

          </aside>

        </div>

      </main>

    </div>
  );
};

/* ================================================= */
/* STATUS ROW                                       */
/* ================================================= */

interface StatusRowProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  ok: boolean;
}

const StatusRow: React.FC<StatusRowProps> = ({
  icon,
  label,
  value,
  ok,
}) => {
  return (
    <div className="flex items-center gap-3">

      <span className="text-charcoal-400">
        {icon}
      </span>

      <span className="flex-1 text-[11px] text-charcoal-500">
        {label}
      </span>

      <span
        className={`flex items-center gap-1.5 text-[11px] font-medium ${
          ok
            ? 'text-forest'
            : 'text-charcoal-400'
        }`}
      >

        <span
          className={`w-1.5 h-1.5 rounded-full ${
            ok
              ? 'bg-forest'
              : 'bg-charcoal-300'
          }`}
        />

        {value}

      </span>

    </div>
  );
};