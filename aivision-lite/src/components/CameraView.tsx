import React, { useRef, useState, useEffect } from "react";
import { Camera, ImageUp, Sparkles, AlertTriangle, Eye, ShieldCheck, HelpCircle } from "lucide-react";
import { PresetScenario } from "../types";
import { PRESET_SCENARIOS } from "../data/presets";

// Auto-detect real camera specifications via MediaDevices API
export async function detectCameraSpecifications(stream?: MediaStream | null) {
  const result = { brand: "Unknown Camera", sensor: "Unknown Sensor", res: "Unknown Resolution", status: "كاميرا مجهولة", peakZoom: "Unknown Zoom" };
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cams = devices.filter(d => d.kind === "videoinput");
    if (cams.length > 0) result.brand = cams[0].label || `Camera ${cams[0].deviceId.slice(0,8)}`;
    if (stream) {
      const track = stream.getVideoTracks()[0];
      if (track) {
        const settings = track.getSettings();
        if (settings.width && settings.height) result.res = `${settings.width}×${settings.height}`;
        const caps = (track as any).getCapabilities?.();
        if (caps?.zoom) result.peakZoom = `${caps.zoom.max?.toFixed(1) || "?"}x optical`;
        result.sensor = track.label || "Video Track";
        result.status = `${result.brand} — ${result.res}`;
      }
    }
  } catch {}
  return result;
}

// Define safe physical orbital movement paths for each premium target preset
export function getTargetPosition(id: string, index: number, time: number, width: number, height: number) {
  // Use unique sin/cos frequency and radius so they float around beautifully
  const angle = (time / 2000) + (index * Math.PI / 3.5);
  // Keep targets inside canvas area (which is 640 x 480)
  const rx = 160 + (index % 3) * 30; // X radius
  const ry = 110 + (index % 2) * 20;  // Y radius
  
  // Center is the canvas center
  const cx = width / 2;
  const cy = height / 2;
  
  return {
    x: cx + Math.sin(angle) * rx - 25,
    y: cy + Math.cos(angle * 1.3) * ry - 25,
    w: 50,
    h: 50
  };
}

interface CameraViewProps {
  selectedPreset: PresetScenario | null;
  onImageCaptured: (base64: string, nameHint: string, forensicMode?: boolean) => void;
  isScanning: boolean;
  filterMode: "normal" | "thermal" | "stealth" | "nightvision";
  setFilterMode: (mode: "normal" | "thermal" | "stealth" | "nightvision") => void;
  onSelectPreset?: (scenario: PresetScenario) => void;
}

