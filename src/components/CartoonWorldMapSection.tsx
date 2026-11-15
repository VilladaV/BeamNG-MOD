import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type DragEvent,
  type PointerEvent as ReactPointerEvent,
} from 'react';
import {
  ChevronDown,
  ChevronUp,
  Cloud,
  CloudOff,
  Compass,
  Crosshair,
  Dice5,
  Globe,
  MapPin,
  Move,
  RotateCcw,
  Search,
  Sparkles,
  Trash2,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import {
  CARTOON_CONTINENTS,
  DEFAULT_REAL_MAP_PINS,
  WORLD_ALL_LAND_PATH,
  WORLD_GREAT_LAKES_PATH,
  WORLD_MAP_VIEWBOX,
} from '@/data/cartoonWorldMapData';
import {
  saveSharedWorldPins,
  subscribeToSharedWorldPins,
} from '@/lib/firebase';
import type { MapModItem } from '@/types/mods';

interface PinCoord {
  x: number;
  y: number;
}

type PinMap = Record<string, PinCoord>;
type DrawerFilter = 'all' | 'unplaced' | 'placed' | 'real' | 'fictional';

interface RegionPreset {
  id: string;
  label: string;
  zoom: number;
  focusX: number;
  focusY: number;
}

const STORAGE_KEY = 'beamng-cartoon-world-map-pins-v1';

const REGION_PRESETS: RegionPreset[] = [
  { id: 'world', label: '🌍 Mundo', zoom: 1, focusX: 50, focusY: 50 },
  { id: 'japan', label: '🗾 Japón', zoom: 4.2, focusX: 88.2, focusY: 31.8 },
  { id: 'europe', label: '🏰 Europa', zoom: 2.8, focusX: 50.5, focusY: 23.0 },
  { id: 'na', label: '🗽 Norteamérica', zoom: 2.3, focusX: 18.0, focusY: 32.5 },
  { id: 'sa', label: '🌴 Sudamérica', zoom: 2.5, focusX: 28.0, focusY: 64.0 },
  { id: 'oceania', label: '🦘 Oceanía', zoom: 2.8, focusX: 88.0, focusY: 73.0 },
];

const CARTOON_CLOUDS = [
  { id: 'c1', x: 64, y: 20, scale: 0.9, delay: '0s' },
  { id: 'c2', x: 202, y: 42, scale: 0.72, delay: '1.8s' },
  { id: 'c3', x: 358, y: 24, scale: 0.85, delay: '3.4s' },
  { id: 'c4', x: 32, y: 186, scale: 0.78, delay: '2.2s' },
  { id: 'c5', x: 368, y: 174, scale: 0.82, delay: '4.1s' },
];

const CARTOON_WAVES = [
  { id: 'w1', x: 14, y: 138, delay: '0s' },
  { id: 'w2', x: 188, y: 132, delay: '1.1s' },
  { id: 'w3', x: 196, y: 214, delay: '2.3s' },
  { id: 'w4', x: 334, y: 176, delay: '0.7s' },
  { id: 'w5', x: 444, y: 122, delay: '1.9s' },
];

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function computePanForFocus(zoom: number, focusX: number, focusY: number): PinCoord {
  if (zoom <= 1) return { x: 0, y: 0 };
  const minPan = -(zoom - 1) * 100;
  return {
    x: clamp(50 - zoom * focusX, minPan, 0),
    y: clamp(50 - zoom * focusY, minPan, 0),
  };
}

function clampPan(pan: PinCoord, zoom: number): PinCoord {
  if (zoom <= 1) return { x: 0, y: 0 };
  const minPan = -(zoom - 1) * 100;
  return {
    x: clamp(pan.x, minPan, 0),
    y: clamp(pan.y, minPan, 0),
  };
}

function loadInitialPins(validIds: Set<string>): PinMap {
  if (typeof window !== 'undefined') {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw !== null) {
        const parsed = JSON.parse(raw) as Record<string, unknown>;
        if (parsed && typeof parsed === 'object') {
          const restored: PinMap = {};
          for (const [id, coord] of Object.entries(parsed)) {
            if (!validIds.has(id) || !coord || typeof coord !== 'object') continue;
            const c = coord as { x?: unknown; y?: unknown };
            if (typeof c.x === 'number' && typeof c.y === 'number') {
              restored[id] = {
                x: clamp(c.x, 1.2, 98.8),
                y: clamp(c.y, 1.5, 98.5),
              };
            }
          }
          return restored;
        }
      }
    } catch {
      // Fallback to curated real-world starting pins below
    }
  }

  const defaults: PinMap = {};
  for (const [id, pin] of Object.entries(DEFAULT_REAL_MAP_PINS)) {
    if (validIds.has(id)) {
      defaults[id] = { x: pin.x, y: pin.y };
    }
  }
  return defaults;
}

/** Decorative SVG clouds, waves, terrain doodles, compass rose, and mini race boat. */
function CartoonWorldDecorations() {
  return (
    <g aria-hidden="true" className="pointer-events-none select-none">
      {/* Dashed treasure-map latitude & equator lines */}
      <line
        x1={0}
        y1={WORLD_MAP_VIEWBOX.height * 0.516}
        x2={WORLD_MAP_VIEWBOX.width}
        y2={WORLD_MAP_VIEWBOX.height * 0.516}
        stroke="#FFFFFF"
        strokeOpacity="0.45"
        strokeWidth="0.9"
        strokeDasharray="4 4"
      />
      <line
        x1={0}
        y1={WORLD_MAP_VIEWBOX.height * 0.25}
        x2={WORLD_MAP_VIEWBOX.width}
        y2={WORLD_MAP_VIEWBOX.height * 0.25}
        stroke="#FFFFFF"
        strokeOpacity="0.25"
        strokeWidth="0.7"
        strokeDasharray="2 5"
      />
      <line
        x1={0}
        y1={WORLD_MAP_VIEWBOX.height * 0.78}
        x2={WORLD_MAP_VIEWBOX.width}
        y2={WORLD_MAP_VIEWBOX.height * 0.78}
        stroke="#FFFFFF"
        strokeOpacity="0.25"
        strokeWidth="0.7"
        strokeDasharray="2 5"
      />

      {/* Animated comic ocean wave squiggles */}
      {CARTOON_WAVES.map((w) => (
        <g
          key={w.id}
          className="cartoon-wave"
          style={{ animationDelay: w.delay }}
        >
          <path
            d={`M ${w.x} ${w.y} q 4 -3.2 8 0 t 8 0 t 8 0`}
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="1.4"
            strokeLinecap="round"
            opacity="0.78"
          />
          <path
            d={`M ${w.x + 5} ${w.y + 4.5} q 3.5 -2.5 7 0 t 7 0`}
            fill="none"
            stroke="#E0F2FE"
            strokeWidth="1.1"
            strokeLinecap="round"
            opacity="0.65"
          />
        </g>
      ))}

      {/* Little comic sailboats in the oceans */}
      <g transform="translate(198, 92)">
        <path d="M 0 5 L 11 5 L 9 9 L 2 9 Z" fill="#FB7185" stroke="#18181b" strokeWidth="0.9" />
        <line x1="5.5" y1="5" x2="5.5" y2="-4" stroke="#18181b" strokeWidth="0.9" />
        <path d="M 6 -3.5 L 11 3.5 L 6 3.5 Z" fill="#FFFFFF" stroke="#18181b" strokeWidth="0.8" />
        <path d="M 5.5 -4 L 2 -2.5 L 5.5 -1 Z" fill="#FFBE0B" stroke="#18181b" strokeWidth="0.6" />
      </g>

      <g transform="translate(362, 198)">
        <path d="M 0 5 L 11 5 L 9 9 L 2 9 Z" fill="#FFBE0B" stroke="#18181b" strokeWidth="0.9" />
        <line x1="5.5" y1="5" x2="5.5" y2="-4" stroke="#18181b" strokeWidth="0.9" />
        <path d="M 6 -3.5 L 11 3.5 L 6 3.5 Z" fill="#FFFFFF" stroke="#18181b" strokeWidth="0.8" />
      </g>

      {/* Playful hand-drawn continent doodles (mountains, Fuji, cactus, pines) */}
      {/* Rockies */}
      <g transform="translate(58, 74)">
        <polygon points="0,8 4.5,0 9,8" fill="#D97706" stroke="#18181b" strokeWidth="0.8" />
        <polygon points="3,2.7 4.5,0 6,2.7 4.5,3.4" fill="#FFFFFF" />
      </g>
      {/* Andes */}
      <g transform="translate(120, 174)">
        <polygon points="0,9 5,0 10,9" fill="#15803D" stroke="#18181b" strokeWidth="0.8" />
        <polygon points="3.3,3 5,0 6.7,3 5,3.7" fill="#FFFFFF" />
      </g>
      {/* Alps */}
      <g transform="translate(244, 66)">
        <polygon points="0,6 3.5,0 7,6" fill="#7C3AED" stroke="#18181b" strokeWidth="0.7" />
        <polygon points="2.2,2 3.5,0 4.8,2" fill="#FFFFFF" />
      </g>
      {/* Himalayas */}
      <g transform="translate(348, 92)">
        <polygon points="0,9 5.5,0 11,9" fill="#E11D48" stroke="#18181b" strokeWidth="0.8" />
        <polygon points="3.5,3 5.5,0 7.5,3 5.5,4" fill="#FFFFFF" />
      </g>
      {/* Cute Sahara Palm/Dune & Pine in Siberia */}
      <path
        d="M 244 106 q 6 -4 12 0 M 252 108 q 6 -3.5 12 0"
        fill="none"
        stroke="#B45309"
        strokeWidth="1"
        strokeLinecap="round"
        opacity="0.75"
      />
      <g transform="translate(318, 43)">
        <polygon points="3,0 0,6 6,6" fill="#16A34A" stroke="#18181b" strokeWidth="0.7" />
        <rect x="2.3" y="6" width="1.4" height="2" fill="#78350F" />
      </g>

      {/* Puffy animated cartoon clouds */}
      {CARTOON_CLOUDS.map((c) => (
        <g
          key={c.id}
          transform={`translate(${c.x}, ${c.y}) scale(${c.scale})`}
        >
          <g className="cartoon-cloud" style={{ animationDelay: c.delay }}>
            <path
              d="M 6 14 h 22 a 5 5 0 0 0 0.5 -10 a 7 7 0 0 0 -13.5 -1.5 a 5.5 5.5 0 0 0 -9 4.5 a 4.5 4.5 0 0 0 0 7 Z"
              fill="#FFFFFF"
              fillOpacity="0.92"
              stroke="#18181b"
              strokeWidth="1.2"
              strokeLinejoin="round"
            />
          </g>
        </g>
      ))}

      {/* Ocean text labels */}
      <text
        x="184"
        y="112"
        textAnchor="middle"
        fill="#FFFFFF"
        fillOpacity="0.72"
        fontSize="5.6"
        fontWeight="900"
        letterSpacing="1.6"
      >
        OCÉANO ATLÁNTICO
      </text>
      <text
        x="34"
        y="148"
        textAnchor="middle"
        fill="#FFFFFF"
        fillOpacity="0.72"
        fontSize="5.4"
        fontWeight="900"
        letterSpacing="1.4"
      >
        PACÍFICO
      </text>
      <text
        x="348"
        y="164"
        textAnchor="middle"
        fill="#FFFFFF"
        fillOpacity="0.72"
        fontSize="5.4"
        fontWeight="900"
        letterSpacing="1.4"
      >
        OCÉANO ÍNDICO
      </text>

      {/* Playful Cartoon Compass Rose in bottom-left */}
      <g transform="translate(34, 228)">
        <circle cx="0" cy="0" r="18" fill="#FEF3C7" stroke="#18181b" strokeWidth="1.8" />
        <circle cx="0" cy="0" r="14" fill="none" stroke="#F59E0B" strokeWidth="0.9" strokeDasharray="2 2" />
        <polygon points="0,-13 3.2,-3 0,0 -3.2,-3" fill="#FB7185" stroke="#18181b" strokeWidth="0.8" />
        <polygon points="0,13 3.2,3 0,0 -3.2,3" fill="#FFFFFF" stroke="#18181b" strokeWidth="0.8" />
        <polygon points="13,0 3,3.2 0,0 3,-3.2" fill="#FFBE0B" stroke="#18181b" strokeWidth="0.8" />
        <polygon points="-13,0 -3,3.2 0,0 -3,-3.2" fill="#FFFFFF" stroke="#18181b" strokeWidth="0.8" />
        <circle cx="0" cy="0" r="2.2" fill="#18181b" />
        <text x="0" y="-14.6" textAnchor="middle" fontSize="5" fontWeight="900" fill="#18181b">N</text>
        <text x="0" y="17.8" textAnchor="middle" fontSize="4.6" fontWeight="900" fill="#18181b">S</text>
        <text x="15.5" y="1.6" textAnchor="middle" fontSize="4.6" fontWeight="900" fill="#18181b">E</text>
        <text x="-15.5" y="1.6" textAnchor="middle" fontSize="4.6" fontWeight="900" fill="#18181b">O</text>
      </g>
    </g>
  );
}