export default function CameraView({
  selectedPreset,
  onImageCaptured,
  isScanning,
  filterMode,
  setFilterMode,
  onSelectPreset
}: CameraViewProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [useLiveCamera, setUseLiveCamera] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [laserY, setLaserY] = useState(15);
  const [laserDirection, setLaserDirection] = useState(1);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [zoomMinimized, setZoomMinimized] = useState(true);
  
  // Real motion tracking state
  const [trackMotion, setTrackMotion] = useState(false);
  const [forensicMode, setForensicMode] = useState(false);
  const motionRectRef = useRef<{x: number, y: number, w: number, h: number, active: boolean}>({ x: 0, y: 0, w: 0, h: 0, active: false });
  const motionCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const lastFrameDataRef = useRef<Uint8ClampedArray | null>(null);

  // Advanced multi-target tracking refs (Part A)
  interface TrackTarget {
    id: number;
    cx: number; cy: number;
    w: number; h: number;
    vx: number; vy: number;
    trail: Array<{x: number; y: number}>;
    dwell: number;
    frames: number;
    prevArea: number;
  }
  const trackTargetsRef = useRef<TrackTarget[]>([]);
  const nextTrackIdRef = useRef<number>(1);
  const heatCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Preset simulation trail ref
  const presetTrailRef = useRef<Map<string, Array<{x: number; y: number}>>>(new Map());

  // Thermal palette and frame-delta refs (Part B)
  const thermalPaletteRef = useRef<"ironbow" | "rainbow" | "arctic" | "whiteHot">("ironbow");
  const prevThermalLumaRef = useRef<Float32Array | null>(null);
  const prevThermalTimeRef = useRef<number>(0);

  // NVG heading ref for azimuth compass
  const nvgHeadingRef = useRef<number>(0);

  // NVG EMA refs for adaptive gain smoothing (Improvement 3)
  const nvgEmaMinRef = useRef<number>(0);
  const nvgEmaMaxRef = useRef<number>(255);

  // NVG real heading refs (Improvement 11)
  const nvgRealHeadingRef = useRef<number | null>(null);
  const nvgUseRealHeadingRef = useRef<boolean>(false);

  // Camera specs ref (Improvement 1)
  const cameraSpecsRef = useRef({ brand: "Unknown Camera", sensor: "Unknown Sensor", res: "Unknown Resolution", status: "كاميرا مجهولة", peakZoom: "Unknown Zoom" });

  // Selected blob ref for live click tracking (Improvement 7)
  const selectedBlobIdRef = useRef<number>(-1);

  useEffect(() => {
    // initialize offscreen motion canvas
    const mCan = document.createElement("canvas");
    mCan.width = 64;
    mCan.height = 48;
    motionCanvasRef.current = mCan;

    // initialize heat accumulation canvas
    const hCan = document.createElement("canvas");
    hCan.width = 640;
    hCan.height = 480;
    heatCanvasRef.current = hCan;
  }, []);

  // Laser scanner line animation loop
  useEffect(() => {
    let animId: number;
    const animateLaser = () => {
      setLaserY((prevY) => {
        let nextY = prevY + laserDirection * 1.5;
        if (nextY >= 90) {
          setLaserDirection(-1);
          return 90;
        }
        if (nextY <= 10) {
          setLaserDirection(1);
          return 10;
        }
        return nextY;
      });
      animId = requestAnimationFrame(animateLaser);
    };

    if (isScanning) {
      animId = requestAnimationFrame(animateLaser);
    }
    return () => cancelAnimationFrame(animId);
  }, [isScanning, laserDirection]);

  // Request/Toggle real webcam permission
  useEffect(() => {
    let stream: MediaStream | null = null;
    if (useLiveCamera) {
      navigator.mediaDevices
        .getUserMedia({ video: { facingMode: "environment" } })
        .then((s) => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
          setCameraError("");
        })
        .catch((err) => {
          console.warn("Camera block or error: ", err);
          setCameraError("Camera unavailable or permission denied. Falling back to digital simulation.");
          setUseLiveCamera(false);
        });
    } else {
      if (videoRef.current && videoRef.current.srcObject) {
        const s = videoRef.current.srcObject as MediaStream;
        s.getTracks().forEach((track) => track.stop());
        videoRef.current.srcObject = null;
      }
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [useLiveCamera]);

  // Update camera specs when live camera changes (Improvement 1)
  useEffect(() => {
    if (useLiveCamera) {
      const updateSpecs = async () => {
        const stream = videoRef.current?.srcObject instanceof MediaStream ? videoRef.current.srcObject as MediaStream : null;
        const specs = await detectCameraSpecifications(stream);
        cameraSpecsRef.current = specs;
      };
      const timer = setTimeout(updateSpecs, 1500); // wait for stream to initialize
      return () => clearTimeout(timer);
    }
  }, [useLiveCamera]);

  // DeviceOrientation handler for NVG real compass heading (Improvement 11)
  useEffect(() => {
    const handler = (e: DeviceOrientationEvent) => {
      if (e.alpha !== null) {
        nvgRealHeadingRef.current = e.alpha;
        nvgUseRealHeadingRef.current = true;
      }
    };
    if (typeof DeviceOrientationEvent !== 'undefined') {
      window.addEventListener('deviceorientation', handler);
    }
    return () => window.removeEventListener('deviceorientation', handler);
  }, []);

  // Clear preset trails when preset changes (Improvement 15)
  useEffect(() => {
    presetTrailRef.current.clear();
  }, [selectedPreset]);

  // Render simulation sketch on static canvas base on selected preset details
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        if (entry.target === canvas) {
          canvas.width = entry.contentRect.width;
          canvas.height = entry.contentRect.height;
        }
      }
    });
    resizeObserver.observe(canvas);

    let animId: number;

    const renderCanvas = () => {
      // Calculate centering focal coordinate
      let cx = canvas.width / 2;
      let cy = canvas.height / 2;
      
      if (trackMotion && motionRectRef.current.active && zoomLevel > 1) {
         cx = motionRectRef.current.x + motionRectRef.current.w / 2;
         cy = motionRectRef.current.y + motionRectRef.current.h / 2;
      }

      if (useLiveCamera && videoRef.current && videoRef.current.readyState >= 2) {
        const vWidth = videoRef.current.videoWidth || canvas.width;
        const vHeight = videoRef.current.videoHeight || canvas.height;
        
        // Calculate crop dimensions based on current zoom level
        const sWidth = vWidth / zoomLevel;
        const sHeight = vHeight / zoomLevel;
        
        // Center the cropped area dynamically over tracked target coordinates
        const videoCenterX = cx * (vWidth / canvas.width);
        const videoCenterY = cy * (vHeight / canvas.height);
        
        let sx = videoCenterX - sWidth / 2;
        let sy = videoCenterY - sHeight / 2;
        
        // Clamp to prevent cropping out of bounds
        sx = Math.max(0, Math.min(vWidth - sWidth, sx));
        sy = Math.max(0, Math.min(vHeight - sHeight, sy));
        
        ctx.drawImage(videoRef.current, sx, sy, sWidth, sHeight, 0, 0, canvas.width, canvas.height);
        
        // Motion Detection Algorithm — Enhanced Multi-Blob Real Tracking
        if (trackMotion && motionCanvasRef.current) {
          const mCtx = motionCanvasRef.current.getContext("2d", { willReadFrequently: true });
          if (mCtx) {
            const mW = motionCanvasRef.current.width;
            const mH = motionCanvasRef.current.height;
            mCtx.drawImage(canvas, 0, 0, mW, mH);
            const mData = mCtx.getImageData(0, 0, mW, mH);
            const pixels = mData.data;

            if (lastFrameDataRef.current) {
              // Step 1 — build motion flag map and compute global mean motion vector (camera-shake compensation)
              const motionMap = new Uint8Array(mW * mH);
              let globalDxSum = 0, globalDySum = 0, globalCount = 0;

              for (let i = 0; i < pixels.length; i += 4) {
                const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
                const lr = lastFrameDataRef.current[i], lg = lastFrameDataRef.current[i + 1], lb = lastFrameDataRef.current[i + 2];
                const diff = Math.abs(r - lr) + Math.abs(g - lg) + Math.abs(b - lb);
                const pi = i >> 2;
                if (diff > 80) {
                  motionMap[pi] = 1;
                  globalDxSum += (r - lr);
                  globalDySum += (g - lg);
                  globalCount++;
                }
              }
              const globalDx = globalCount > 0 ? globalDxSum / globalCount : 0;
              const globalDy = globalCount > 0 ? globalDySum / globalCount : 0;

              // Step 2 — simple connected-component / blob finding (up to 5 blobs)
              const visited = new Uint8Array(mW * mH);
              interface RawBlob { minX: number; minY: number; maxX: number; maxY: number; sumX: number; sumY: number; count: number; }
              const blobs: RawBlob[] = [];

              for (let pi = 0; pi < mW * mH; pi++) {
                if (!motionMap[pi] || visited[pi]) continue;
                if (blobs.length >= 5) break;

                // BFS flood fill
                const queue: number[] = [pi];
                visited[pi] = 1;
                let bMinX = mW, bMinY = mH, bMaxX = 0, bMaxY = 0, bSumX = 0, bSumY = 0, bCnt = 0;

                while (queue.length > 0) {
                  const cur = queue.pop()!;
                  const cx2 = cur % mW;
                  const cy2 = Math.floor(cur / mW);
                  bMinX = Math.min(bMinX, cx2); bMaxX = Math.max(bMaxX, cx2);
                  bMinY = Math.min(bMinY, cy2); bMaxY = Math.max(bMaxY, cy2);
                  bSumX += cx2; bSumY += cy2; bCnt++;

                  // check 4-neighbours (with distance tolerance of 2)
                  const neighbours = [cur - 1, cur + 1, cur - mW, cur + mW, cur - 2, cur + 2, cur - mW * 2, cur + mW * 2];
                  for (const nb of neighbours) {
                    if (nb >= 0 && nb < mW * mH && motionMap[nb] && !visited[nb]) {
                      visited[nb] = 1;
                      queue.push(nb);
                    }
                  }
                }

                if (bCnt >= 8) {
                  blobs.push({ minX: bMinX, minY: bMinY, maxX: bMaxX, maxY: bMaxY, sumX: bSumX, sumY: bSumY, count: bCnt });
                }
              }

              // Step 3 — scale blobs to canvas coords
              const scaleX = canvas.width / mW;
              const scaleY = canvas.height / mH;

              interface CanvasBlob { cx: number; cy: number; w: number; h: number; }
              const canvasBlobs: CanvasBlob[] = blobs.map(b => ({
                cx: (b.sumX / b.count) * scaleX,
                cy: (b.sumY / b.count) * scaleY,
                w: Math.max(8, (b.maxX - b.minX) * scaleX),
                h: Math.max(8, (b.maxY - b.minY) * scaleY)
              }));

              // Step 4 — IoU-based matching of blobs to existing trackTargetsRef
              const prevTargets = trackTargetsRef.current;
              const matched = new Set<number>();
              const usedBlobs = new Set<number>();

              const iou = (a: {cx:number;cy:number;w:number;h:number}, b: CanvasBlob): number => {
                const ax1 = a.cx - a.w/2, ay1 = a.cy - a.h/2, ax2 = a.cx + a.w/2, ay2 = a.cy + a.h/2;
                const bx1 = b.cx - b.w/2, by1 = b.cy - b.h/2, bx2 = b.cx + b.w/2, by2 = b.cy + b.h/2;
                const ix1 = Math.max(ax1, bx1), iy1 = Math.max(ay1, by1);
                const ix2 = Math.min(ax2, bx2), iy2 = Math.min(ay2, by2);
                const inter = Math.max(0, ix2 - ix1) * Math.max(0, iy2 - iy1);
                const areaA = a.w * a.h, areaB = b.w * b.h;
                return inter / (areaA + areaB - inter + 1e-6);
              };

              const updatedTargets: TrackTarget[] = [];

              for (let ti = 0; ti < prevTargets.length; ti++) {
                const prev = prevTargets[ti];
                let bestIou = 0.3, bestBi = -1;
                for (let bi = 0; bi < canvasBlobs.length; bi++) {
                  if (usedBlobs.has(bi)) continue;
                  const score = iou(prev, canvasBlobs[bi]);
                  if (score > bestIou) { bestIou = score; bestBi = bi; }
                }
                if (bestBi >= 0) {
                  const b = canvasBlobs[bestBi];
                  usedBlobs.add(bestBi);
                  matched.add(ti);
                  // Compensate for camera shake: subtract global mean motion
                  const rawVx = b.cx - prev.cx - globalDx * scaleX * 0.01;
                  const rawVy = b.cy - prev.cy - globalDy * scaleY * 0.01;
                  const newTrail = [...prev.trail, { x: prev.cx, y: prev.cy }].slice(-12);
                  updatedTargets.push({
                    ...prev,
                    cx: b.cx, cy: b.cy, w: b.w, h: b.h,
                    vx: rawVx, vy: rawVy,
                    trail: newTrail,
                    dwell: prev.dwell + 1,
                    frames: prev.frames + 1,
                    prevArea: prev.w * prev.h
                  });
                }
                // else: target lost, drop it
              }

              // Step 5 — create new targets for unmatched blobs
              for (let bi = 0; bi < canvasBlobs.length; bi++) {
                if (usedBlobs.has(bi)) continue;
                const b = canvasBlobs[bi];
                updatedTargets.push({
                  id: nextTrackIdRef.current++,
                  cx: b.cx, cy: b.cy, w: b.w, h: b.h,
                  vx: 0, vy: 0, trail: [],
                  dwell: 0, frames: 1, prevArea: b.w * b.h
                });
              }

              trackTargetsRef.current = updatedTargets;

              // Update legacy motionRectRef for backwards compatibility
              if (updatedTargets.length > 0) {
                const t0 = updatedTargets[0];
                motionRectRef.current = { x: t0.cx - t0.w/2, y: t0.cy - t0.h/2, w: t0.w, h: t0.h, active: true };
              } else {
                motionRectRef.current.active = false;
              }
            } else {
              motionRectRef.current.active = false;
            }
            lastFrameDataRef.current = new Uint8ClampedArray(pixels);
          }
        } else {
          motionRectRef.current.active = false;
          lastFrameDataRef.current = null;
          if (!trackMotion) trackTargetsRef.current = [];
        }
      } else {
        // Clear with dark tech grid
        ctx.fillStyle = "#020617";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw vector tech scanner grid background
        ctx.strokeStyle = "rgba(16, 185, 129, 0.04)";
        ctx.lineWidth = 1;
        const gridSize = 20;
        for (let x = 0; x < canvas.width; x += gridSize) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, canvas.height);
          ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += gridSize) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(canvas.width, y);
          ctx.stroke();
        }
      }

      // Draw custom visual based on active item
      if (selectedPreset) {
        ctx.save();
        
        // Apply zoom scale centered at tracking focal point cx, cy
        if (zoomLevel > 1) {
          ctx.translate(cx, cy);
          ctx.scale(zoomLevel, zoomLevel);
          ctx.translate(-cx, -cy);
        }
        
        let colorTheme = "#10b981"; // Emerald
        if (filterMode === "thermal") {
          colorTheme = "#f97316"; // Orange
        } else if (filterMode === "stealth") {
          colorTheme = "#06b6d4"; // Cyan
        } else if (filterMode === "nightvision") {
          colorTheme = "#22c55e"; // Phosphor Green
        }

        // Draw Object base matching ID
        ctx.strokeStyle = colorTheme;
        ctx.lineWidth = Math.max(0.35, 2 / Math.sqrt(zoomLevel));
        ctx.fillStyle = "rgba(16, 185, 129, 0.05)";

        const id = selectedPreset.id;

        if (id.includes("spy_") || selectedPreset.category === "Spy & Covert Gear") {
          // Tactical schema of custom hidden spy devices
          ctx.strokeStyle = "#f43f5e"; // Red alert tone
          ctx.fillStyle = "rgba(244, 63, 94, 0.08)";
          ctx.lineWidth = Math.max(0.3, 1.5 / Math.sqrt(zoomLevel));
          ctx.beginPath();
          ctx.arc(cx, cy, 60, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();

          // crosshair scan lines
          ctx.strokeStyle = "rgba(244, 63, 94, 0.35)";
          ctx.beginPath();
          ctx.moveTo(cx - 75, cy); ctx.lineTo(cx + 75, cy);
          ctx.moveTo(cx, cy - 75); ctx.lineTo(cx, cy + 75);
          ctx.stroke();

          ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
          ctx.strokeStyle = "#f43f5e";

          if (id.includes("usb_charger")) {
            // Wall plug body
            ctx.beginPath();
            ctx.rect(cx - 28, cy - 20, 56, 50);
            ctx.fill();
            ctx.stroke();
            // Metal prongs
            ctx.strokeRect(cx - 16, cy - 34, 10, 14);
            ctx.strokeRect(cx + 6, cy - 34, 10, 14);
            // Red highlighted pinhole spy camera lens
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx, cy + 5, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Radar pulse ring
            ctx.strokeStyle = "rgba(239, 68, 68, 0.85)";
            ctx.beginPath();
            ctx.arc(cx, cy + 5, 12 + (Date.now() % 500) / 45, 0, Math.PI * 2);
            ctx.stroke();
          } else if (id.includes("smoke_detector")) {
            // Ceiling disk
            ctx.beginPath();
            ctx.arc(cx, cy, 48, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Central chamber mesh
            ctx.strokeRect(cx - 20, cy - 12, 40, 24);
            // Hidden lens indicator
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx + 10, cy, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Crosshair highlights
            ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
            ctx.strokeRect(cx + 2, cy - 8, 16, 16);
          } else if (id.includes("mirror_clock")) {
            // Digital clock frame
            ctx.strokeRect(cx - 55, cy - 22, 110, 44);
            // Numeric clock digits
            ctx.fillStyle = "rgba(244, 63, 94, 0.35)";
            ctx.font = "bold 13px monospace";
            ctx.fillText("12:45", cx - 20, cy + 5);
            // Red pinhole lens hidden behind reflection mirror
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx + 38, cy, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Radar sweep ring
            ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
            ctx.beginPath();
            ctx.arc(cx + 38, cy, 14, 0, Math.PI * 2);
            ctx.stroke();
          } else if (id.includes("screw_head")) {
            // Screw head circle with cross drive slots
            ctx.beginPath();
            ctx.arc(cx, cy, 24, 0, Math.PI * 2);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(cx - 14, cy - 14); ctx.lineTo(cx + 14, cy + 14);
            ctx.moveTo(cx + 14, cy - 14); ctx.lineTo(cx - 14, cy + 14);
            ctx.stroke();
            // Center-bored pinhole lens channel
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx, cy, 3.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
          } else if (id.includes("covert_pen")) {
            // Ballpoint pen structure
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(Math.PI / 4);
            ctx.strokeRect(-5, -55, 10, 110);
            ctx.strokeRect(2, -35, 4, 45); // pocket clip
            // Pinhole camera lens inside clip head
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(4, -30, 2.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
          } else if (id.includes("teddy_eye")) {
            // Bear circular head base
            ctx.beginPath();
            ctx.arc(cx, cy, 42, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Right normal eye
            ctx.fillStyle = "#334155";
            ctx.beginPath();
            ctx.arc(cx - 14, cy - 8, 7, 0, Math.PI * 2);
            ctx.fill();
            // Left eye containing hidden pinhole lens
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx + 14, cy - 8, 7, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Active targeting ring
            ctx.strokeStyle = "rgba(239, 68, 68, 0.9)";
            ctx.beginPath();
            ctx.arc(cx + 14, cy - 8, 14, 0, Math.PI * 2);
            ctx.stroke();
          } else {
            // Generic Spy Gear Targeting Ring
            ctx.strokeStyle = "#f43f5e";
            ctx.beginPath();
            ctx.arc(cx, cy, 40, 0, Math.PI * 2);
            ctx.stroke();
            ctx.fillStyle = "#f43f5e";
            ctx.beginPath();
            ctx.arc(cx, cy, 5, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        else if (id.includes("smart_tv") || id.includes("crt_tv")) {
          // Electronic Screen
          ctx.fillStyle = "rgba(30, 41, 59, 0.4)";
          ctx.fillRect(cx - 85, cy - 55, 170, 105);
          ctx.strokeRect(cx - 85, cy - 55, 170, 105);

          // Inner reflection line
          ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
          ctx.beginPath();
          ctx.moveTo(cx - 80, cy + 40);
          ctx.lineTo(cx + 70, cy - 50);
          ctx.stroke();

          // Stand base
          ctx.strokeStyle = colorTheme;
          ctx.beginPath();
          ctx.moveTo(cx - 20, cy + 50);
          ctx.lineTo(cx - 25, cy + 68);
          ctx.lineTo(cx + 25, cy + 68);
          ctx.lineTo(cx + 20, cy + 50);
          ctx.closePath();
          ctx.stroke();
        }
        else if (id.includes("router")) {
          // Base Router chassis
          ctx.fillStyle = "rgba(15, 23, 42, 0.6)";
          ctx.beginPath();
          ctx.moveTo(cx - 55, cy + 20);
          ctx.lineTo(cx - 45, cy - 10);
          ctx.lineTo(cx + 45, cy - 10);
          ctx.lineTo(cx + 55, cy + 20);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();

          // 4 Dipole Antennas
          ctx.strokeStyle = colorTheme;
          ctx.lineWidth = 3;
          for (let i = 0; i < 4; i++) {
            const ax = cx - 40 + i * 26;
            ctx.beginPath();
            ctx.moveTo(ax, cy - 10);
            ctx.lineTo(ax - 5, cy - 65);
            ctx.stroke();
          }
          ctx.lineWidth = 1;
        }
        else if (id.includes("dog") || id.includes("cat") || id.includes("panda")) {
          // Quadruped biological structure animal representation
          ctx.fillStyle = "rgba(22, 101, 52, 0.15)";
          ctx.beginPath();
          ctx.ellipse(cx + 5, cy + 10, 48, 32, 0, 0, Math.PI * 2); // Body
          ctx.ellipse(cx - 35, cy - 15, 22, 22, 0, 0, Math.PI * 2); // Head
          ctx.fill();
          ctx.stroke();

          // Four Legs
          ctx.beginPath();
          ctx.moveTo(cx - 25, cy + 25); ctx.lineTo(cx - 25, cy + 60);
          ctx.moveTo(cx + 25, cy + 25); ctx.lineTo(cx + 25, cy + 60);
          ctx.moveTo(cx - 10, cy + 25); ctx.lineTo(cx - 10, cy + 60);
          ctx.moveTo(cx + 10, cy + 25); ctx.lineTo(cx + 10, cy + 60);
          ctx.stroke();

          // Tail
          ctx.beginPath();
          ctx.arc(cx + 50, cy, 18, Math.PI * 1.5, Math.PI * 0.2);
          ctx.stroke();
        }
        else if (id.includes("human")) {
          // Full physical human mesh simulation
          ctx.beginPath();
          ctx.arc(cx, cy - 65, 14, 0, Math.PI * 2); // Head
          ctx.moveTo(cx, cy - 51);
          ctx.lineTo(cx, cy + 25); // Spinal Axis

          // Shoulders and arms
          ctx.moveTo(cx - 28, cy - 35);
          ctx.lineTo(cx + 28, cy - 35);
          ctx.moveTo(cx - 28, cy - 35);
          ctx.lineTo(cx - 40, cy + 15);
          ctx.moveTo(cx + 28, cy - 35);
          ctx.lineTo(cx + 40, cy + 15);

          // Pelvic waist base and legs
          ctx.moveTo(cx, cy + 25);
          ctx.lineTo(cx - 20, cy + 85);
          ctx.moveTo(cx, cy + 25);
          ctx.lineTo(cx + 20, cy + 85);
          ctx.stroke();

          // Focus indicator rings on chest/head
          ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
          ctx.beginPath();
          ctx.arc(cx, cy - 65, 25, 0, Math.PI * 2);
          ctx.stroke();
        }
        else if (id.includes("spy_")) {
          // Tactical schematic of custom hidden spy devices
          ctx.strokeStyle = "#f43f5e"; // Red alert tone
          ctx.fillStyle = "rgba(244, 63, 94, 0.08)";
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(cx, cy, 60, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();

          // crosshair scan lines
          ctx.strokeStyle = "rgba(244, 63, 94, 0.35)";
          ctx.beginPath();
          ctx.moveTo(cx - 75, cy); ctx.lineTo(cx + 75, cy);
          ctx.moveTo(cx, cy - 75); ctx.lineTo(cx, cy + 75);
          ctx.stroke();

          ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
          ctx.strokeStyle = "#f43f5e";

          if (id.includes("usb_charger")) {
            // Wall plug body
            ctx.beginPath();
            ctx.rect(cx - 28, cy - 20, 56, 50);
            ctx.fill();
            ctx.stroke();
            // Metal prongs
            ctx.strokeRect(cx - 16, cy - 34, 10, 14);
            ctx.strokeRect(cx + 6, cy - 34, 10, 14);
            // Red highlighted pinhole spy camera lens
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx, cy + 5, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Radar pulse ring
            ctx.strokeStyle = "rgba(239, 68, 68, 0.85)";
            ctx.beginPath();
            ctx.arc(cx, cy + 5, 12 + (Date.now() % 500) / 45, 0, Math.PI * 2);
            ctx.stroke();
          } else if (id.includes("smoke_detector")) {
            // Ceiling disk
            ctx.beginPath();
            ctx.arc(cx, cy, 48, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Central chamber mesh
            ctx.strokeRect(cx - 20, cy - 12, 40, 24);
            // Hidden lens indicator
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx + 10, cy, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Crosshair highlights
            ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
            ctx.strokeRect(cx + 2, cy - 8, 16, 16);
          } else if (id.includes("mirror_clock")) {
            // Digital clock frame
            ctx.strokeRect(cx - 55, cy - 22, 110, 44);
            // Numeric clock digits
            ctx.fillStyle = "rgba(244, 63, 94, 0.35)";
            ctx.font = "bold 13px monospace";
            ctx.fillText("12:45", cx - 20, cy + 5);
            // Red pinhole lens hidden behind reflection mirror
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx + 38, cy, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Radar sweep ring
            ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
            ctx.beginPath();
            ctx.arc(cx + 38, cy, 14, 0, Math.PI * 2);
            ctx.stroke();
          } else if (id.includes("screw_head")) {
            // Screw head circle with cross drive slots
            ctx.beginPath();
            ctx.arc(cx, cy, 24, 0, Math.PI * 2);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(cx - 14, cy - 14); ctx.lineTo(cx + 14, cy + 14);
            ctx.moveTo(cx + 14, cy - 14); ctx.lineTo(cx - 14, cy + 14);
            ctx.stroke();
            // Center-bored pinhole lens channel
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx, cy, 3.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
          } else if (id.includes("covert_pen")) {
            // Ballpoint pen structure
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(Math.PI / 4);
            ctx.strokeRect(-5, -55, 10, 110);
            ctx.strokeRect(2, -35, 4, 45); // pocket clip
            // Pinhole camera lens inside clip head
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(4, -30, 2.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
          } else if (id.includes("teddy_eye")) {
            // Bear circular head base
            ctx.beginPath();
            ctx.arc(cx, cy, 42, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Right normal eye
            ctx.fillStyle = "#334155";
            ctx.beginPath();
            ctx.arc(cx - 14, cy - 8, 7, 0, Math.PI * 2);
            ctx.fill();
            // Left eye containing hidden pinhole lens
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(cx + 14, cy - 8, 7, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Active targeting ring
            ctx.strokeStyle = "rgba(239, 68, 68, 0.9)";
            ctx.beginPath();
            ctx.arc(cx + 14, cy - 8, 14, 0, Math.PI * 2);
            ctx.stroke();
          }
        }
        ctx.restore();

        // 4K Microscopic Enhancement Overlays outside the scale matrix to keep text vector-sharp
        if (zoomLevel > 1.1) {
          const specs = detectCameraSpecifications();
          ctx.save();
          
          // Draw a technical scan reticle in the center
          ctx.strokeStyle = zoomLevel >= 15 ? "rgba(6, 182, 212, 0.4)" : "rgba(16, 185, 129, 0.4)";
          ctx.lineWidth = 1;
          
          // Outer fine tech target ring
          ctx.beginPath();
          ctx.arc(cx, cy, 80, 0, Math.PI * 2);
          ctx.stroke();

          // Scale coordinate indicators
          ctx.fillStyle = zoomLevel >= 15 ? "#06b6d4" : "#10b981";
          ctx.font = "8px monospace";
          ctx.fillText(`FOCAL RANGE: ${(15 / zoomLevel).toFixed(3)}mm`, cx - 75, cy - 85);
          ctx.fillText(`4K RESOLVING: ${(Math.min(100, zoomLevel * 3)).toFixed(1)}% WAFER GRID`, cx - 74, cy + 92);

          // If really deep zoom (>= 15x), draw subpixel lattice lines representing simulated 4K sensor cell structure
          if (zoomLevel >= 15) {
            ctx.strokeStyle = "rgba(6, 182, 212, 0.15)";
            ctx.lineWidth = 0.5;
            const latticeSize = 15;
            for (let x = cx - 110; x <= cx + 110; x += latticeSize) {
              ctx.beginPath();
              ctx.moveTo(x, cy - 110);
              ctx.lineTo(x, cy + 110);
              ctx.stroke();
            }
            for (let y = cy - 110; y <= cy + 110; y += latticeSize) {
              ctx.beginPath();
              ctx.moveTo(cx - 110, y);
              ctx.lineTo(cx + 110, y);
              ctx.stroke();
            }
            
            // Draw central target focus micro-dots
            ctx.fillStyle = "rgba(244, 63, 94, 0.7)";
            ctx.beginPath();
            ctx.arc(cx, cy, 2, 0, Math.PI * 2);
            ctx.fill();

            // High Definition watermark badge
            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
            ctx.fillRect(cx - 65, cy - 12, 130, 24);
            ctx.strokeStyle = "rgba(6, 182, 212, 0.5)";
            ctx.strokeRect(cx - 65, cy - 12, 130, 24);
            ctx.fillStyle = "#06b6d4";
            ctx.font = "bold 8px monospace";
            ctx.textAlign = "center";
            ctx.fillText("4K UHD COGNITIVE UPSCALING", cx, cy + 3);
            ctx.textAlign = "left";
          }

          // Top right watermark for device-spec awareness
          ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
          ctx.fillRect(canvas.width - 170, 8, 162, 50);
          ctx.strokeStyle = "rgba(16, 185, 129, 0.35)";
          ctx.strokeRect(canvas.width - 170, 8, 162, 50);
          
          ctx.font = "bold 8px system-ui, sans-serif";
          ctx.fillStyle = "#10b981";
          ctx.fillText("📷 كفاءة العدسة المجمَّعة المكتشفة:", canvas.width - 164, 20);
          ctx.fillStyle = "#ffffff";
          ctx.font = "7px system-ui, sans-serif";
          ctx.fillText(specs.brand, canvas.width - 164, 31);
          ctx.font = "7px monospace";
          ctx.fillStyle = "rgba(255,255,255,0.7)";
          ctx.fillText(specs.sensor, canvas.width - 164, 40);
          ctx.fillStyle = "#38bdf8";
          ctx.fillText(`RESOLVING LEVEL: x${zoomLevel.toFixed(0)} @ 4K STATUS`, canvas.width - 164, 49);

          ctx.restore();
        }

        // Draw Preset item name tag next to the visual center
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px system-ui, sans-serif";
        ctx.fillText(selectedPreset.name.toUpperCase(), 15, canvas.height - 38);
        ctx.fillStyle = "#10b981";
        ctx.font = "9px monospace";
        ctx.fillText(`BOUNDS: ${selectedPreset.size}`, 15, canvas.height - 25);
        ctx.fillStyle = "#06b6d4";
        ctx.fillText(`ZOOM: x${zoomLevel.toFixed(zoomLevel >= 10 ? 0 : 1)} [${zoomLevel >= 15 ? "4K UHD SUPER-RES" : "OPTICAL ENHANCED"}]`, 15, canvas.height - 12);
      } else if (!useLiveCamera) {
        // Drawing standard standby scanning graphic
        ctx.save();
        ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
        ctx.font = "italic 11px monospace";
        ctx.textBaseline = "middle";
        ctx.textAlign = "center";
        ctx.fillText("STANDBY LOGICAL CONTROLLER ACTIVE", canvas.width / 2, canvas.height / 2 - 20);
        ctx.fillText("SELECT PRESET TEST TARGET BELOW", canvas.width / 2, canvas.height / 2);
        ctx.fillText("OR FLIP LIVE CAMERA STREAM SWITCH", canvas.width / 2, canvas.height / 2 + 20);
        ctx.restore();
      }

      // Draw Active Motion Tracking Rect (or Real Moving Targets in simulated mode)
      if (trackMotion) {
        const trackingPresets = [
          "spy_usb_charger",
          "spy_smoke_detector",
          "spy_mirror_clock",
          "spy_screw_head",
          "spy_covert_pen",
          "spy_teddy_eye",
          "room_router"
        ];
        
        const time = Date.now();
        
        trackingPresets.forEach((presetId, index) => {
          const foundPreset = PRESET_SCENARIOS.find(p => p.id === presetId);
          if (!foundPreset) return;
          
          const pos = getTargetPosition(presetId, index, time, canvas.width, canvas.height);
          const isCurrent = selectedPreset?.id === presetId;
          
          ctx.save();
          
          // Outer box color based on filters
          let targetColor = isCurrent ? "#ef4444" : "#10b981";
          if (filterMode === "thermal") {
            targetColor = isCurrent ? "#ef4444" : "#f97316";
          } else if (filterMode === "stealth") {
            targetColor = isCurrent ? "#f43f5e" : "#06b6d4";
          } else if (filterMode === "nightvision") {
            targetColor = isCurrent ? "#ef4444" : "#22c55e";
          }
          
          ctx.strokeStyle = targetColor;
          ctx.lineWidth = isCurrent ? 2.5 : 1.5;

          // Drawing neat brackets for targets
          const bracketLen = 8;
          const x = pos.x;
          const y = pos.y;
          const w = pos.w;
          const h = pos.h;

          // Top-Left
          ctx.beginPath();
          ctx.moveTo(x, y + bracketLen); ctx.lineTo(x, y); ctx.lineTo(x + bracketLen, y);
          ctx.stroke();
          // Top-Right
          ctx.beginPath();
          ctx.moveTo(x + w, y + bracketLen); ctx.lineTo(x + w, y); ctx.lineTo(x + w - bracketLen, y);
          ctx.stroke();
          // Bottom-Left
          ctx.beginPath();
          ctx.moveTo(x, y + h - bracketLen); ctx.lineTo(x, y + h); ctx.lineTo(x + bracketLen, y + h);
          ctx.stroke();
          // Bottom-Right
          ctx.beginPath();
          ctx.moveTo(x + w, y + h - bracketLen); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - bracketLen, y + h);
          ctx.stroke();

          // Outer fill
          ctx.fillStyle = isCurrent ? "rgba(239, 68, 68, 0.08)" : "rgba(16, 185, 129, 0.02)";
          ctx.fillRect(x, y, w, h);

          // Target focus point
          const tx = x + w / 2;
          const ty = y + h / 2;
          ctx.fillStyle = targetColor;
          ctx.beginPath();
          ctx.arc(tx, ty, 2, 0, Math.PI * 2);
          ctx.fill();

          if (isCurrent) {
            ctx.strokeStyle = "rgba(239, 68, 68, 0.6)";
            ctx.beginPath();
            ctx.arc(tx, ty, 14 + (Date.now() % 400) / 30, 0, Math.PI * 2);
            ctx.stroke();
          }

          // Preset simulation: trail dots (last 5 positions)
          const prevTrailArr = presetTrailRef.current.get(presetId) || [];
          prevTrailArr.push({ x: tx, y: ty });
          if (prevTrailArr.length > 5) prevTrailArr.shift();
          presetTrailRef.current.set(presetId, prevTrailArr);
          for (let tri = 0; tri < prevTrailArr.length; tri++) {
            const tAlpha = (tri + 1) / prevTrailArr.length * 0.6;
            ctx.globalAlpha = tAlpha;
            ctx.fillStyle = targetColor;
            ctx.beginPath();
            ctx.arc(prevTrailArr[tri].x, prevTrailArr[tri].y, 2.5, 0, Math.PI * 2);
            ctx.fill();
          }
          ctx.globalAlpha = 1;

          // Preset simulation: velocity arrow (angular orbital direction)
          const angle2 = (time / 2000) + (index * Math.PI / 3.5);
          const vdx = Math.cos(angle2) * 12;
          const vdy = -Math.sin(angle2 * 1.3) * 10;
          ctx.strokeStyle = targetColor;
          ctx.lineWidth = 1;
          ctx.globalAlpha = 0.8;
          ctx.beginPath();
          ctx.moveTo(tx, ty);
          ctx.lineTo(tx + vdx, ty + vdy);
          ctx.stroke();
          // Arrowhead
          const vAng = Math.atan2(vdy, vdx);
          ctx.fillStyle = targetColor;
          ctx.beginPath();
          ctx.moveTo(tx + vdx, ty + vdy);
          ctx.lineTo(tx + vdx - 5 * Math.cos(vAng - 0.5), ty + vdy - 5 * Math.sin(vAng - 0.5));
          ctx.lineTo(tx + vdx - 5 * Math.cos(vAng + 0.5), ty + vdy - 5 * Math.sin(vAng + 0.5));
          ctx.closePath();
          ctx.fill();
          ctx.globalAlpha = 1;

          // Preset simulation: range line from centroid to frame center with distance label
          const fcx = canvas.width / 2;
          const fcy = canvas.height / 2;
          const rangeDist = Math.round(Math.sqrt((tx - fcx) ** 2 + (ty - fcy) ** 2));
          ctx.setLineDash([2, 4]);
          ctx.strokeStyle = "rgba(148,163,184,0.3)";
          ctx.lineWidth = 0.8;
          ctx.beginPath();
          ctx.moveTo(tx, ty);
          ctx.lineTo(fcx, fcy);
          ctx.stroke();
          ctx.setLineDash([]);
          const midRx = (tx + fcx) / 2;
          const midRy = (ty + fcy) / 2;
          ctx.fillStyle = "rgba(148,163,184,0.9)";
          ctx.font = "7px monospace";
          ctx.fillText(`${rangeDist}px`, midRx + 2, midRy - 2);

          // Preset simulation: threat badge based on proximity to center
          const threatClose = rangeDist < 80;
          const threatBadgeColor = threatClose ? "#ef4444" : (rangeDist < 160 ? "#f59e0b" : "#22c55e");
          const threatBadgeLabel = threatClose ? "HIGH" : (rangeDist < 160 ? "MED" : "LOW");
          ctx.fillStyle = "rgba(0,0,0,0.65)";
          ctx.fillRect(x - 1, y - 14, 38, 12);
          ctx.fillStyle = threatBadgeColor;
          ctx.font = "bold 8px monospace";
          ctx.fillText(`RISK:${threatBadgeLabel}`, x + 1, y - 5);

          // Metadata badge tags next to the target
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 8px system-ui, sans-serif";

          ctx.fillText(`[${isCurrent ? "LOCKED" : `TRK-0${index + 1}`}]`, x + w + 5, y + 8);

          ctx.fillStyle = isCurrent ? "#f87171" : "#34d399";
          ctx.font = "7px monospace";
          ctx.fillText(`CONF: ${foundPreset.confidence}%`, x + w + 5, y + 17);
          ctx.fillText(`SIZE: ${foundPreset.size}`, x + w + 5, y + 25);
          ctx.fillText(`RECON: ${foundPreset.category.split(" & ")[0].toUpperCase()}`, x + w + 5, y + 33);

          if (isCurrent) {
            ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(tx, ty);
            ctx.lineTo(canvas.width / 2, canvas.height / 2);
            ctx.stroke();
            ctx.setLineDash([]);
          }
          
          ctx.restore();
        });

        // Also permit camera actual motion detection if present
        if (motionRectRef.current.active) {
          ctx.save();
          ctx.strokeStyle = "#ef4444";
          ctx.lineWidth = 2;
          const m = motionRectRef.current;
          const pad = 10;
          ctx.strokeRect(m.x - pad, m.y - pad, m.w + pad*2, m.h + pad*2);
          ctx.fillStyle = "#ef4444";
          ctx.font = "9px monospace";
          ctx.fillText("MOTION ACCELERATION", m.x - pad, m.y - pad - 5);
          ctx.restore();
        }

        // === ADVANCED MULTI-TARGET LIVE TRACKING RENDERING ===
        if (useLiveCamera && trackMotion) {
          const targets = trackTargetsRef.current;
          const cW = canvas.width;
          const cH = canvas.height;
          const canvasArea = cW * cH;
          const tNow = Date.now();

          // Feature 10 — Zone grid overlay (3x3)
          ctx.save();
          ctx.strokeStyle = "rgba(100,200,255,0.12)";
          ctx.lineWidth = 0.8;
          for (let zi = 1; zi < 3; zi++) {
            ctx.beginPath();
            ctx.moveTo(zi * cW / 3, 0);
            ctx.lineTo(zi * cW / 3, cH);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, zi * cH / 3);
            ctx.lineTo(cW, zi * cH / 3);
            ctx.stroke();
          }
          ctx.restore();

          // Feature 11 — Motion heat canvas compositing
          if (heatCanvasRef.current) {
            const hCtx = heatCanvasRef.current.getContext("2d");
            if (hCtx) {
              heatCanvasRef.current.width = cW;
              heatCanvasRef.current.height = cH;
              targets.forEach((tgt: TrackTarget) => {
                hCtx.fillStyle = "rgba(255,50,0,0.02)";
                hCtx.beginPath();
                hCtx.arc(tgt.cx, tgt.cy, Math.max(tgt.w, tgt.h) * 0.5, 0, Math.PI * 2);
                hCtx.fill();
              });
              ctx.save();
              ctx.globalAlpha = 0.35;
              ctx.globalCompositeOperation = "screen";
              ctx.drawImage(heatCanvasRef.current, 0, 0);
              ctx.restore();
            }
          }

          // Feature 13 — Total count badge (top-left HUD)
          ctx.save();
          ctx.fillStyle = "rgba(0,0,0,0.7)";
          ctx.fillRect(6, 34, 110, 18);
          ctx.fillStyle = "#00ffcc";
          ctx.font = "bold 9px monospace";
          ctx.fillText(`⊕ TARGETS: ${targets.length}`, 10, 47);
          ctx.restore();

          // Find most-stable target for lock-on animation
          let lockTarget: TrackTarget | null = null;
          for (const tgt of targets) {
            if (!lockTarget || tgt.frames > lockTarget.frames) lockTarget = tgt;
          }

          targets.forEach((tgt: TrackTarget) => {
            ctx.save();

            const speed = Math.sqrt(tgt.vx * tgt.vx + tgt.vy * tgt.vy);
            const bboxArea = tgt.w * tgt.h;
            const areaRatio = Math.min(1, bboxArea / canvasArea);
            const distEst = Math.round(100 * (1 - areaRatio));
            const dwellSec = (tgt.dwell / 30).toFixed(1);
            const conf = Math.min(100, Math.round((tgt.frames / 30) * 100));
            const prevArea = tgt.prevArea || bboxArea;
            const areaChanging = bboxArea > prevArea * 1.05 ? "CLOSING" : (bboxArea < prevArea * 0.95 ? "RECEDING" : "STEADY");
            const areaArrow = bboxArea > prevArea * 1.05 ? "↑" : (bboxArea < prevArea * 0.95 ? "↓" : "→");

            // Threat level color
            let threatColor = "#22c55e"; // GREEN
            let threatLabel = "PASSIVE";
            if (speed > 4) { threatColor = "#ef4444"; threatLabel = "THREAT"; }
            else if (speed > 2) { threatColor = "#f59e0b"; threatLabel = "ACTIVE"; }

            // Feature 4 — Trail (ghost path) drawing
            const trail = tgt.trail;
            for (let ti = 0; ti < trail.length; ti++) {
              const age = (trail.length - ti) / trail.length;
              ctx.globalAlpha = (1 - age) * 0.7;
              ctx.fillStyle = threatColor;
              ctx.beginPath();
              ctx.arc(trail[ti].x, trail[ti].y, 2.5 * (1 - age * 0.5), 0, Math.PI * 2);
              ctx.fill();
            }
            ctx.globalAlpha = 1;

            // Feature 10 — Zone highlight
            const zoneCol = Math.floor((tgt.cx / cW) * 3);
            const zoneRow = Math.floor((tgt.cy / cH) * 3);
            const zx = zoneCol * cW / 3;
            const zy = zoneRow * cH / 3;
            ctx.strokeStyle = threatColor;
            ctx.globalAlpha = 0.25;
            ctx.lineWidth = 1.5;
            ctx.strokeRect(zx, zy, cW / 3, cH / 3);
            ctx.globalAlpha = 1;

            // Bounding box
            const bx = tgt.cx - tgt.w / 2;
            const by = tgt.cy - tgt.h / 2;
            ctx.strokeStyle = threatColor;
            ctx.lineWidth = 1.5;
            const bl = 8;
            // TL
            ctx.beginPath(); ctx.moveTo(bx, by + bl); ctx.lineTo(bx, by); ctx.lineTo(bx + bl, by); ctx.stroke();
            // TR
            ctx.beginPath(); ctx.moveTo(bx + tgt.w - bl, by); ctx.lineTo(bx + tgt.w, by); ctx.lineTo(bx + tgt.w, by + bl); ctx.stroke();
            // BL
            ctx.beginPath(); ctx.moveTo(bx, by + tgt.h - bl); ctx.lineTo(bx, by + tgt.h); ctx.lineTo(bx + bl, by + tgt.h); ctx.stroke();
            // BR
            ctx.beginPath(); ctx.moveTo(bx + tgt.w - bl, by + tgt.h); ctx.lineTo(bx + tgt.w, by + tgt.h); ctx.lineTo(bx + tgt.w, by + tgt.h - bl); ctx.stroke();

            // Feature 5 — Trajectory prediction dotted line
            if (speed > 0.5) {
              ctx.setLineDash([3, 4]);
              ctx.strokeStyle = threatColor;
              ctx.globalAlpha = 0.55;
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(tgt.cx, tgt.cy);
              ctx.lineTo(tgt.cx + tgt.vx * 8, tgt.cy + tgt.vy * 8);
              ctx.stroke();
              ctx.setLineDash([]);
              ctx.globalAlpha = 1;
              // Arrowhead
              const px = tgt.cx + tgt.vx * 8;
              const py = tgt.cy + tgt.vy * 8;
              const ang = Math.atan2(tgt.vy, tgt.vx);
              ctx.globalAlpha = 0.7;
              ctx.fillStyle = threatColor;
              ctx.beginPath();
              ctx.moveTo(px, py);
              ctx.lineTo(px - 6 * Math.cos(ang - 0.4), py - 6 * Math.sin(ang - 0.4));
              ctx.lineTo(px - 6 * Math.cos(ang + 0.4), py - 6 * Math.sin(ang + 0.4));
              ctx.closePath();
              ctx.fill();
              ctx.globalAlpha = 1;
            }

            // Feature 3 — Velocity vector arrow from centroid
            if (speed > 0.3) {
              ctx.strokeStyle = "#ffffff";
              ctx.lineWidth = 1.2;
              ctx.globalAlpha = 0.8;
              ctx.beginPath();
              ctx.moveTo(tgt.cx, tgt.cy);
              ctx.lineTo(tgt.cx + tgt.vx * 12, tgt.cy + tgt.vy * 12);
              ctx.stroke();
              ctx.globalAlpha = 1;
            }

            // HUD badges (right of bbox)
            const labX = bx + tgt.w + 5;
            let labY = by + 10;
            ctx.font = "bold 8px monospace";
            ctx.fillStyle = threatColor;
            ctx.fillText(`ID:${tgt.id} ${threatLabel}`, labX, labY); labY += 10;
            ctx.fillStyle = "#e2e8f0";
            ctx.font = "7px monospace";
            // Feature 6 — dwell time badge
            ctx.fillText(`T:${dwellSec}s`, labX, labY); labY += 9;
            // Feature 9 — Distance estimate
            ctx.fillText(`~${distEst}m`, labX, labY); labY += 9;
            // Feature 8 — Size-change direction
            ctx.fillText(`${areaArrow} ${areaChanging}`, labX, labY); labY += 9;
            // Feature 12 — Confidence score
            ctx.fillText(`CNF:${conf}%`, labX, labY);

            ctx.restore();
          });

          // Feature 15 — Lock-on animation for most stable target
          if (lockTarget && lockTarget.frames >= 3) {
            const lt = lockTarget;
            const tPulse = (tNow % 1000) / 1000;
            const innerR = Math.max(lt.w, lt.h) * 0.6 + 6 + tPulse * 4;
            const outerR = innerR + 10;
            ctx.save();
            ctx.strokeStyle = "#00ffcc";
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.85 - tPulse * 0.3;
            ctx.beginPath(); ctx.arc(lt.cx, lt.cy, innerR, 0, Math.PI * 2); ctx.stroke();
            ctx.beginPath(); ctx.arc(lt.cx, lt.cy, outerR, 0, Math.PI * 2); ctx.stroke();
            // Rotating tick marks every 45°
            ctx.globalAlpha = 0.9;
            const rotAngle = (tNow / 2000) % (Math.PI * 2);
            for (let ti = 0; ti < 8; ti++) {
              const tickAng = rotAngle + ti * (Math.PI / 4);
              ctx.beginPath();
              ctx.moveTo(lt.cx + innerR * Math.cos(tickAng), lt.cy + innerR * Math.sin(tickAng));
              ctx.lineTo(lt.cx + (outerR + 4) * Math.cos(tickAng), lt.cy + (outerR + 4) * Math.sin(tickAng));
              ctx.stroke();
            }
            ctx.fillStyle = "#00ffcc";
            ctx.font = "bold 9px monospace";
            ctx.textAlign = "center";
            ctx.fillText("LOCKED", lt.cx, lt.cy - outerR - 6);
            ctx.textAlign = "left";
            ctx.globalAlpha = 1;
            ctx.restore();
          }
        }
      }

      // Apply Custom Special Color Overlay Filters inside core viewport (Runs on live webcam as well!)
      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imgData.data;

      if (filterMode === "thermal") {
        // === ADVANCED FLIR THERMAL IMAGING — Adaptive Histogram Equalization ===
        const TW = canvas.width;
        const TH = canvas.height;

        // Pass 1: Find scene luminance min/max for adaptive stretching
        let sceneMin = 255, sceneMax = 0;
        for (let i = 0; i < data.length; i += 4 * 8) {
          const lum = 0.299 * data[i] + 0.587 * data[i+1] + 0.114 * data[i+2];
          if (lum < sceneMin) sceneMin = lum;
          if (lum > sceneMax) sceneMax = lum;
        }
        const lumRange = Math.max(1, sceneMax - sceneMin);

        // Pass 2: Apply palette with adaptive stretch (Feature 1 — Palette switcher)
        const currentPalette = thermalPaletteRef.current;
        // Also capture raw luma for frame-delta (Feature 4)
        const rawLumas = new Float32Array(TW * TH);
        for (let i = 0; i < data.length; i += 4) {
          rawLumas[i >> 2] = 0.299 * data[i] + 0.587 * data[i+1] + 0.114 * data[i+2];
        }
        for (let i = 0; i < data.length; i += 4) {
          const lum = rawLumas[i >> 2];
          const norm = Math.min(1, Math.max(0, (lum - sceneMin) / lumRange));
          let red = 0, green = 0, blue = 0;
          if (currentPalette === "rainbow") {
            // hue=norm*270 in HSL, S=100%, L=50%
            const hue = norm * 270;
            const c = 1, x2 = 1 - Math.abs(((hue / 60) % 2) - 1);
            const hi = Math.floor(hue / 60) % 6;
            const [r1, g1, b1] = hi === 0 ? [c, x2, 0] : hi === 1 ? [x2, c, 0] : hi === 2 ? [0, c, x2] : hi === 3 ? [0, x2, c] : hi === 4 ? [x2, 0, c] : [c, 0, x2];
            red = Math.round(r1 * 255); green = Math.round(g1 * 255); blue = Math.round(b1 * 255);
          } else if (currentPalette === "arctic") {
            // inverse: cold=white, hot=dark blue/purple
            const inv = 1 - norm;
            red = Math.round(inv * 255);
            green = Math.round(inv * 200);
            blue = Math.round(255 - norm * 100);
          } else if (currentPalette === "whiteHot") {
            const g3 = Math.round(norm * 255);
            red = g3; green = g3; blue = g3;
          } else {
            // ironbow (default)
            if (norm < 0.125) {
              const t = norm / 0.125;
              red = Math.floor(t * 30); green = 0; blue = Math.floor(20 + t * 100);
            } else if (norm < 0.25) {
              const t = (norm - 0.125) / 0.125;
              red = Math.floor(30 + t * 40); green = Math.floor(t * 15); blue = Math.floor(120 + t * 80);
            } else if (norm < 0.375) {
              const t = (norm - 0.25) / 0.125;
              red = Math.floor(70 - t * 30); green = Math.floor(15 + t * 105); blue = Math.floor(200 + t * 30);
            } else if (norm < 0.5) {
              const t = (norm - 0.375) / 0.125;
              red = Math.floor(40 + t * 60); green = Math.floor(120 + t * 90); blue = Math.floor(230 - t * 150);
            } else if (norm < 0.625) {
              const t = (norm - 0.5) / 0.125;
              red = Math.floor(100 + t * 125); green = Math.floor(210 + t * 30); blue = Math.floor(80 - t * 70);
            } else if (norm < 0.75) {
              const t = (norm - 0.625) / 0.125;
              red = Math.floor(225 + t * 30); green = Math.floor(240 - t * 120); blue = Math.floor(10 - t * 10);
            } else if (norm < 0.875) {
              const t = (norm - 0.75) / 0.125;
              red = 255; green = Math.floor(120 - t * 100); blue = Math.floor(t * 30);
            } else {
              const t = (norm - 0.875) / 0.125;
              red = 255; green = Math.floor(20 + t * 235); blue = Math.floor(30 + t * 225);
            }
          }
          data[i] = red; data[i+1] = green; data[i+2] = blue;
        }
        ctx.putImageData(imgData, 0, 0);

        // === THERMAL HUD OVERLAYS ===
        const tcx = TW / 2;
        const tcy = TH / 2;
        ctx.save();

        // 1. Main target scope with corner brackets
        ctx.strokeStyle = "rgba(244,63,94,0.9)";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(tcx - 70, tcy - 70, 140, 140);
        ctx.fillStyle = "#f43f5e";
        // Corner ticks
        [[tcx-73,tcy-73,14,3],[tcx-73,tcy-73,3,14],[tcx+59,tcy-73,14,3],[tcx+70,tcy-73,3,14],
         [tcx-73,tcy+70,14,3],[tcx-73,tcy+59,3,14],[tcx+59,tcy+70,14,3],[tcx+70,tcy+59,3,14]].forEach(([rx,ry,rw,rh]) => {
          ctx.fillRect(rx, ry, rw, rh);
        });

        // 2. Pixel-level hotspot/coldspot detection in target zone
        let maxB = -1, minB = 999, peakX = tcx, peakY = tcy, sinkX = tcx - 30, sinkY = tcy + 30;
        let totalV = 0, cnt = 0;
        const bl = Math.floor(tcx - 70), bt = Math.floor(tcy - 70), br = Math.floor(tcx + 70), bb = Math.floor(tcy + 70);
        for (let ty2 = Math.max(0, bt); ty2 < bb && ty2 < TH; ty2 += 3) {
          for (let tx2 = Math.max(0, bl); tx2 < br && tx2 < TW; tx2 += 3) {
            const idx = (ty2 * TW + tx2) * 4;
            if (idx < data.length) {
              const bv = 0.299 * data[idx] + 0.587 * data[idx+1] + 0.114 * data[idx+2];
              totalV += bv; cnt++;
              if (bv > maxB) { maxB = bv; peakX = tx2; peakY = ty2; }
              if (bv < minB) { minB = bv; sinkX = tx2; sinkY = ty2; }
            }
          }
        }
        const avgB = cnt > 0 ? totalV / cnt : 120;

        // Map brightness to temperature: 18°C (cold) to 45°C (hot)
        const mapTemp = (b: number) => (18 + (b / 255) * 27 + Math.sin(Date.now() / 3000) * 0.1).toFixed(1);
        const centerTemp = mapTemp(avgB);
        const hotTemp = mapTemp(maxB);
        const coldTemp = mapTemp(minB);

        // Hotspot glow
        const hotGrad = ctx.createRadialGradient(peakX, peakY, 0, peakX, peakY, 20);
        hotGrad.addColorStop(0, "rgba(255,255,255,0.6)");
        hotGrad.addColorStop(1, "rgba(255,100,0,0)");
        ctx.globalAlpha = 0.5;
        ctx.fillStyle = hotGrad;
        ctx.beginPath(); ctx.arc(peakX, peakY, 20, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 1;

        // Hotspot crosshair
        ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(peakX-10, peakY); ctx.lineTo(peakX+10, peakY);
        ctx.moveTo(peakX, peakY-10); ctx.lineTo(peakX, peakY+10);
        ctx.stroke();
        ctx.beginPath(); ctx.arc(peakX, peakY, 4, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = "#fff"; ctx.font = "bold 8px monospace";
        ctx.fillText(`MAX ${hotTemp}°C`, peakX + 12, peakY - 2);

        // Coldspot marker
        ctx.strokeStyle = "#60a5fa";
        ctx.beginPath();
        ctx.moveTo(sinkX-6, sinkY); ctx.lineTo(sinkX+6, sinkY);
        ctx.moveTo(sinkX, sinkY-6); ctx.lineTo(sinkX, sinkY+6);
        ctx.stroke();
        ctx.fillStyle = "#93c5fd"; ctx.font = "8px monospace";
        ctx.fillText(`MIN ${coldTemp}°C`, sinkX + 8, sinkY + 10);

        // 3. 9-point temperature measurement grid
        const gridPts = [
          [tcx-50,tcy-50],[tcx,tcy-50],[tcx+50,tcy-50],
          [tcx-50,tcy],   [tcx,tcy],   [tcx+50,tcy],
          [tcx-50,tcy+50],[tcx,tcy+50],[tcx+50,tcy+50]
        ];
        gridPts.forEach(([gx, gy], gi) => {
          const gi2 = (Math.floor(gy) * TW + Math.floor(gx)) * 4;
          const gb = gi2 >= 0 && gi2 < data.length ? (0.299 * data[gi2] + 0.587 * data[gi2+1] + 0.114 * data[gi2+2]) : avgB;
          const gt = mapTemp(gb);
          ctx.fillStyle = "rgba(0,0,0,0.55)";
          ctx.fillRect(gx - 14, gy + 2, 30, 11);
          ctx.fillStyle = gi === 4 ? "#fde047" : "#e2e8f0";
          ctx.font = "7px monospace";
          ctx.fillText(`${gt}°`, gx - 12, gy + 11);
          ctx.strokeStyle = gi === 4 ? "rgba(253,224,71,0.7)" : "rgba(255,255,255,0.3)";
          ctx.lineWidth = 0.5;
          ctx.beginPath(); ctx.arc(gx, gy, 2, 0, Math.PI * 2); ctx.stroke();
        });

        // 4. Center temperature panel
        ctx.fillStyle = "rgba(10,5,20,0.8)";
        ctx.fillRect(tcx - 112, tcy - 118, 224, 40);
        ctx.strokeStyle = "#f43f5e"; ctx.lineWidth = 1;
        ctx.strokeRect(tcx - 112, tcy - 118, 224, 40);
        ctx.fillStyle = "#f43f5e"; ctx.font = "bold 9px system-ui";
        ctx.fillText("🌡️ FLIR THERMAL SENSOR — ADAPTIVE MODE", tcx - 104, tcy - 104);
        ctx.fillStyle = "#fff"; ctx.font = "bold 10px system-ui";
        ctx.fillText(`CENTER: ${centerTemp}°C`, tcx - 104, tcy - 89);

        // Human body range indicator
        const numTemp = parseFloat(centerTemp);
        const isBioTemp = numTemp >= 35.5 && numTemp <= 38.5;
        ctx.fillStyle = "rgba(10,5,20,0.75)";
        ctx.fillRect(tcx - 90, tcy + 78, 180, 22);
        ctx.strokeStyle = isBioTemp ? "#10b981" : "#f97316";
        ctx.strokeRect(tcx - 90, tcy + 78, 180, 22);
        ctx.fillStyle = isBioTemp ? "#10b981" : "#f97316";
        ctx.font = "bold 9px system-ui";
        ctx.fillText(isBioTemp ? "🧬 BIOLOGIC HEAT SIGNATURE" : "⚡ ELECTRONIC HEAT SOURCE", tcx - 80, tcy + 93);

        // 5. Enhanced spectrum legend — right margin
        const barX2 = TW - 22, barY2 = 40, barW2 = 10, barH2 = TH - 80;
        const lg2 = ctx.createLinearGradient(barX2, barY2, barX2, barY2 + barH2);
        lg2.addColorStop(0, "#ffffff");
        lg2.addColorStop(0.12, "#fde047");
        lg2.addColorStop(0.25, "#f97316");
        lg2.addColorStop(0.45, "#ef4444");
        lg2.addColorStop(0.6, "#a855f7");
        lg2.addColorStop(0.75, "#3b82f6");
        lg2.addColorStop(0.9, "#1e40af");
        lg2.addColorStop(1, "#0f172a");
        ctx.fillStyle = lg2;
        ctx.fillRect(barX2, barY2, barW2, barH2);
        ctx.strokeStyle = "rgba(255,255,255,0.35)";
        ctx.strokeRect(barX2, barY2, barW2, barH2);
        // Temperature ticks on legend
        ctx.fillStyle = "#fff"; ctx.font = "7px monospace";
        const tempLabels = [["45°C",0],["38°C",0.2],["32°C",0.4],["26°C",0.6],["20°C",0.8],["14°C",1.0]];
        tempLabels.forEach(([label, frac]) => {
          const ly = barY2 + (frac as number) * barH2;
          ctx.fillText(label as string, barX2 - 28, ly + 3);
          ctx.strokeStyle = "rgba(255,255,255,0.3)"; ctx.lineWidth = 0.5;
          ctx.beginPath(); ctx.moveTo(barX2 - 2, ly); ctx.lineTo(barX2, ly); ctx.stroke();
        });

        // Feature 1 — Palette switcher HUD button on canvas (bottom-left corner)
        {
          ctx.fillStyle = "rgba(0,0,0,0.75)";
          ctx.fillRect(4, TH - 42, 80, 18);
          ctx.strokeStyle = "rgba(249,115,22,0.7)";
          ctx.lineWidth = 0.8;
          ctx.strokeRect(4, TH - 42, 80, 18);
          ctx.fillStyle = "#fb923c";
          ctx.font = "bold 7px monospace";
          ctx.fillText(`PALETTE: ${currentPalette.toUpperCase()}`, 8, TH - 29);
        }

        // Feature 2 — 9-zone temperature grid over the full frame
        {
          const cellW2 = TW / 3;
          const cellH2 = TH / 3;
          let hotCellIdx2 = 0;
          let hotCellLuma2 = -1;
          const cellLumas2: number[] = [];
          for (let rr = 0; rr < 3; rr++) {
            for (let cc = 0; cc < 3; cc++) {
              let sumL2 = 0, cntL2 = 0;
              const x2s = Math.floor(cc * cellW2), y2s = Math.floor(rr * cellH2);
              const x2e = Math.floor((cc + 1) * cellW2), y2e = Math.floor((rr + 1) * cellH2);
              for (let yy = y2s; yy < y2e; yy += 4) {
                for (let xx = x2s; xx < x2e; xx += 4) {
                  const ii = (yy * TW + xx) * 4;
                  if (ii < data.length) { sumL2 += rawLumas[ii >> 2]; cntL2++; }
                }
              }
              const avgL2 = cntL2 > 0 ? sumL2 / cntL2 : 128;
              cellLumas2.push(avgL2);
              if (avgL2 > hotCellLuma2) { hotCellLuma2 = avgL2; hotCellIdx2 = rr * 3 + cc; }
            }
          }
          for (let rr = 0; rr < 3; rr++) {
            for (let cc = 0; cc < 3; cc++) {
              const ci2 = rr * 3 + cc;
              const cx2s = cc * cellW2, cy2s = rr * cellH2;
              const cellTemp2 = (14 + (cellLumas2[ci2] / 255) * 31).toFixed(1);
              ctx.strokeStyle = ci2 === hotCellIdx2 ? "rgba(251,146,60,0.7)" : "rgba(255,255,255,0.1)";
              ctx.lineWidth = ci2 === hotCellIdx2 ? 1.5 : 0.5;
              ctx.strokeRect(cx2s, cy2s, cellW2, cellH2);
              ctx.fillStyle = "rgba(0,0,0,0.5)";
              ctx.fillRect(cx2s + cellW2/2 - 14, cy2s + cellH2/2 - 7, 28, 12);
              ctx.fillStyle = ci2 === hotCellIdx2 ? "#fb923c" : "#e2e8f0";
              ctx.font = "7px monospace";
              ctx.textAlign = "center";
              ctx.fillText(`${cellTemp2}°C`, cx2s + cellW2 / 2, cy2s + cellH2 / 2 + 3);
              ctx.textAlign = "left";
            }
          }
        }

        // Feature 3 — Bio-heat detection circle (norm in 0.55-0.72 range = body temp 35-38.5°C)
        {
          let bioSumX = 0, bioSumY = 0, bioCnt = 0;
          for (let by3 = 0; by3 < TH; by3 += 4) {
            for (let bx3 = 0; bx3 < TW; bx3 += 4) {
              const ii3 = (by3 * TW + bx3) * 4;
              const lum3 = rawLumas[ii3 >> 2];
              const norm3 = Math.min(1, Math.max(0, (lum3 - sceneMin) / lumRange));
              if (norm3 >= 0.55 && norm3 <= 0.72) {
                bioSumX += bx3; bioSumY += by3; bioCnt++;
              }
            }
          }
          if (bioCnt > 40) {
            const bioCx = bioSumX / bioCnt;
            const bioCy = bioSumY / bioCnt;
            const bioPulse = Math.abs(Math.sin(Date.now() / 600)) * 8;
            ctx.save();
            ctx.strokeStyle = "#22c55e";
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.7 + Math.sin(Date.now() / 500) * 0.2;
            ctx.beginPath(); ctx.arc(bioCx, bioCy, 24 + bioPulse, 0, Math.PI * 2); ctx.stroke();
            ctx.beginPath(); ctx.arc(bioCx, bioCy, 16, 0, Math.PI * 2); ctx.stroke();
            ctx.globalAlpha = 1;
            ctx.fillStyle = "rgba(0,0,0,0.7)";
            ctx.fillRect(bioCx - 58, bioCy - 38, 116, 14);
            ctx.fillStyle = "#22c55e";
            ctx.font = "bold 8px monospace";
            ctx.textAlign = "center";
            ctx.fillText("BIO HEAT SIGNATURE DETECTED", bioCx, bioCy - 28);
            ctx.textAlign = "left";
            ctx.restore();
          }
        }

        // Feature 4 — Frame delta temperature drift
        {
          const tNowThermal = Date.now();
          const prevLuma = prevThermalLumaRef.current;
          if (prevLuma && prevLuma.length === rawLumas.length) {
            const dtSec = Math.max(0.016, (tNowThermal - prevThermalTimeRef.current) / 1000);
            let deltaSum = 0;
            for (let di = 0; di < rawLumas.length; di += 8) { deltaSum += rawLumas[di] - prevLuma[di]; }
            const deltaMeanLuma = deltaSum / (rawLumas.length / 8);
            const deltaTempPerSec = (deltaMeanLuma / 255) * 31 / dtSec;
            const sign4 = deltaTempPerSec >= 0 ? "+" : "";
            ctx.fillStyle = "rgba(0,0,0,0.65)";
            ctx.fillRect(4, TH - 58, 120, 14);
            ctx.fillStyle = "#fde047";
            ctx.font = "bold 7px monospace";
            ctx.fillText(`ΔTEMP: ${sign4}${deltaTempPerSec.toFixed(1)}°C/s`, 8, TH - 47);
          }
          prevThermalLumaRef.current = new Float32Array(rawLumas);
          prevThermalTimeRef.current = tNowThermal;
        }

        // Feature 5 — Cold-spot marker (min luma pixel in full frame)
        {
          let minL5 = Infinity, coldX5 = 0, coldY5 = 0;
          for (let cy5 = 0; cy5 < TH; cy5 += 3) {
            for (let cx5 = 0; cx5 < TW; cx5 += 3) {
              const ii5 = (cy5 * TW + cx5) * 4;
              const l5 = rawLumas[ii5 >> 2];
              if (l5 < minL5) { minL5 = l5; coldX5 = cx5; coldY5 = cy5; }
            }
          }
          ctx.save();
          ctx.strokeStyle = "#60a5fa";
          ctx.lineWidth = 1.2;
          const d5 = 6;
          ctx.beginPath();
          ctx.moveTo(coldX5 - d5, coldY5); ctx.lineTo(coldX5, coldY5 - d5);
          ctx.lineTo(coldX5 + d5, coldY5); ctx.lineTo(coldX5, coldY5 + d5);
          ctx.closePath();
          ctx.stroke();
          ctx.fillStyle = "#93c5fd";
          ctx.font = "bold 7px monospace";
          ctx.fillText("COLD", coldX5 + d5 + 2, coldY5 + 3);
          ctx.restore();
        }

        ctx.restore();

      } else if (filterMode === "stealth") {
        // Cyan anti-recon laser outlining
        for (let i = 0; i < data.length; i += 4) {
          const r = data[i];
          const g = data[i + 1];
          const b = data[i + 2];
          const lightness = (r + g + b) / 3;
          if (lightness > 20) {
            data[i] = 6;       // Glowing neon cyan accent
            data[i + 1] = 182;
            data[i + 2] = 212;
          }
        }
        ctx.putImageData(imgData, 0, 0);
      } else if (filterMode === "nightvision") {
        // ── GEN-3+ NVG: Adaptive gain · gamma · bloom · vignette · tactical HUD ──
        const W = canvas.width;
        const H = canvas.height;

        // Pass 1 — adaptive gain: find scene luma range
        let lumaMin = 255, lumaMax = 0;
        for (let i = 0; i < data.length; i += 4) {
          const luma = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
          if (luma < lumaMin) lumaMin = luma;
          if (luma > lumaMax) lumaMax = luma;
        }
        const lumaRange = Math.max(lumaMax - lumaMin, 1);

        // Pass 2 — NVG pixel processing with gamma + phosphor bloom kernel prep
        const bloomAcc = new Float32Array(W * H); // luma accumulator for bloom
        const GAMMA = 0.55; // gen-3 cathode gamma
        for (let i = 0; i < data.length; i += 4) {
          const rawLuma = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
          // Adaptive stretch to [0..1], gamma-corrected
          let norm = (rawLuma - lumaMin) / lumaRange;
          norm = Math.pow(Math.max(0, Math.min(1, norm)), GAMMA);
          // Phosphor noise: high-frequency dithering typical of GEN-3 tubes
          const noise = (Math.random() - 0.5) * 0.04 * (1 - norm); // noise only in dark areas
          const amp = Math.max(0, Math.min(1, norm + noise));
          // Phosphor spectral split: Ga-As photocathode peaks at ~550 nm (green-yellow)
          data[i]     = Math.round(amp * 18);          // near-zero red
          data[i + 1] = Math.round(amp * 255);         // full phosphor green
          data[i + 2] = Math.round(amp * 38);          // faint blue for realism
          bloomAcc[(i >> 2)] = amp;
        }
        ctx.putImageData(imgData, 0, 0);

        // Pass 3 — bloom glow: radial gradient on every pixel above 0.85 brightness
        // (simulates photocathode saturation / bright-spot halo)
        ctx.save();
        ctx.globalCompositeOperation = "screen";
        for (let py = 0; py < H; py += 2) {
          for (let px = 0; px < W; px += 2) {
            const amp = bloomAcc[py * W + px];
            if (amp > 0.82) {
              const radius = 6 + amp * 18;
              const grd = ctx.createRadialGradient(px, py, 0, px, py, radius);
              const alpha = ((amp - 0.82) / 0.18) * 0.55;
              grd.addColorStop(0, `rgba(60,255,80,${alpha.toFixed(2)})`);
              grd.addColorStop(1, "rgba(0,0,0,0)");
              ctx.fillStyle = grd;
              ctx.fillRect(px - radius, py - radius, radius * 2, radius * 2);
            }
          }
        }
        ctx.restore();

        // Pass 4 — CRT scanlines (every 2 px, alternating dark band)
        ctx.save();
        ctx.globalCompositeOperation = "multiply";
        for (let y = 0; y < H; y += 2) {
          ctx.fillStyle = "rgba(0,0,0,0.28)";
          ctx.fillRect(0, y, W, 1);
        }
        ctx.restore();

        // Pass 5 — vignette: circular dark falloff from center
        ctx.save();
        const vgrd = ctx.createRadialGradient(W / 2, H / 2, H * 0.28, W / 2, H / 2, H * 0.72);
        vgrd.addColorStop(0, "rgba(0,0,0,0)");
        vgrd.addColorStop(1, "rgba(0,0,0,0.72)");
        ctx.fillStyle = vgrd;
        ctx.fillRect(0, 0, W, H);
        ctx.restore();

        // Pass 6 — tactical reticle: central crosshair + range hash marks
        ctx.save();
        const cx = W / 2, cy = H / 2;
        ctx.strokeStyle = "rgba(34,255,70,0.75)";
        ctx.lineWidth = 1;
        // Crosshair arms (gap in centre)
        const gap = 18, arm = 42;
        ctx.beginPath();
        ctx.moveTo(cx - gap - arm, cy); ctx.lineTo(cx - gap, cy);
        ctx.moveTo(cx + gap, cy);       ctx.lineTo(cx + gap + arm, cy);
        ctx.moveTo(cx, cy - gap - arm); ctx.lineTo(cx, cy - gap);
        ctx.moveTo(cx, cy + gap);       ctx.lineTo(cx, cy + gap + arm);
        ctx.stroke();
        // Centre dot
        ctx.fillStyle = "rgba(34,255,70,0.9)";
        ctx.beginPath(); ctx.arc(cx, cy, 2.5, 0, Math.PI * 2); ctx.fill();
        // Range hash marks on bottom arm
        for (let r = 1; r <= 4; r++) {
          const hy = cy + gap + r * 9;
          const hw = r === 2 ? 6 : 3;
          ctx.beginPath(); ctx.moveTo(cx - hw, hy); ctx.lineTo(cx + hw, hy); ctx.stroke();
        }
        ctx.restore();

        // Pass 7 — corner tactical brackets
        ctx.save();
        ctx.strokeStyle = "rgba(34,255,70,0.55)";
        ctx.lineWidth = 1.5;
        const bSize = 18, bOff = 10;
        [[bOff, bOff, 1, 1], [W - bOff, bOff, -1, 1], [bOff, H - bOff, 1, -1], [W - bOff, H - bOff, -1, -1]].forEach(([bx, by, dx, dy]) => {
          ctx.beginPath();
          ctx.moveTo(bx + dx * bSize, by);
          ctx.lineTo(bx, by);
          ctx.lineTo(bx, by + dy * bSize);
          ctx.stroke();
        });
        ctx.restore();

        // Pass 8 — top HUD bar
        const t = Date.now();
        const blinkOn = Math.floor(t / 700) % 2 === 0;
        ctx.save();
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(0, 0, W, 28);
        ctx.fillStyle = "#22ff46";
        ctx.font = "bold 9px monospace";
        ctx.fillText("GEN-3+ NVG  ◆  940nm IR", 10, 12);
        ctx.fillText(`GAIN: AUTO +${(36 + Math.sin(t / 2000) * 2).toFixed(1)}dB`, 10, 23);
        ctx.fillStyle = blinkOn ? "#22ff46" : "rgba(34,255,70,0.3)";
        ctx.fillText("● ACTIVE", W - 64, 12);
        ctx.fillStyle = "#22ff46";
        ctx.fillText(`ZOOM ×${zoomLevel.toFixed(1)}`, W - 64, 23);
        ctx.restore();

        // Pass 9 — bottom status bar
        ctx.save();
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(0, H - 22, W, 22);
        ctx.fillStyle = "rgba(34,255,70,0.8)";
        ctx.font = "8px monospace";
        const hh = String(new Date().getHours()).padStart(2, "0");
        const mm = String(new Date().getMinutes()).padStart(2, "0");
        const ss = String(new Date().getSeconds()).padStart(2, "0");
        ctx.fillText(`${hh}:${mm}:${ss}Z  ◆  OPFOR-SCAN  ◆  IR-SIG: ${blinkOn ? "DETECTED" : "SCANNING..."}  ◆  TUBE: OK`, 10, H - 8);
        ctx.restore();

        // Pass 10 — Sobel edge enhancement
        {
          const edgeData = ctx.getImageData(0, 0, W, H);
          const ed = edgeData.data;
          const edgeOut = new Uint8ClampedArray(ed.length);
          for (let epy = 1; epy < H - 1; epy++) {
            for (let epx = 1; epx < W - 1; epx++) {
              const idx00 = ((epy - 1) * W + (epx - 1)) * 4;
              const idx01 = ((epy - 1) * W + epx) * 4;
              const idx02 = ((epy - 1) * W + (epx + 1)) * 4;
              const idx10 = (epy * W + (epx - 1)) * 4;
              const idx12 = (epy * W + (epx + 1)) * 4;
              const idx20 = ((epy + 1) * W + (epx - 1)) * 4;
              const idx21 = ((epy + 1) * W + epx) * 4;
              const idx22 = ((epy + 1) * W + (epx + 1)) * 4;
              const g00 = ed[idx00] * 0.299 + ed[idx00+1] * 0.587 + ed[idx00+2] * 0.114;
              const g01 = ed[idx01] * 0.299 + ed[idx01+1] * 0.587 + ed[idx01+2] * 0.114;
              const g02 = ed[idx02] * 0.299 + ed[idx02+1] * 0.587 + ed[idx02+2] * 0.114;
              const g10 = ed[idx10] * 0.299 + ed[idx10+1] * 0.587 + ed[idx10+2] * 0.114;
              const g12 = ed[idx12] * 0.299 + ed[idx12+1] * 0.587 + ed[idx12+2] * 0.114;
              const g20 = ed[idx20] * 0.299 + ed[idx20+1] * 0.587 + ed[idx20+2] * 0.114;
              const g21 = ed[idx21] * 0.299 + ed[idx21+1] * 0.587 + ed[idx21+2] * 0.114;
              const g22 = ed[idx22] * 0.299 + ed[idx22+1] * 0.587 + ed[idx22+2] * 0.114;
              const gx = -g00 - 2 * g10 - g20 + g02 + 2 * g12 + g22;
              const gy = -g00 - 2 * g01 - g02 + g20 + 2 * g21 + g22;
              const mag = Math.min(255, Math.sqrt(gx * gx + gy * gy));
              const pi = (epy * W + epx) * 4;
              edgeOut[pi] = 0;
              edgeOut[pi+1] = Math.round(mag);
              edgeOut[pi+2] = 0;
              edgeOut[pi+3] = mag > 20 ? 255 : 0;
            }
          }
          const edgeCanvas = document.createElement("canvas");
          edgeCanvas.width = W; edgeCanvas.height = H;
          const eCtx = edgeCanvas.getContext("2d");
          if (eCtx) {
            const edgeImgData = eCtx.createImageData(W, H);
            edgeImgData.data.set(edgeOut);
            eCtx.putImageData(edgeImgData, 0, 0);
            ctx.save();
            ctx.globalCompositeOperation = "screen";
            ctx.globalAlpha = 0.4;
            ctx.drawImage(edgeCanvas, 0, 0);
            ctx.restore();
          }
        }

        // Pass 11 — Temporal grain (deterministic, time-varying)
        {
          const grainCanvas = document.createElement("canvas");
          grainCanvas.width = W; grainCanvas.height = H;
          const gCtx = grainCanvas.getContext("2d");
          if (gCtx) {
            const gImg = gCtx.createImageData(W, H);
            const gd = gImg.data;
            const tGrain = Date.now();
            for (let gpy = 0; gpy < H; gpy++) {
              for (let gpx = 0; gpx < W; gpx++) {
                const grainVal = Math.round(127 + 127 * Math.sin(tGrain * 0.07 + gpx * 0.03 + gpy * 0.07));
                const gi = (gpy * W + gpx) * 4;
                gd[gi] = grainVal; gd[gi+1] = grainVal; gd[gi+2] = grainVal; gd[gi+3] = 255;
              }
            }
            gCtx.putImageData(gImg, 0, 0);
            ctx.save();
            ctx.globalCompositeOperation = "overlay";
            ctx.globalAlpha = 0.12;
            ctx.drawImage(grainCanvas, 0, 0);
            ctx.restore();
          }
        }

        // Pass 12 — IR range estimator bar (right edge, military NVG stadia)
        {
          ctx.save();
          const barX12 = W - 36;
          const barTop = 35;
          const barBot = H - 30;
          const barH12 = barBot - barTop;
          ctx.fillStyle = "rgba(0,0,0,0.45)";
          ctx.fillRect(barX12 - 2, barTop, 30, barH12);
          ctx.strokeStyle = "rgba(34,255,70,0.6)";
          ctx.lineWidth = 1;
          ctx.strokeRect(barX12 - 2, barTop, 30, barH12);
          ctx.fillStyle = "rgba(34,255,70,0.8)";
          ctx.font = "6px monospace";
          const distLabels12: Array<[string, number]> = [["50m", 0.08], ["100m", 0.28], ["200m", 0.56], ["400m", 0.88]];
          distLabels12.forEach(([dlabel, frac]) => {
            const dy = barTop + frac * barH12;
            ctx.beginPath(); ctx.moveTo(barX12 - 2, dy); ctx.lineTo(barX12 + 8, dy); ctx.stroke();
            ctx.fillText(dlabel, barX12 + 10, dy + 3);
          });
          ctx.fillStyle = "rgba(34,255,70,0.6)";
          ctx.font = "bold 6px monospace";
          ctx.fillText("RNG", barX12, barTop - 5);
          ctx.restore();
        }

        // Pass 13 — Azimuth compass strip (top edge, 20px tall)
        {
          ctx.save();
          ctx.fillStyle = "rgba(0,0,0,0.6)";
          ctx.fillRect(0, 0, W, 20);
          const tCompass = Date.now();
          const heading13 = Math.sin(tCompass / 8000) * 15;
          nvgHeadingRef.current = heading13;
          ctx.strokeStyle = "rgba(34,255,70,0.55)";
          ctx.lineWidth = 0.8;
          ctx.fillStyle = "rgba(34,255,70,0.85)";
          ctx.font = "bold 7px monospace";
          const compassLabels: Array<[string, number]> = [
            ["N", 0], ["NE", 45], ["E", 90], ["SE", 135],
            ["S", 180], ["SW", 225], ["W", 270], ["NW", 315]
          ];
          compassLabels.forEach(([clabel, deg]) => {
            const offsetDeg = deg - heading13;
            const norm13 = ((offsetDeg % 360) + 360) % 360;
            const frac13 = norm13 / 360;
            const cx13 = frac13 * W;
            if (cx13 >= 0 && cx13 <= W) {
              ctx.beginPath(); ctx.moveTo(cx13, 12); ctx.lineTo(cx13, 20); ctx.stroke();
              ctx.textAlign = "center";
              ctx.fillText(clabel, cx13, 10);
            }
          });
          // minor degree ticks
          ctx.strokeStyle = "rgba(34,255,70,0.25)";
          for (let deg10 = 0; deg10 < 360; deg10 += 10) {
            const offsetDeg10 = deg10 - heading13;
            const norm10 = ((offsetDeg10 % 360) + 360) % 360;
            const frac10 = norm10 / 360;
            const cx10 = frac10 * W;
            if (cx10 >= 0 && cx10 <= W) {
              ctx.beginPath(); ctx.moveTo(cx10, 16); ctx.lineTo(cx10, 20); ctx.stroke();
            }
          }
          ctx.textAlign = "left";
          // Center marker
          ctx.strokeStyle = "rgba(34,255,70,0.9)";
          ctx.lineWidth = 1.5;
          ctx.beginPath(); ctx.moveTo(W/2, 12); ctx.lineTo(W/2, 20); ctx.stroke();
          ctx.restore();
        }
      }

    // Continuous loop of animation for targets tracking at 60 FPS
      animId = requestAnimationFrame(renderCanvas);
    };

    renderCanvas();

    return () => {
      cancelAnimationFrame(animId);
      resizeObserver.disconnect();
    };
  }, [selectedPreset, filterMode, useLiveCamera, isScanning, zoomLevel, trackMotion]);

  // Click/press handler mapped coordinates on canvas to select active target
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();

    // Map mouse position to canvas coordinates
    const clickX = ((e.clientX - rect.left) / rect.width) * canvas.width;
    const clickY = ((e.clientY - rect.top) / rect.height) * canvas.height;

    // Feature 1 — Thermal palette toggle button hit test (bottom-left corner, 84px wide x 18px tall at TH-42)
    if (filterMode === "thermal") {
      const btnX = 4, btnY = canvas.height - 42, btnW = 80, btnH = 18;
      if (clickX >= btnX && clickX <= btnX + btnW && clickY >= btnY && clickY <= btnY + btnH) {
        const palettes: Array<"ironbow" | "rainbow" | "arctic" | "whiteHot"> = ["ironbow", "rainbow", "arctic", "whiteHot"];
        const idx = palettes.indexOf(thermalPaletteRef.current);
        thermalPaletteRef.current = palettes[(idx + 1) % palettes.length];
        return;
      }
    }

    const trackingPresets = [
      "spy_usb_charger",
      "spy_smoke_detector",
      "spy_mirror_clock",
      "spy_screw_head",
      "spy_covert_pen",
      "spy_teddy_eye",
      "room_router"
    ];
    
    const time = Date.now();
    let clickedPresetId: string | null = null;
    
    for (let i = 0; i < trackingPresets.length; i++) {
      const presetId = trackingPresets[i];
      const pos = getTargetPosition(presetId, i, time, canvas.width, canvas.height);
      const pad = 24; // Easy clickable hot target range padding
      if (
        clickX >= pos.x - pad &&
        clickX <= pos.x + pos.w + pad &&
        clickY >= pos.y - pad &&
        clickY <= pos.y + pos.h + pad
      ) {
        clickedPresetId = presetId;
        break;
      }
    }
    
    if (clickedPresetId) {
      const found = PRESET_SCENARIOS.find(p => p.id === clickedPresetId);
      if (found && onSelectPreset) {
        onSelectPreset(found);
        
        // Dynamic cute beep chirp audio synth confirmation feedback
        try {
          const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
          if (AudioContextClass) {
            const ctx = new AudioContextClass();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = "sine";
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            gain.gain.setValueAtTime(0.04, ctx.currentTime);
            gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.18);
            osc.start();
            osc.stop(ctx.currentTime + 0.18);
          }
        } catch (soundErr) {}
      }
    }
  };

  // Click handler to manually snap a canvas/cam frame is sending to router
  const triggerManualCapture = () => {
    const snapshot = canvasRef.current;
    if (!snapshot) {
      alert("الرجاء تشغيل النموذج أو الكاميرا أولاً لالتقاط لقطة مستهدفة.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Grab EXACT representation of filtered canvas layout
    ctx.drawImage(snapshot, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg");

    const filterLabel = filterMode.toUpperCase();
    const nameHint = useLiveCamera 
      ? `Live Scan Snapshot (${filterLabel})` 
      : (selectedPreset ? `${selectedPreset.name} (${filterLabel})` : `Custom Target (${filterLabel})`);

    // Turn off live camera state so the viewport collapses back perfectly, showing results in dashboard!
    if (useLiveCamera) {
      setUseLiveCamera(false);
    }

    onImageCaptured(dataUrl, nameHint, forensicMode);
  };

  // Drag and drop event handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processUploadedFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("Invalid file: Must upload a standard photographic image.");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        onImageCaptured(e.target.result as string, file.name.substring(0, 20), forensicMode);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processUploadedFile(e.dataTransfer.files[0]);
    }
  };

  const handleManualUploadClick = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processUploadedFile(e.target.files[0]);
    }
  };

  const devSpecs = detectCameraSpecifications();

  // IMMERSIVE FULL SCREEN VIEW LAYOUT (Active Camera Mode)
  if (useLiveCamera) {
    return (
      <div 
        id="camera-fullscreen-viewport" 
        className="fixed inset-0 z-[100] bg-slate-950 w-screen h-screen overflow-hidden select-none font-sans"
      >
        {/* Active webcam stream layer (invisible) */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="absolute opacity-0 pointer-events-none"
          style={{ width: "1px", height: "1px" }}
        ></video>

        {/* High resolution tech canvas preview mapping - Stretched strictly to 100% of the screen */}
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          onMouseDown={handleCanvasClick}
          className="absolute inset-0 w-full h-full object-cover z-0 cursor-pointer"
        />

        {/* Floating cinematic grid scan lines for a premium sci-fi feel */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(18,24,38,0.1),rgba(18,24,38,0.15))] opacity-40 pointer-events-none z-10"></div>

        {/* Fullscreen HUD HeaderOverlay */}
        <div className="absolute top-4 left-4 right-4 z-30 flex justify-between items-center bg-slate-900/85 border border-slate-800/80 p-3 rounded-xl shadow-2xl backdrop-blur-md">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 bg-red-500 rounded-full animate-ping"></span>
            <div>
              <span className="font-mono text-[9px] text-red-400 font-extrabold tracking-widest block uppercase">
                🔴 LIVE SPECTRUM FULLSCREEN MONITORING HUD
              </span>
              <h2 className="text-xs font-bold font-sans tracking-tight text-slate-100 uppercase mt-0.5">
                تتبع الأهداف وتكبير الطيف الكهرومغناطيسي الذكي
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              setUseLiveCamera(false);
              setTrackMotion(false);
            }}
            className="bg-red-950/80 border border-red-500/50 hover:bg-red-900/60 text-red-300 rounded-lg px-3 py-1.5 text-xs font-bold font-mono tracking-wider transition cursor-pointer flex items-center gap-1 shadow-lg"
            title="خروج من شاشة الكاميرا الكاملة"
          >
            EXIT STREAM [إغلاق الشاشة]
          </button>
        </div>

        {/* Side target analyzer list & telemetry - floats on the right of the screen */}
        <div className="absolute top-20 right-4 w-60 z-30 flex flex-col gap-3 bg-slate-950/90 border border-slate-800 p-3.5 rounded-xl shadow-2xl backdrop-blur max-h-[72vh] overflow-y-auto text-right" dir="rtl">
          <div className="flex justify-between items-center border-b border-slate-850 pb-1.5">
            <h3 className="font-extrabold text-[11px] text-emerald-400 flex items-center gap-1.5">
              <span>🎯</span>
              <span>رادار تتبع الحركة الواقعي</span>
            </h3>
          </div>

          <div className="flex flex-col gap-1.5">
            <button
              onClick={() => setTrackMotion(!trackMotion)}
              className={`p-2 rounded-lg border text-right transition flex items-center justify-between gap-1.5 ${
                trackMotion
                  ? "bg-slate-900 border-red-500 text-slate-100 shadow-[0_0_10px_rgba(239,68,68,0.2)]"
                  : "bg-slate-950/80 border-slate-850 hover:border-slate-800 text-slate-300"
              }`}
            >
              <span className="text-[10px] font-bold">تفعيل تتبع الأجسام المتحركة الحية</span>
              <span className={`w-3 h-3 rounded-full ${trackMotion ? "bg-red-500 animate-pulse" : "bg-slate-700"}`}></span>
            </button>
          </div>
          
          <div className="mt-1 text-[9px] text-slate-400 font-mono">
            {trackMotion && motionRectRef.current?.active ? "جاري تعقب هدف متحرك بمجال الرؤية..." : (trackMotion ? "جاري محاكاة وتتبع مسارات الأجسام..." : "ميزة التتبع متوقفة")}
          </div>

          {trackMotion && (
            <div className="flex flex-col gap-1.5 border-t border-slate-850 pt-2.5 mt-1">
              <span className="text-[10px] font-sans font-extrabold text-slate-350 block text-right">
                المستهدفات المتحركة النشطة [ACTIVE TARGETS]:
              </span>
              <p className="text-[8.5px] text-slate-550 leading-tight">
                اضغط على أي مُستهدَف على الشاشة مباشرةً أو اختره من القائمة أدناه لقفل التتبع وتحميل كامل بياناته الأمنية:
              </p>
              <div className="flex flex-col gap-1 max-h-[35vh] overflow-y-auto pr-1 no-scrollbar text-right">
                {[
                  "spy_usb_charger",
                  "spy_smoke_detector",
                  "spy_mirror_clock",
                  "spy_screw_head",
                  "spy_covert_pen",
                  "spy_teddy_eye",
                  "room_router"
                ].map((tid, idx) => {
                  const pItem = PRESET_SCENARIOS.find(p => p.id === tid);
                  if (!pItem) return null;
                  const isCurrent = selectedPreset?.id === pItem.id;
                  return (
                    <button
                      key={pItem.id}
                      onClick={() => onSelectPreset && onSelectPreset(pItem)}
                      className={`w-full p-2 rounded-lg text-right text-[10px] border transition flex items-center justify-between gap-2 cursor-pointer ${
                        isCurrent
                          ? "bg-red-950/50 border-red-500 text-red-200 font-bold shadow-[0_0_8px_rgba(239,68,68,0.15)]"
                          : "bg-slate-950 border-slate-900 text-slate-400 hover:border-slate-800 hover:text-slate-200"
                      }`}
                    >
                      <div className="flex flex-col text-right truncate">
                        <span className="font-semibold block truncate max-w-[150px]">{pItem.name.split(" (")[0]}</span>
                        <span className="text-[7.5px] font-mono text-slate-500 block">SPD: {(0.6 + (idx * 0.15)).toFixed(1)}m/s // CONF: {pItem.confidence}%</span>
                      </div>
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${isCurrent ? "bg-red-500 animate-ping" : "bg-emerald-500"}`}></span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Minimalized/Expanded Live Zoom Widget Floating Overlay overlaying on the left side/corner dynamically */}
        <div className="absolute bottom-24 right-4 z-30">
          {zoomMinimized ? (
            <button
              type="button"
              onClick={() => setZoomMinimized(false)}
              className="flex items-center gap-1.5 bg-slate-950/95 border border-emerald-500/45 text-emerald-400 rounded-full py-1.5 px-3 font-mono font-bold text-xs shadow-2xl hover:bg-slate-900 transition animate-pulse cursor-pointer"
              title="توسيع التقريب الزووم"
            >
              <span>🔍 {zoomLevel.toFixed(zoomLevel >= 10 ? 0 : 1)}x</span>
            </button>
          ) : (
            <div className="flex flex-col gap-1.5 bg-slate-950/95 border border-slate-800 text-slate-100 rounded-xl p-2.5 shadow-2xl backdrop-blur w-44">
              <div className="flex items-center justify-between font-mono">
                <span className="text-[8px] text-slate-400 font-bold uppercase">التقريب الرقمي</span>
                <button
                  type="button"
                  onClick={() => setZoomMinimized(true)}
                  className="text-[8px] text-red-450 hover:text-red-400 font-bold px-1.5 py-0.5 rounded bg-red-950/20 border border-red-900/30 cursor-pointer"
                >
                  ✕ تصغير
                </button>
              </div>
              
              <div className="flex items-center justify-between gap-1 font-mono">
                <button
                  type="button"
                  onClick={() => {
                    setZoomLevel((prev) => {
                      if (prev <= 2) return Math.max(1, Number((prev - 0.2).toFixed(1)));
                      if (prev <= 5) return Math.max(1, Number((prev - 0.5).toFixed(1)));
                      if (prev <= 10) return Math.max(1, prev - 1);
                      if (prev <= 30) return Math.max(1, prev - 5);
                      return Math.max(1, prev - 10);
                    });
                  }}
                  disabled={zoomLevel <= 1}
                  className="w-6 h-6 flex items-center justify-center rounded bg-slate-900 border border-slate-800 disabled:opacity-30 hover:border-emerald-500 hover:text-emerald-400 font-extrabold text-[12px] text-center transition cursor-pointer"
                >
                  -
                </button>
                
                <span className="text-xs text-emerald-400 font-extrabold tracking-tight text-center flex-1">
                  {zoomLevel.toFixed(zoomLevel >= 10 ? 0 : 1)}x
                </span>

                <button
                  type="button"
                  onClick={() => {
                    setZoomLevel((prev) => {
                      if (prev < 2) return Math.min(100, Number((prev + 0.2).toFixed(1)));
                      if (prev < 5) return Math.min(100, Number((prev + 0.5).toFixed(1)));
                      if (prev < 10) return Math.min(100, prev + 1);
                      if (prev < 30) return Math.min(100, prev + 5);
                      return Math.min(100, prev + 10);
                    });
                  }}
                  disabled={zoomLevel >= 100}
                  className="w-6 h-6 flex items-center justify-center rounded bg-slate-900 border border-slate-800 disabled:opacity-30 hover:border-emerald-500 hover:text-emerald-400 font-extrabold text-[12px] text-center transition cursor-pointer"
                >
                  +
                </button>
              </div>

              {/* Quick jump presets inside dynamic panel */}
              <div className="flex gap-1 justify-between mt-1 pt-1.5 border-t border-slate-850 font-mono">
                {[1, 5, 10, 50, 100].map((z) => (
                  <button
                    key={z}
                    type="button"
                    onClick={() => { setZoomLevel(z); setZoomMinimized(true); }}
                    className={`py-0.5 px-1 text-[8px] font-bold rounded border transition flex-1 text-center cursor-pointer ${
                      Math.abs(zoomLevel - z) < 0.1
                        ? "bg-emerald-500 text-slate-950 border-emerald-400 font-black"
                        : "bg-slate-900 text-slate-400 border-slate-850 hover:text-slate-100"
                    }`}
                  >
                    {z}x
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Device specifications HUD box on the left */}
        <div className="absolute top-20 left-4 bg-slate-950/90 border border-emerald-500/30 p-2.5 rounded-xl flex flex-col gap-1 z-20 text-[10px] font-mono leading-tight backdrop-blur max-w-[280px]">
          <div className="text-emerald-400 font-extrabold uppercase flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            {devSpecs.brand}
          </div>
          <div className="text-slate-400 mt-0.5">Sensor: {devSpecs.sensor}</div>
          <div className="text-slate-400">Hardware Res: {devSpecs.res}</div>
          <div className="text-emerald-500/95 font-bold mt-1 text-[9px]">{devSpecs.status}</div>
          <div className="text-slate-500 text-[8px] mt-0.5 font-bold">Zoom Range: {devSpecs.peakZoom}</div>
        </div>

        {/* Active scan status bottom stats over the background map */}
        <div className="absolute bottom-24 left-4 bg-slate-950/85 border border-slate-800 p-2.5 rounded-xl text-[9px] font-mono text-slate-300 flex flex-col gap-0.5 z-20">
          <div>SIGNAL RANGE: COMPLIANT</div>
          <div>FPS: 60.0 // LATENCY: 8ms</div>
          <div>UHD BUFFER: OPTIC-LINK A++</div>
        </div>

        {/* Laser scanner effect for the full screen view */}
        {isScanning && (
          <div
            id="glowing-laser-strip-fullscreen"
            style={{ top: `${laserY}%` }}
            className={`absolute left-0 w-full h-0.5 pointer-events-none transition-all duration-75 z-10 ${
              filterMode === "thermal"
                ? "bg-gradient-to-r from-transparent via-orange-500 to-transparent shadow-[0_0_12px_rgba(249,115,22,0.8)]"
                : filterMode === "stealth"
                ? "bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_rgba(6,182,212,0.8)]"
                : "bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_12px_rgba(16,185,129,0.8)]"
            }`}
          ></div>
        )}

        {/* Sci-Fi Targeting corner bracket borders */}
        <div className="absolute top-6 left-6 w-12 h-12 border-t-4 border-l-4 border-emerald-500/50 rounded-tl-xl pointer-events-none z-20"></div>
        <div className="absolute top-6 right-6 w-12 h-12 border-t-4 border-r-4 border-emerald-500/50 rounded-tr-xl pointer-events-none z-20"></div>
        <div className="absolute bottom-6 left-6 w-12 h-12 border-b-4 border-l-4 border-emerald-500/50 rounded-bl-xl pointer-events-none z-20"></div>
        <div className="absolute bottom-6 right-6 w-12 h-12 border-b-4 border-r-4 border-emerald-500/50 rounded-br-xl pointer-events-none z-20"></div>

        {/* Stretched HUD crosshair at target or center */}
        {trackMotion && motionRectRef.current && motionRectRef.current.active ? (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 pointer-events-none flex flex-col items-center justify-center text-red-500 z-10">
            <div className="text-[9px] font-mono font-black tracking-widest uppercase bg-slate-950/80 px-2 py-0.5 rounded border border-red-500 animate-pulse mb-2 text-center w-max">
              🎯 LOCK: MOTION TRACKING
            </div>
            <div className="w-20 h-20 border border-dashed border-red-500/40 rounded-full flex items-center justify-center animate-spin" style={{ animationDuration: "12s" }}>
              <div className="w-12 h-12 border border-red-500/30 rounded-full"></div>
            </div>
          </div>
        ) : (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 border border-emerald-500/30 rounded-full flex items-center justify-center pointer-events-none z-10">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping"></div>
            <div className="absolute w-8 h-0.5 bg-emerald-500/50"></div>
            <div className="absolute h-8 w-0.5 bg-emerald-500/50"></div>
          </div>
        )}

        {/* Controls Panel Bottom Hub - semi transparent floating glass */}
        <div className="absolute bottom-4 left-4 right-4 z-30 flex flex-col gap-2.5 bg-slate-900/90 border border-slate-800/80 p-3 rounded-xl shadow-2xl backdrop-blur-md">
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Filter Modes */}
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-mono text-slate-400 font-bold uppercase mr-1.5">FILTERS:</span>
              <div className="flex items-center gap-1 bg-slate-950/90 p-1 rounded-lg border border-slate-850">
                <button
                  onClick={() => setFilterMode("normal")}
                  className={`text-[10px] px-2.5 py-1 rounded font-semibold transition ${filterMode === "normal" ? "bg-slate-800 text-emerald-400 shadow" : "text-slate-400 hover:text-slate-200"}`}
                >
                  Normal
                </button>
                <button
                  onClick={() => setFilterMode("thermal")}
                  className={`text-[10px] px-2.5 py-1 rounded font-semibold transition ${filterMode === "thermal" ? "bg-slate-800 text-orange-400 shadow" : "text-slate-400 hover:text-slate-200"}`}
                >
                  Thermal ID
                </button>
                <button
                  onClick={() => setFilterMode("stealth")}
                  className={`text-[10px] px-2.5 py-1 rounded font-semibold transition ${filterMode === "stealth" ? "bg-slate-800 text-cyan-400 shadow" : "text-slate-400 hover:text-slate-200"}`}
                >
                  Stealth Wave
                </button>
                <button
                  onClick={() => setFilterMode("nightvision")}
                  className={`text-[10px] px-2.5 py-1 rounded font-semibold transition ${filterMode === "nightvision" ? "bg-green-950/80 text-green-400 border border-green-800 shadow" : "text-slate-400 hover:text-slate-200"}`}
                >
                  🌙 Night Vision (رؤية ليلية)
                </button>
              </div>
            </div>

            {/* Primary triggers */}
            <div className="flex-1 max-w-sm flex gap-3">
              <button
                id="btn-scan-trigger-fullscreen"
                disabled={isScanning}
                onClick={triggerManualCapture}
                className="flex-1 bg-emerald-600 border border-emerald-500 hover:bg-emerald-500 active:bg-emerald-700 disabled:bg-slate-800 disabled:border-slate-700 disabled:text-slate-500 text-slate-950 py-2.5 px-4 rounded-xl text-xs font-black font-sans tracking-wider transition flex items-center justify-center gap-2 shadow cursor-pointer"
              >
                <Sparkles className="w-4 h-4 animate-spin-slow" />
                ANALYZE TARGET [تحليل طيفي عميق ⚡]
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // STANDARD IN-DASHBOARD WIDGET LAYOUT (When Live camera stream is closed)
  return (
    <div className="w-full flex flex-col bg-slate-900 border border-slate-800 rounded-2xl p-4 gap-4 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-2.5-z-10">
        <div>
          <h2 className="text-sm font-extrabold tracking-wider text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-slate-600 rounded-full"></span>
            ACTIVE VIEWPORT SCANNER
          </h2>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">
            DEVICE MODE: {useLiveCamera ? "LIVE MOBILE SATELLITE" : "DIGITAL GRAPH MODELING"}
          </p>
        </div>

        {/* Viewport Filters */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 flex-wrap">
          <button
            onClick={() => setFilterMode("normal")}
            className={`text-[10px] px-2 py-1 rounded font-semibold transition ${filterMode === "normal" ? "bg-slate-800 text-emerald-400 shadow" : "text-slate-400 hover:text-slate-200"}`}
          >
            Normal
          </button>
          <button
            onClick={() => setFilterMode("thermal")}
            className={`text-[10px] px-2 py-1 rounded font-semibold transition ${filterMode === "thermal" ? "bg-slate-800 text-orange-400 shadow" : "text-slate-400 hover:text-slate-200"}`}
          >
            Thermal ID
          </button>
          <button
            onClick={() => setFilterMode("stealth")}
            className={`text-[10px] px-2 py-1 rounded font-semibold transition ${filterMode === "stealth" ? "bg-slate-800 text-cyan-400 shadow" : "text-slate-400 hover:text-slate-200"}`}
          >
            Stealth Wave
          </button>
          <button
            onClick={() => setFilterMode("nightvision")}
            className={`text-[10px] px-2 py-1 rounded font-semibold transition ${filterMode === "nightvision" ? "bg-green-950/80 text-green-400 border border-green-700/55 shadow" : "text-slate-400 hover:text-slate-200"}`}
          >
            🌙 Night Vision (رؤية ليلية)
          </button>
        </div>
      </div>

      {/* Main Viewfinder Frame wrapper */}
      <div
        id="camera-viewfinder"
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative aspect-[4/3] w-full rounded-xl overflow-hidden border-2 transition-all ${
          dragActive
            ? "border-emerald-400 bg-emerald-900/10 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
            : "border-slate-800 bg-slate-950"
        }`}
      >
        {/* Real Live Video Camera layer - invisible, feeds real-time canvas buffer */}
        {useLiveCamera && (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="absolute opacity-0 pointer-events-none"
            style={{ width: "1px", height: "1px" }}
          ></video>
        )}

        {/* Unified High-Fidelity Tech Canvas Layer */}
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          onMouseDown={handleCanvasClick}
          className="absolute inset-0 w-full h-full object-cover z-0 cursor-pointer"
        />

        {/* HUD Scanner Graphics Overlays */}
        <div id="hud-corner-tl" className="absolute top-4 left-4 w-5 h-5 border-t-2 border-l-2 border-emerald-500 rounded-tl pointer-events-none"></div>
        <div id="hud-corner-tr" className="absolute top-4 right-4 w-5 h-5 border-t-2 border-r-2 border-emerald-500 rounded-tr pointer-events-none"></div>
        <div id="hud-corner-bl" className="absolute bottom-4 left-4 w-5 h-5 border-b-2 border-l-2 border-emerald-500 rounded-bl pointer-events-none"></div>
        <div id="hud-corner-br" className="absolute bottom-4 right-4 w-5 h-5 border-b-2 border-r-2 border-emerald-500 rounded-br pointer-events-none"></div>

        {/* Moving Cross Hair Center */}
        <div id="scanner-reticle" className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 border border-emerald-500/30 rounded-full flex items-center justify-center pointer-events-none">
          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></div>
          <div className="absolute w-6 h-0.5 bg-emerald-500/55"></div>
          <div className="absolute h-6 w-0.5 bg-emerald-500/55"></div>
        </div>

        {/* Laser Scanning Line Sweep */}
        {isScanning && (
          <div
            id="glowing-laser-strip"
            style={{ top: `${laserY}%` }}
            className={`absolute left-0 w-full h-0.5 pointer-events-none transition-all duration-75 z-10 ${
              filterMode === "thermal"
                ? "bg-gradient-to-r from-transparent via-orange-500 to-transparent shadow-[0_0_12px_rgba(249,115,22,0.8)]"
                : filterMode === "stealth"
                ? "bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_rgba(6,182,212,0.8)]"
                : "bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_12px_rgba(16,185,129,0.8)]"
            }`}
          ></div>
        )}

        {/* Drag and drop full panel blocker */}
        {dragActive && (
          <div className="absolute inset-0 bg-emerald-950/80 backdrop-blur-xs flex flex-col justify-center items-center gap-3 z-20 text-emerald-400 border border-emerald-400">
            <ImageUp className="w-12 h-12 animate-bounce" />
            <span className="font-mono text-sm tracking-widest font-extrabold animate-pulse">
              DEPOSIT PHYSICAL OPTICAL TARGET HERE
            </span>
          </div>
        )}

        {/* Scanning telemetry warning stats */}
        <div className="absolute top-4 left-4 right-4 flex justify-between z-10 pointer-events-none select-none text-[9px] font-mono">
          <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 text-emerald-400 tracking-wider">
            AZIMUTH: 182.492° // ALT: +41°
          </div>
          <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 text-emerald-400 tracking-wider">
            ISO: 400 // SHUTTER: 1/800s
          </div>
        </div>

        {/* Camera block error tooltip */}
        {cameraError && (
          <div className="absolute inset-x-4 bottom-14 bg-red-950/90 border border-red-500/50 p-2 rounded text-red-200 text-[10px] flex items-start gap-1.5 z-10 font-mono">
            <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span>{cameraError}</span>
          </div>
        )}

        {/* Real Live Camera Zoom Control Overlay */}
        <div className="absolute bottom-4 right-4 flex flex-col gap-1.5 bg-slate-950/90 border border-slate-800 text-slate-100 rounded-xl p-2 z-20 shadow-xl backdrop-blur shrink-0 select-none font-mono w-[184px]">
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-slate-400 font-bold uppercase">سيرفر التقريب</span>
            <span className="text-[9px] text-emerald-400 font-bold">4K ZOOM</span>
          </div>
          
          <div className="flex items-center justify-between gap-1">
            <button
              type="button"
              onClick={() => {
                setZoomLevel((prev) => {
                  if (prev <= 2) return Math.max(1, Number((prev - 0.2).toFixed(1)));
                  if (prev <= 5) return Math.max(1, Number((prev - 0.5).toFixed(1)));
                  if (prev <= 10) return Math.max(1, prev - 1);
                  if (prev <= 30) return Math.max(1, prev - 5);
                  return Math.max(1, prev - 10);
                });
              }}
              disabled={zoomLevel <= 1}
              className="w-6 h-6 flex items-center justify-center rounded bg-slate-900 border border-slate-800 disabled:opacity-30 disabled:hover:border-slate-800 hover:border-emerald-500/50 hover:text-emerald-400 font-extrabold text-[13px] transition cursor-pointer text-center leading-none"
              title="تصغير الزוوم (Zoom Out)"
            >
              -
            </button>
            
            <span className="text-[11px] text-emerald-400 font-black tracking-tight text-center flex-1">
              {zoomLevel.toFixed(zoomLevel >= 10 ? 0 : 1)}x
            </span>

            <button
              type="button"
              onClick={() => {
                setZoomLevel((prev) => {
                  if (prev < 2) return Math.min(100, Number((prev + 0.2).toFixed(1)));
                  if (prev < 5) return Math.min(100, Number((prev + 0.5).toFixed(1)));
                  if (prev < 10) return Math.min(100, prev + 1);
                  if (prev < 30) return Math.min(100, prev + 5);
                  return Math.min(100, prev + 10);
                });
              }}
              disabled={zoomLevel >= 100}
              className="w-6 h-6 flex items-center justify-center rounded bg-slate-900 border border-slate-800 disabled:opacity-30 disabled:hover:border-slate-800 hover:border-emerald-500/50 hover:text-emerald-400 font-extrabold text-[13px] transition cursor-pointer text-center leading-none"
              title="تكبير الزוوم (Zoom In)"
            >
              +
            </button>
          </div>

          {/* Quick jump presets */}
          <div className="flex gap-1 justify-between mt-0.5 pt-1.5 border-t border-slate-850">
            {[1, 5, 10, 50, 100].map((z) => (
              <button
                key={z}
                type="button"
                onClick={() => setZoomLevel(z)}
                className={`py-0.5 px-1.5 text-[9px] font-black rounded border transition flex-1 text-center ${
                  Math.abs(zoomLevel - z) < 0.1
                    ? "bg-emerald-500 text-slate-950 border-emerald-400"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                }`}
                title={`التقريب المباشر لـ x${z}`}
              >
                {z}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Control Buttons Panel */}
      <div className="grid grid-cols-2 gap-2.5">
        <button
          id="btn-toggle-camera"
          onClick={() => setUseLiveCamera(!useLiveCamera)}
          className={`py-2 px-3 rounded-lg border text-xs font-bold font-mono tracking-wide transition flex items-center justify-center gap-2 ${
            useLiveCamera
              ? "bg-red-900/20 border-red-500/50 text-red-300 hover:bg-red-900/30"
              : "bg-slate-950 border-slate-800 text-emerald-400 hover:border-emerald-500/50 hover:bg-slate-850"
          }`}
        >
          <Camera className="w-4 h-4" />
          {useLiveCamera ? "DISABLE STREAM" : "LIVE CAMERA STREAM"}
        </button>

        <button
          id="btn-scan-trigger"
          disabled={isScanning}
          onClick={triggerManualCapture}
          className="bg-emerald-600 border border-emerald-500 hover:bg-emerald-500 active:bg-emerald-700 disabled:bg-slate-800 disabled:border-slate-700 disabled:text-slate-500 text-slate-950 py-2 px-3 rounded-lg text-xs font-extrabold font-mono tracking-widest transition flex items-center justify-center gap-2 shadow"
        >
          <Sparkles className="w-4 h-4" />
          {isScanning ? "SWEEPING..." : "ANALYZE CAMERA"}
        </button>
      </div>

      {/* drag-and-drop manual upload pattern fallback */}
      <div className="w-full flex flex-col items-center justify-center border border-dashed border-slate-850 rounded-lg p-2 bg-slate-950/50">
        <label className="text-[11px] text-slate-400 font-mono text-center cursor-pointer hover:text-emerald-400 transition flex items-center gap-2">
          <span>Or manually drag & drop image or Click Here to upload:</span>
          <span className="text-[10px] px-1.5 py-0.5 bg-slate-800 rounded font-bold text-slate-200 hover:bg-emerald-600/25 transition">
            SELECT FILE
          </span>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleManualUploadClick}
            className="hidden"
          />
        </label>
      </div>

      {/* Dynamic Target-Tracking HUD controller segment */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 flex flex-col gap-3 mt-1" dir="rtl">
        <div className="flex justify-between items-center border-b border-slate-850 pb-2 flex-wrap gap-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <h3 className="font-sans font-extrabold text-xs text-slate-200">
              إعدادات التصوير والتحليل الحقيقي
            </h3>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 font-sans leading-relaxed text-right">
          هذا النظام يتيح لك التقاط صور واقعية والكشف عن ماهيتها الحقيقية. يمكنك الخيار بين التحليل العادي (بدون إضافات وهمية) أو تمكين التحليل الجنائي المتقدم:
        </p>

        <div className="flex flex-col gap-3">
          <button
            onClick={() => setForensicMode(!forensicMode)}
            className={`w-full p-2.5 rounded-lg border text-right transition flex items-center justify-between gap-1 cursor-pointer ${
              forensicMode
                ? "bg-slate-900 border-emerald-500 text-slate-100 shadow-[0_0_12px_rgba(16,185,129,0.15)]"
                : "bg-slate-950 border-slate-850 hover:border-slate-700 text-slate-300"
            }`}
          >
            <div className="flex flex-col gap-0.5">
              <span className="text-[11px] font-bold flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                تفعيل التحليل الجنائي الرقمي المتقدم (OSINT Forensics)
              </span>
              <span className="text-[9px] text-slate-500 font-mono block">يقدم تقريرًا فنيًا حول الإضاءة، والظلال، وبيانات الصورة</span>
            </div>
            <span className={`w-3 h-3 rounded-full flex-shrink-0 ${forensicMode ? "bg-emerald-500 animate-pulse" : "bg-slate-700"}`}></span>
          </button>

          <button
            onClick={() => setTrackMotion(!trackMotion)}
            className={`w-full p-2.5 rounded-lg border text-right transition flex items-center justify-between gap-1 cursor-pointer ${
              trackMotion
                ? "bg-slate-900 border-red-500 text-slate-100 shadow-[0_0_12px_rgba(239,68,68,0.15)]"
                : "bg-slate-950 border-slate-850 hover:border-slate-700 text-slate-300"
            }`}
          >
            <div className="flex flex-col gap-0.5">
              <span className="text-[11px] font-bold flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${trackMotion ? "bg-red-500 animate-ping" : "bg-slate-500"}`}></span>
                تتبع الأهداف وتحديد المستهدفات الحية (Active Target Tracking)
              </span>
              <span className="text-[9px] text-slate-500 font-mono block">يعرض الأهداف متحركة على الشاشة ويسهل اختيارها وعرض معلوماتها بمجرد الضغط عليها</span>
            </div>
            <span className={`w-3 h-3 rounded-full flex-shrink-0 ${trackMotion ? "bg-red-500 animate-pulse" : "bg-slate-700"}`}></span>
          </button>
        </div>

        {trackMotion && (
          <div className="flex flex-col gap-1.5 border-t border-slate-850 pt-2.5 mt-1">
            <span className="text-[10px] font-sans font-extrabold text-slate-350 block text-right">
              المستهدفات المتحركة النشطة على الشاشة [DYNAMIC TARGETS]:
            </span>
            <span className="text-[9px] text-slate-500 block text-right leading-tight">
              اضغط مباشرة على المستهدفات المتحركة أعلى شاشة العرض أو اختر من القائمة التالية لعرض كامل التفاصيل فورا:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-[180px] overflow-y-auto pr-1 no-scrollbar text-right mt-1">
              {[
                "spy_usb_charger",
                "spy_smoke_detector",
                "spy_mirror_clock",
                "spy_screw_head",
                "spy_covert_pen",
                "spy_teddy_eye",
                "room_router"
              ].map((tid, idx) => {
                const pItem = PRESET_SCENARIOS.find(p => p.id === tid);
                if (!pItem) return null;
                const isCurrent = selectedPreset?.id === pItem.id;
                return (
                  <button
                    key={pItem.id}
                    onClick={() => onSelectPreset && onSelectPreset(pItem)}
                    className={`p-2 rounded-lg text-right text-[10px] border transition flex items-center justify-between gap-1.5 cursor-pointer ${
                      isCurrent
                        ? "bg-red-950/40 border-red-500 text-red-250 font-bold shadow-[0_0_8px_rgba(239,68,68,0.12)]"
                        : "bg-slate-950 border-slate-900 text-slate-400 hover:border-slate-850 hover:text-slate-200"
                    }`}
                  >
                    <div className="flex flex-col text-right truncate">
                      <span className="font-semibold block truncate max-w-[130px]">{pItem.name.split(" (")[0]}</span>
                      <span className="text-[7.5px] font-mono text-slate-500 block">SPD: {(0.6 + (idx * 0.15)).toFixed(1)}m/s</span>
                    </div>
                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${isCurrent ? "bg-red-500 animate-ping" : "bg-emerald-500"}`}></span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