interface PinInspectorBubbleProps {
  map: MapModItem;
  coord: PinCoord;
  onStartReposition: () => void;
  onRemove: () => void;
  onClose: () => void;
}

/** Floating cartoon speech-bubble card inspecting the currently selected world pin. */
function PinInspectorBubble({
  map,
  coord,
  onStartReposition,
  onRemove,
  onClose,
}: PinInspectorBubbleProps) {
  const [realFailed, setRealFailed] = useState(false);
  const showSplit = Boolean(map.isRealWorld && map.realImageUrl && !realFailed);

  return (
    <div
      onPointerDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      className="absolute bottom-3 left-3 z-30 w-[265px] max-w-[calc(100%-24px)] rounded-2xl border-[3px] border-zinc-900 bg-white p-2.5 shadow-[0_6px_0_#18181b] sm:w-[290px]"
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <span
            className={`inline-flex items-center gap-1 rounded-full border-2 border-zinc-900 px-2 py-0.5 text-[10px] font-black uppercase tracking-wider ${
              map.isRealWorld ? 'bg-[#2EC4B6] text-zinc-950' : 'bg-[#FFBE0B] text-zinc-950'
            }`}
          >
            {map.isRealWorld ? '📍 Lugar Real' : '✨ Original BeamNG'}
          </span>
          <h3 className="mt-1 truncate font-comic-display text-sm font-black text-zinc-900">
            {map.displayName}
          </h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar detalle del pin"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-zinc-900 bg-zinc-100 text-zinc-800 transition hover:bg-zinc-200"
        >
          <X className="h-3.5 w-3.5" strokeWidth={2.75} />
        </button>
      </div>

      {/* 50/50 split real vs game or original game thumbnail */}
      <div className="relative mb-2 aspect-[16/9] w-full overflow-hidden rounded-xl border-2 border-zinc-900 bg-zinc-100">
        {showSplit ? (
          <div className="relative grid h-full w-full grid-cols-2">
            <div className="relative h-full w-full overflow-hidden">
              <img
                src={map.realImageUrl}
                alt={map.realLocationName ?? map.displayName}
                referrerPolicy="no-referrer"
                onError={() => setRealFailed(true)}
                className="h-full w-full object-cover"
              />
              <span className="absolute top-1.5 left-1.5 rounded-full bg-zinc-950/75 px-1.5 py-0.5 text-[9px] font-extrabold uppercase text-white">
                Real
              </span>
            </div>
            <div className="relative h-full w-full overflow-hidden">
              <img
                src={map.gameImageUrl}
                alt={map.displayName}
                className="h-full w-full object-cover"
              />
              <span className="absolute top-1.5 right-1.5 rounded-full bg-teal-400/95 px-1.5 py-0.5 text-[9px] font-extrabold uppercase text-zinc-950">
                Juego
              </span>
            </div>
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-y-0 left-1/2 w-[2px] -translate-x-1/2 bg-white shadow"
            />
          </div>
        ) : (
          <img
            src={map.gameImageUrl}
            alt={map.displayName}
            className="h-full w-full object-cover"
          />
        )}
      </div>

      <div className="mb-2.5 space-y-0.5 text-[11px]">
        {map.isRealWorld && map.realLocationName && (
          <p className="flex items-center gap-1 truncate font-semibold text-teal-700">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="truncate">{map.realLocationName}</span>
          </p>
        )}
        <p className="truncate font-mono text-[10px] text-zinc-500">
          {map.zipName} · ({coord.x.toFixed(1)}%, {coord.y.toFixed(1)}%)
        </p>
      </div>

      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={onStartReposition}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border-2 border-zinc-900 bg-[#FFBE0B] px-2.5 py-1.5 text-xs font-extrabold text-zinc-950 shadow-[0_2px_0_#18181b] transition hover:-translate-y-0.5 active:translate-y-0"
        >
          <Crosshair className="h-3.5 w-3.5" />
          Mover con clic
        </button>
        <button
          type="button"
          onClick={onRemove}
          aria-label="Quitar pin del mapa"
          className="flex items-center justify-center gap-1 rounded-xl border-2 border-zinc-900 bg-rose-100 px-2.5 py-1.5 text-xs font-extrabold text-rose-700 shadow-[0_2px_0_#18181b] transition hover:bg-rose-200"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Quitar
        </button>
      </div>
    </div>
  );
}

interface CartoonWorldMapSectionProps {
  allMaps: MapModItem[];
}

export function CartoonWorldMapSection({ allMaps }: CartoonWorldMapSectionProps) {
  const validMapIds = useMemo(() => new Set(allMaps.map((m) => m.id)), [allMaps]);
  const mapById = useMemo(
    () => new Map(allMaps.map((m) => [m.id, m])),
    [allMaps]
  );

  const [isOpen, setIsOpen] = useState(false);
  const [placedPins, setPlacedPins] = useState<PinMap>(() =>
    loadInitialPins(new Set(allMaps.map((m) => m.id)))
  );
  const [cloudStatus, setCloudStatus] = useState<'connecting' | 'synced' | 'saving' | 'offline'>(
    'connecting'
  );
  const [placingMapId, setPlacingMapId] = useState<string | null>(null);
  const [selectedPinId, setSelectedPinId] = useState<string | null>(null);
  const [lastDroppedId, setLastDroppedId] = useState<string | null>(null);

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<PinCoord>({ x: 0, y: 0 });
  const [isDragOverCanvas, setIsDragOverCanvas] = useState(false);

  const [drawerFilter, setDrawerFilter] = useState<DrawerFilter>('all');
  const [drawerSearch, setDrawerSearch] = useState('');

  const viewportRef = useRef<HTMLDivElement>(null);
  const worldLayerRef = useRef<HTMLDivElement>(null);
  const placedPinsRef = useRef<PinMap>(placedPins);

  const dragPinRef = useRef<{
    mapId: string;
    startX: number;
    startY: number;
    moved: boolean;
    latestCoord: PinCoord | null;
  } | null>(null);

  const panGestureRef = useRef<{
    startClientX: number;
    startClientY: number;
    startPanX: number;
    startPanY: number;
    moved: boolean;
  } | null>(null);

  // Mirror placed pins to localStorage as instant offline cache
  useEffect(() => {
    placedPinsRef.current = placedPins;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(placedPins));
    } catch {
      // Ignore storage quota errors gracefully
    }
  }, [placedPins]);

  // Real-time Cloud Firestore subscription so pins stay synced across PC & mobile
  useEffect(() => {
    const unsubscribe = subscribeToSharedWorldPins(validMapIds, {
      onRemotePins: (remotePins) => {
        // Avoid overwriting an active pointer drag mid-gesture
        if (!dragPinRef.current) {
          placedPinsRef.current = remotePins;
          setPlacedPins(remotePins);
        }
        setCloudStatus('synced');
      },
      onMissingRemote: () => placedPinsRef.current,
      onError: () => {
        setCloudStatus('offline');
      },
    });
    return () => unsubscribe();
  }, [validMapIds]);

  const persistPinsToCloud = useCallback((nextPins: PinMap) => {
    setCloudStatus('saving');
    void saveSharedWorldPins(nextPins)
      .then(() => {
        setCloudStatus('synced');
      })
      .catch(() => {
        setCloudStatus('offline');
      });
  }, []);

  const commitPins = useCallback(
    (nextPins: PinMap) => {
      placedPinsRef.current = nextPins;
      setPlacedPins(nextPins);
      persistPinsToCloud(nextPins);
    },
    [persistPinsToCloud]
  );

  const placedCount = useMemo(
    () => Object.keys(placedPins).filter((id) => validMapIds.has(id)).length,
    [placedPins, validMapIds]
  );

  const placingMap = placingMapId ? (mapById.get(placingMapId) ?? null) : null;
  const selectedMap = selectedPinId ? (mapById.get(selectedPinId) ?? null) : null;
  const selectedCoord = selectedPinId ? placedPins[selectedPinId] : undefined;

  const clientPointToWorldPercent = useCallback(
    (clientX: number, clientY: number): PinCoord | null => {
      const layer = worldLayerRef.current;
      if (!layer) return null;
      const rect = layer.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return null;
      return {
        x: Number(clamp(((clientX - rect.left) / rect.width) * 100, 1.2, 98.8).toFixed(2)),
        y: Number(clamp(((clientY - rect.top) / rect.height) * 100, 1.5, 98.5).toFixed(2)),
      };
    },
    []
  );

  const placePinAt = useCallback(
    (mapId: string, coord: PinCoord) => {
      const next = { ...placedPinsRef.current, [mapId]: coord };
      commitPins(next);
      setLastDroppedId(mapId);
      setSelectedPinId(mapId);
      setPlacingMapId(null);
    },
    [commitPins]
  );

  const applyZoom = useCallback(
    (nextZoom: number, focusX?: number, focusY?: number) => {
      const clampedZoom = Number(clamp(nextZoom, 1, 4.6).toFixed(2));
      if (focusX !== undefined && focusY !== undefined) {
        setZoom(clampedZoom);
        setPan(computePanForFocus(clampedZoom, focusX, focusY));
        return;
      }
      const centerX = zoom > 0 ? (50 - pan.x) / zoom : 50;
      const centerY = zoom > 0 ? (50 - pan.y) / zoom : 50;
      setZoom(clampedZoom);
      setPan(computePanForFocus(clampedZoom, centerX, centerY));
    },
    [pan.x, pan.y, zoom]
  );

  const focusPinOnMap = useCallback(
    (mapId: string) => {
      const coord = placedPins[mapId];
      if (!coord) return;
      const nextZoom = Math.max(zoom, 2.6);
      setZoom(nextZoom);
      setPan(computePanForFocus(nextZoom, coord.x, coord.y));
      setSelectedPinId(mapId);
    },
    [placedPins, zoom]
  );

  const handleAutoPlaceRealMaps = useCallback(() => {
    const next = { ...placedPinsRef.current };
    for (const [id, pin] of Object.entries(DEFAULT_REAL_MAP_PINS)) {
      if (validMapIds.has(id)) {
        next[id] = { x: pin.x, y: pin.y };
      }
    }
    commitPins(next);
    setPlacingMapId(null);
  }, [commitPins, validMapIds]);

  const handleScatterUnplacedOriginals = useCallback(() => {
    const next = { ...placedPinsRef.current };
    // Distribute unplaced original/fictional maps cleanly across landmasses & islands
    const creativeZones: Array<[number, number, number, number]> = [
      [10, 26, 26, 40],  // North America
      [24, 34, 54, 76],  // South America
      [45, 56, 20, 31],  // Europe
      [47, 59, 44, 66],  // Africa
      [63, 83, 24, 42],  // Asia
      [82, 92, 68, 79],  // Oceania
    ];
    let slotIdx = 0;
    for (const map of allMaps) {
      if (next[map.id] || map.isRealWorld) continue;
      const [xMin, xMax, yMin, yMax] = creativeZones[slotIdx % creativeZones.length];
      // Deterministic pseudo-random spread from map id hash so positions look playful & organic
      let hash = 2166136261;
      for (let i = 0; i < map.id.length; i++) {
        hash ^= map.id.charCodeAt(i);
        hash = Math.imul(hash, 16777619);
      }
      const rx = ((hash >>> 0) % 1000) / 1000;
      const ry = (((hash >>> 10) ^ slotIdx * 97) % 1000) / 1000;
      next[map.id] = {
        x: Number((xMin + rx * (xMax - xMin)).toFixed(2)),
        y: Number((yMin + ry * (yMax - yMin)).toFixed(2)),
      };
      slotIdx++;
    }
    commitPins(next);
    setPlacingMapId(null);
  }, [allMaps, commitPins]);

  const handleClearAllPins = useCallback(() => {
    commitPins({});
    setSelectedPinId(null);
    setPlacingMapId(null);
  }, [commitPins]);

  // Viewport pointer handlers: pan map or click-to-place active map
  const handleViewportPointerDown = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    panGestureRef.current = {
      startClientX: e.clientX,
      startClientY: e.clientY,
      startPanX: pan.x,
      startPanY: pan.y,
      moved: false,
    };
  };

  const handleViewportPointerMove = (e: ReactPointerEvent<HTMLDivElement>) => {
    const activeDrag = dragPinRef.current;
    if (activeDrag) {
      const dist = Math.hypot(e.clientX - activeDrag.startX, e.clientY - activeDrag.startY);
      if (dist > 3) {
        activeDrag.moved = true;
      }
      const nextCoord = clientPointToWorldPercent(e.clientX, e.clientY);
      if (nextCoord && activeDrag.moved) {
        activeDrag.latestCoord = nextCoord;
        setPlacedPins((prev) => ({
          ...prev,
          [activeDrag.mapId]: nextCoord,
        }));
      }
      return;
    }

    const panGesture = panGestureRef.current;
    const viewport = viewportRef.current;
    if (!panGesture || !viewport || zoom <= 1) return;

    const dxPx = e.clientX - panGesture.startClientX;
    const dyPx = e.clientY - panGesture.startClientY;
    if (Math.hypot(dxPx, dyPx) > 4) {
      panGesture.moved = true;
    }
    if (!panGesture.moved) return;

    const rect = viewport.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;

    const dxPct = (dxPx / rect.width) * 100;
    const dyPct = (dyPx / rect.height) * 100;
    setPan(
      clampPan(
        {
          x: panGesture.startPanX + dxPct,
          y: panGesture.startPanY + dyPct,
        },
        zoom
      )
    );
  };

  const handleViewportPointerUp = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (dragPinRef.current) {
      const { mapId, moved, latestCoord } = dragPinRef.current;
      dragPinRef.current = null;
      if (moved && latestCoord) {
        commitPins({ ...placedPinsRef.current, [mapId]: latestCoord });
      } else if (!moved) {
        setSelectedPinId((prev) => (prev === mapId ? null : mapId));
      }
      return;
    }

    const panGesture = panGestureRef.current;
    panGestureRef.current = null;
    if (panGesture?.moved) return;

    if (placingMapId) {
      const coord = clientPointToWorldPercent(e.clientX, e.clientY);
      if (coord) {
        placePinAt(placingMapId, coord);
      }
      return;
    }

    // Clicking empty ocean/continent closes the pin bubble
    setSelectedPinId(null);
  };

  const handlePinPointerDown = (
    e: ReactPointerEvent<HTMLButtonElement>,
    mapId: string
  ) => {
    if (e.button !== 0 || placingMapId) return;
    e.stopPropagation();
    viewportRef.current?.setPointerCapture(e.pointerId);
    dragPinRef.current = {
      mapId,
      startX: e.clientX,
      startY: e.clientY,
      moved: false,
      latestCoord: null,
    };
  };

  // HTML5 drag-and-drop from the map drawer directly onto the world canvas
  const handleCanvasDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (!isDragOverCanvas) setIsDragOverCanvas(true);
  };

  const handleCanvasDragLeave = () => {
    setIsDragOverCanvas(false);
  };

  const handleCanvasDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOverCanvas(false);
    const mapId = e.dataTransfer.getData('text/beamng-map-id');
    if (!mapId || !validMapIds.has(mapId)) return;
    const coord = clientPointToWorldPercent(e.clientX, e.clientY);
    if (coord) {
      placePinAt(mapId, coord);
    }
  };

  const drawerMaps = useMemo(() => {
    const q = drawerSearch.trim().toLowerCase();
    return allMaps.filter((map) => {
      const isPlaced = Boolean(placedPins[map.id]);
      if (drawerFilter === 'placed' && !isPlaced) return false;
      if (drawerFilter === 'unplaced' && isPlaced) return false;
      if (drawerFilter === 'real' && !map.isRealWorld) return false;
      if (drawerFilter === 'fictional' && map.isRealWorld) return false;

      if (!q) return true;
      return (
        map.displayName.toLowerCase().includes(q) ||
        (map.realLocationName?.toLowerCase().includes(q) ?? false) ||
        map.zipName.toLowerCase().includes(q)
      );
    });
  }, [allMaps, drawerFilter, drawerSearch, placedPins]);

  const unplacedCount = allMaps.length - placedCount;
  const realCount = useMemo(
    () => allMaps.filter((m) => m.isRealWorld).length,
    [allMaps]
  );
  const fictionalCount = allMaps.length - realCount;

  // Inverse pin scaling keeps pins crisp instead of becoming huge at 4x zoom
  const pinScale = 1 / Math.pow(zoom, 0.72);

  return (
    <section
      aria-label="Mapa mundial cartoon interactivo de BeamNG"
      className="mb-7"
    >
      {/* Collapsible Cartoon Banner */}
      <div
        className={`rounded-3xl border-[3px] border-zinc-900 bg-gradient-to-r from-[#FEF9C3] via-[#FFFBEB] to-[#E0F2FE] px-4 py-3 shadow-[0_5px_0_#18181b] transition-all sm:px-6 ${
          isOpen ? 'rounded-b-none border-b-2' : ''
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border-[2.5px] border-zinc-900 bg-[#FFBE0B] text-zinc-950 shadow-[0_3px_0_#18181b]">
              <Globe className="h-6 w-6" strokeWidth={2.5} />
            </span>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-comic-display text-lg font-black tracking-tight text-zinc-900 sm:text-xl">
                  Mapa Mundial Cartoon
                </h2>
                <span className="inline-flex items-center gap-1 rounded-full border-2 border-zinc-900 bg-[#2EC4B6] px-2.5 py-0.5 text-xs font-black text-zinc-950 shadow-[0_2px_0_#18181b]">
                  {placedCount} / {allMaps.length} ubicados
                </span>
                <span
                  title="Los pines se guardan y sincronizan en tiempo real con Firebase Cloud Firestore"
                  className={`inline-flex items-center gap-1 rounded-full border-2 border-zinc-900 px-2.5 py-0.5 text-[11px] font-black shadow-[0_2px_0_#18181b] ${
                    cloudStatus === 'synced'
                      ? 'bg-emerald-200 text-zinc-950'
                      : cloudStatus === 'saving' || cloudStatus === 'connecting'
                        ? 'bg-amber-200 text-zinc-950'
                        : 'bg-zinc-200 text-zinc-700'
                  }`}
                >
                  {cloudStatus === 'offline' ? (
                    <CloudOff className="h-3 w-3" />
                  ) : (
                    <Cloud className="h-3 w-3" />
                  )}
                  {cloudStatus === 'synced'
                    ? 'Nube sincronizada'
                    : cloudStatus === 'saving'
                      ? 'Guardando...'
                      : cloudStatus === 'connecting'
                        ? 'Conectando...'
                        : 'Solo local'}
                </span>
              </div>
              <p className="text-xs font-medium text-zinc-600 sm:text-sm">
                ¡Ubica o arrastra tus mapas reales y ficticios a tu gusto por todo el mundo dibujado!
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsOpen((v) => !v)}
            aria-expanded={isOpen}
            className={`cartoon-pill inline-flex items-center gap-2 rounded-full border-[2.5px] border-zinc-900 px-4 py-2 font-comic-display text-sm font-black shadow-[0_3px_0_#18181b] transition hover:-translate-y-0.5 active:translate-y-0 ${
              isOpen
                ? 'bg-[#FB7185] text-white'
                : 'bg-[#FFBE0B] text-zinc-950 hover:bg-[#FDE047]'
            }`}
          >
            {isOpen ? (
              <>
                Cerrar Mapa Mundial
                <ChevronUp className="h-4 w-4" strokeWidth={2.75} />
              </>
            ) : (
              <>
                🗺️ Abrir Mapa Mundial Cartoon
                <ChevronDown className="h-4 w-4" strokeWidth={2.75} />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Expandable Interactive World Map Workspace */}
      {isOpen && (
        <div className="cartoon-map-frame rounded-b-3xl border-t-0 bg-[#FFFDF7] p-3 sm:p-5">
          {/* Active Placement Banner OR Quick Controls Bar */}
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2.5">
            {placingMap ? (
              <div className="flex flex-wrap items-center gap-2 rounded-2xl border-[2.5px] border-zinc-900 bg-[#FFBE0B] px-3.5 py-2 shadow-[0_3px_0_#18181b]">
                <Crosshair className="h-4 w-4 animate-pulse text-zinc-950" strokeWidth={2.75} />
                <span className="text-xs font-black text-zinc-950 sm:text-sm">
                  Haz clic en cualquier punto del mapa para ubicar:{' '}
                  <span className="underline decoration-2">{placingMap.displayName}</span>
                </span>
                <button
                  type="button"
                  onClick={() => setPlacingMapId(null)}
                  className="ml-1 rounded-full border-2 border-zinc-900 bg-white px-2.5 py-0.5 text-xs font-extrabold text-zinc-900 hover:bg-zinc-100"
                >
                  Cancelar
                </button>
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-1.5">
                {REGION_PRESETS.map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => applyZoom(preset.zoom, preset.focusX, preset.focusY)}
                    className="rounded-full border-2 border-zinc-900 bg-white px-2.5 py-1 text-xs font-extrabold text-zinc-800 shadow-[0_2px_0_#18181b] transition hover:-translate-y-0.5 hover:bg-[#FEF08A]"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                onClick={handleAutoPlaceRealMaps}
                title="Coloca los 65 mapas basados en lugares reales en sus zonas del mundo"
                className="inline-flex items-center gap-1.5 rounded-full border-2 border-zinc-900 bg-[#2EC4B6] px-3 py-1 text-xs font-black text-zinc-950 shadow-[0_2px_0_#18181b] transition hover:-translate-y-0.5 hover:bg-[#5EEAD4]"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Auto-ubicar reales ({realCount})
              </button>
              <button
                type="button"
                onClick={handleScatterUnplacedOriginals}
                title="Reparte creativamente los mapas originales que faltan por ubicar"
                className="inline-flex items-center gap-1.5 rounded-full border-2 border-zinc-900 bg-[#A78BFA] px-3 py-1 text-xs font-black text-zinc-950 shadow-[0_2px_0_#18181b] transition hover:-translate-y-0.5 hover:bg-[#C4B5FD]"
              >
                <Dice5 className="h-3.5 w-3.5" />
                Esparcir originales
              </button>
              <button
                type="button"
                onClick={handleClearAllPins}
                title="Quita todos los pines del mapa para empezar desde cero"
                className="inline-flex items-center gap-1 rounded-full border-2 border-zinc-900 bg-rose-100 px-2.5 py-1 text-xs font-black text-rose-800 shadow-[0_2px_0_#18181b] transition hover:bg-rose-200"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Limpiar
              </button>

              {/* Zoom Toolbar */}
              <div className="ml-1 inline-flex items-center overflow-hidden rounded-full border-2 border-zinc-900 bg-white shadow-[0_2px_0_#18181b]">
                <button
                  type="button"
                  onClick={() => applyZoom(zoom - 0.6)}
                  disabled={zoom <= 1}
                  aria-label="Alejar mapa"
                  className="px-2 py-1 text-zinc-800 transition hover:bg-zinc-100 disabled:opacity-40"
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </button>
                <span className="border-x-2 border-zinc-900 px-2 py-0.5 text-[11px] font-black text-zinc-900">
                  {Math.round(zoom * 100)}%
                </span>
                <button
                  type="button"
                  onClick={() => applyZoom(zoom + 0.7)}
                  disabled={zoom >= 4.6}
                  aria-label="Acercar mapa"
                  className="px-2 py-1 text-zinc-800 transition hover:bg-zinc-100 disabled:opacity-40"
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </button>
                {zoom > 1 && (
                  <button
                    type="button"
                    onClick={() => applyZoom(1, 50, 50)}
                    aria-label="Restablecer vista mundial"
                    className="border-l-2 border-zinc-900 bg-[#FEF08A] px-2 py-1 text-zinc-900 transition hover:bg-[#FDE047]"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Main Grid: Left Illustrated World Map + Right Searchable Map Drawer */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_330px]">
            {/* World Map Ocean Viewport */}
            <div
              ref={viewportRef}
              onPointerDown={handleViewportPointerDown}
              onPointerMove={handleViewportPointerMove}
              onPointerUp={handleViewportPointerUp}
              onDragOver={handleCanvasDragOver}
              onDragLeave={handleCanvasDragLeave}
              onDrop={handleCanvasDrop}
              className={`relative aspect-[494.7/265.7] w-full touch-none overflow-hidden rounded-2xl border-[3px] border-zinc-900 bg-gradient-to-b from-[#60D7FA] via-[#38BDF8] to-[#0284C7] shadow-[inset_0_0_28px_rgba(255,255,255,0.22)] ${
                placingMapId
                  ? 'cursor-crosshair'
                  : zoom > 1
                    ? 'cursor-grab active:cursor-grabbing'
                    : 'cursor-default'
              } ${isDragOverCanvas ? 'ring-4 ring-[#FFBE0B]' : ''}`}
            >
              {/* Subtle comic halftone ocean dots */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 opacity-20"
                style={{
                  backgroundImage:
                    'radial-gradient(circle, rgba(255,255,255,0.9) 1.25px, transparent 1.25px)',
                  backgroundSize: '18px 18px',
                }}
              />

              {/* Transformable World Layer (SVG + Interactive Pin Markers) */}
              <div
                ref={worldLayerRef}
                style={{
                  transformOrigin: '0 0',
                  transform: `translate(${pan.x}%, ${pan.y}%) scale(${zoom})`,
                }}
                className="relative h-full w-full transition-transform duration-100 ease-out will-change-transform"
              >
                <svg
                  viewBox={`0 0 ${WORLD_MAP_VIEWBOX.width} ${WORLD_MAP_VIEWBOX.height}`}
                  className="block h-full w-full"
                >
                  {/* 1. Animated Waves, Clouds, Boat & Compass */}
                  <CartoonWorldDecorations />

                  {/* 2. Hard 3D Comic Extrusion Shadow underneath Continents */}
                  <path
                    d={WORLD_ALL_LAND_PATH}
                    transform="translate(0, 3.6)"
                    fill="#18181b"
                    fillOpacity="0.92"
                    stroke="#18181b"
                    strokeWidth="2.2"
                    strokeLinejoin="round"
                  />

                  {/* 3. Bold Outer Comic Ink Outline */}
                  <path
                    d={WORLD_ALL_LAND_PATH}
                    fill="#18181b"
                    stroke="#18181b"
                    strokeWidth="2.8"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />

                  {/* 4. Colorful Cartoon Continent Regions */}
                  {CARTOON_CONTINENTS.map((continent) => (
                    <g key={continent.id}>
                      {continent.paths.map((d, pathIdx) => (
                        <path
                          key={`${continent.id}-${pathIdx}`}
                          d={d}
                          fill={continent.fill}
                          stroke="#18181b"
                          strokeWidth="0.48"
                          strokeOpacity="0.34"
                          strokeLinejoin="round"
                        />
                      ))}
                    </g>
                  ))}

                  {/* 5. North American Great Lakes cut-out */}
                  {WORLD_GREAT_LAKES_PATH && (
                    <path
                      d={WORLD_GREAT_LAKES_PATH}
                      fill="#38BDF8"
                      stroke="#18181b"
                      strokeWidth="0.6"
                      strokeLinejoin="round"
                    />
                  )}

                  {/* 6. Bold Cartoon Continent Labels */}
                  {CARTOON_CONTINENTS.map((continent) => (
                    <text
                      key={`label-${continent.id}`}
                      x={continent.labelX}
                      y={continent.labelY}
                      textAnchor="middle"
                      fontSize={continent.id === 'japan' ? '4.8' : '5.6'}
                      fontWeight="900"
                      letterSpacing="0.5"
                      fill="#FFFFFF"
                      stroke="#18181b"
                      strokeWidth="1.9"
                      paintOrder="stroke"
                      strokeLinejoin="round"
                      className="pointer-events-none select-none font-cartoon"
                    >
                      {continent.label}
                    </text>
                  ))}
                </svg>

                {/* Interactive Cartoon Map Pins */}
                <div className="pointer-events-none absolute inset-0">
                  {allMaps.map((map) => {
                    const coord = placedPins[map.id];
                    if (!coord) return null;
                    const isSelected = selectedPinId === map.id;
                    const isRecentDrop = lastDroppedId === map.id;

                    return (
                      <div
                        key={map.id}
                        style={{
                          left: `${coord.x}%`,
                          top: `${coord.y}%`,
                          transform: `translate(-50%, -100%) scale(${pinScale})`,
                          transformOrigin: '50% 100%',
                        }}
                        className={`pointer-events-auto absolute ${
                          isSelected ? 'z-30' : 'z-10 hover:z-20'
                        }`}
                      >
                        <button
                          type="button"
                          onPointerDown={(e) => handlePinPointerDown(e, map.id)}
                          aria-label={`Pin de ${map.displayName}`}
                          title={`${map.displayName}${map.realLocationName ? ` — ${map.realLocationName}` : ''} (arrastra para mover)`}
                          className={`group relative flex flex-col items-center focus:outline-none ${
                            isRecentDrop ? 'cartoon-pin-drop' : ''
                          }`}
                        >
                          {/* Floating label pill on hover or selection */}
                          <span
                            className={`pointer-events-none mb-0.5 max-w-[140px] truncate rounded-full border-[1.5px] border-zinc-900 bg-white px-2 py-0.5 text-[10px] font-black text-zinc-950 shadow-[0_2px_0_#18181b] transition-opacity ${
                              isSelected
                                ? 'opacity-100'
                                : 'opacity-0 group-hover:opacity-100'
                            }`}
                          >
                            {map.displayName}
                          </span>

                          {/* Circular Comic Map Thumbnail Bubble */}
                          <div
                            className={`relative h-7 w-7 overflow-hidden rounded-full border-[2.5px] border-zinc-900 shadow-[0_2.5px_0_#18181b] transition-transform group-hover:scale-115 sm:h-8 sm:w-8 ${
                              isSelected
                                ? 'scale-125 ring-2 ring-[#FB7185] ring-offset-1'
                                : map.isRealWorld
                                  ? 'bg-[#2EC4B6]'
                                  : 'bg-[#FFBE0B]'
                            }`}
                          >
                            <img
                              src={map.realImageUrl ?? map.gameImageUrl}
                              alt=""
                              referrerPolicy="no-referrer"
                              draggable={false}
                              onError={(e) => {
                                const img = e.currentTarget;
                                if (!img.dataset.fallback) {
                                  img.dataset.fallback = '1';
                                  img.src = map.gameImageUrl;
                                }
                              }}
                              className="h-full w-full object-cover"
                            />
                          </div>

                          {/* Comic Teardrop Tip */}
                          <span
                            aria-hidden="true"
                            className={`-mt-1 h-2.5 w-2.5 rotate-45 border-r-2 border-b-2 border-zinc-900 ${
                              isSelected
                                ? 'bg-[#FB7185]'
                                : map.isRealWorld
                                  ? 'bg-[#2EC4B6]'
                                  : 'bg-[#FFBE0B]'
                            }`}
                          />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Dropzone hint overlay during drag */}
              {isDragOverCanvas && (
                <div className="pointer-events-none absolute inset-2 z-30 flex items-center justify-center rounded-xl border-4 border-dashed border-[#18181b] bg-[#FFBE0B]/35 backdrop-blur-[1px]">
                  <span className="rounded-full border-2 border-zinc-900 bg-[#FFBE0B] px-4 py-1.5 font-comic-display text-sm font-black text-zinc-950 shadow-[0_3px_0_#18181b]">
                    📍 ¡Suelta aquí para fijar el mapa!
                  </span>
                </div>
              )}

              {/* Subtle helper badge at top-right */}
              <div className="pointer-events-none absolute top-2.5 right-2.5 z-20 hidden rounded-full border-2 border-zinc-900 bg-white/90 px-2.5 py-0.5 text-[10px] font-extrabold text-zinc-800 shadow-[0_2px_0_#18181b] sm:inline-flex sm:items-center sm:gap-1">
                <Move className="h-3 w-3 text-[#0284C7]" />
                Arrastra cualquier pin para moverlo
              </div>

              {/* Speech-Bubble Pin Inspector Overlay */}
              {selectedMap && selectedCoord && (
                <PinInspectorBubble
                  key={selectedMap.id}
                  map={selectedMap}
                  coord={selectedCoord}
                  onStartReposition={() => {
                    setPlacingMapId(selectedMap.id);
                    setSelectedPinId(null);
                  }}
                  onRemove={() => {
                    const next = { ...placedPinsRef.current };
                    delete next[selectedMap.id];
                    commitPins(next);
                    setSelectedPinId(null);
                  }}
                  onClose={() => setSelectedPinId(null)}
                />
              )}
            </div>

            {/* Right Sidebar: Searchable 127-Map Selector Drawer */}
            <div className="relative h-[380px] lg:h-auto lg:min-h-0">
              <aside
                aria-label="Cajón de mapas para colocar en el mundo"
                className="flex h-full flex-col overflow-hidden rounded-2xl border-[3px] border-zinc-900 bg-white shadow-[0_4px_0_#18181b] lg:absolute lg:inset-0"
              >
              <div className="border-b-2 border-zinc-900 bg-[#FEF9C3] p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="inline-flex items-center gap-1.5 font-comic-display text-sm font-black text-zinc-900">
                    <Compass className="h-4 w-4 text-[#F97316]" />
                    Cajón de Mapas
                  </span>
                  <span className="rounded-full border-2 border-zinc-900 bg-white px-2 py-0.5 text-[10px] font-black text-zinc-800">
                    {drawerMaps.length} visibles
                  </span>
                </div>

                {/* Drawer Search Box */}
                <div className="relative mt-2">
                  <Search className="pointer-events-none absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
                  <input
                    type="search"
                    value={drawerSearch}
                    onChange={(e) => setDrawerSearch(e.target.value)}
                    placeholder="Buscar mapa o país..."
                    className="w-full rounded-xl border-2 border-zinc-900 bg-white py-1.5 pr-3 pl-8 text-xs font-semibold text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#FFBE0B]"
                  />
                </div>

                {/* Drawer Filter Pills */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {(
                    [
                      ['all', `Todos (${allMaps.length})`],
                      ['unplaced', `Sin ubicar (${unplacedCount})`],
                      ['placed', `Ubicados (${placedCount})`],
                      ['real', `Reales (${realCount})`],
                      ['fictional', `Originales (${fictionalCount})`],
                    ] as Array<[DrawerFilter, string]>
                  ).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setDrawerFilter(key)}
                      className={`rounded-full border-[1.5px] border-zinc-900 px-2 py-0.5 text-[10px] font-extrabold transition ${
                        drawerFilter === key
                          ? 'bg-zinc-900 text-white'
                          : 'bg-white text-zinc-800 hover:bg-zinc-100'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Scrollable List of Draggable/Clickable Map Cards */}
              <div className="flex-1 space-y-2 overflow-y-auto p-2.5">
                {drawerMaps.length === 0 ? (
                  <p className="py-8 text-center text-xs font-semibold text-zinc-500">
                    No hay mapas en esta categoría.
                  </p>
                ) : (
                  drawerMaps.map((map) => {
                    const isPlaced = Boolean(placedPins[map.id]);
                    const isPlacing = placingMapId === map.id;

                    return (
                      <div
                        key={map.id}
                        draggable
                        onDragStart={(e) => {
                          e.dataTransfer.setData('text/beamng-map-id', map.id);
                          e.dataTransfer.effectAllowed = 'move';
                        }}
                        className={`flex items-center gap-2 rounded-xl border-2 p-1.5 transition ${
                          isPlacing
                            ? 'border-zinc-900 bg-[#FFBE0B]/40 shadow-[0_2px_0_#18181b]'
                            : 'border-zinc-200 bg-zinc-50 hover:border-zinc-900 hover:bg-white'
                        }`}
                      >
                        <img
                          src={map.realImageUrl ?? map.gameImageUrl}
                          alt=""
                          loading="lazy"
                          referrerPolicy="no-referrer"
                          onError={(e) => {
                            const img = e.currentTarget;
                            if (!img.dataset.fallback) {
                              img.dataset.fallback = '1';
                              img.src = map.gameImageUrl;
                            }
                          }}
                          className="h-10 w-12 shrink-0 rounded-lg border border-zinc-900/20 object-cover"
                        />

                        <div className="min-w-0 flex-1">
                          <p className="truncate text-xs font-extrabold text-zinc-900">
                            {map.displayName}
                          </p>
                          <p className="truncate text-[10px] font-medium text-zinc-500">
                            {map.isRealWorld && map.realLocationName
                              ? `📍 ${map.realLocationName}`
                              : '✨ Original BeamNG'}
                          </p>
                        </div>

                        <div className="flex shrink-0 items-center gap-1">
                          {isPlaced ? (
                            <>
                              <button
                                type="button"
                                onClick={() => focusPinOnMap(map.id)}
                                title="Ver y centrar en el mapa"
                                className="rounded-lg border-[1.5px] border-zinc-900 bg-[#2EC4B6] px-2 py-1 text-[10px] font-black text-zinc-950 hover:bg-[#5EEAD4]"
                              >
                                Ver
                              </button>
                              <button
                                type="button"
                                onClick={() => setPlacingMapId(map.id)}
                                title="Elegir nueva ubicación con un clic"
                                className="rounded-lg border-[1.5px] border-zinc-900 bg-[#FFBE0B] px-1.5 py-1 text-[10px] font-black text-zinc-950 hover:bg-[#FDE047]"
                              >
                                <Crosshair className="h-3 w-3" />
                              </button>
                            </>
                          ) : (
                            <button
                              type="button"
                              onClick={() => setPlacingMapId(map.id)}
                              title="Haz clic aquí y luego toca cualquier lugar del mundo"
                              className={`rounded-lg border-[1.5px] border-zinc-900 px-2 py-1 text-[10px] font-black transition ${
                                isPlacing
                                  ? 'bg-zinc-900 text-white'
                                  : 'bg-[#FFBE0B] text-zinc-950 hover:bg-[#FDE047]'
                              }`}
                            >
                              {isPlacing ? 'Elige punto' : '+ Colocar'}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </aside>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
