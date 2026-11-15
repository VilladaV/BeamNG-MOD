import { useState } from 'react';
import { MapPin, Sparkles } from 'lucide-react';
import { getPinAspectClass } from '@/lib/pinAspect';
import type { MapModItem } from '@/types/mods';

interface MapPinCardProps {
  map: MapModItem;
  index: number;
  isActiveSection: boolean;
}

export function MapPinCard({ map, index, isActiveSection }: MapPinCardProps) {
  const [realImgFailed, setRealImgFailed] = useState(false);
  const [gameImgFailed, setGameImgFailed] = useState(false);

  const isBelowFold = index >= 12;
  const shouldLazyLoad = isBelowFold || !isActiveSection;
  const showSplitView = Boolean(map.isRealWorld && map.realImageUrl && !realImgFailed);

  return (
    <article
      tabIndex={0}
      aria-label={`${map.displayName} (${map.zipName})`}
      className={`group relative mb-4 break-inside-avoid overflow-hidden rounded-2xl bg-zinc-200/80 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950 ${
        isBelowFold ? 'card-deferred' : ''
      }`}
    >
      <div className={`relative w-full overflow-hidden ${getPinAspectClass(map.aspectRatio)}`}>
        {showSplitView ? (
          <div className="relative grid h-full w-full grid-cols-2 overflow-hidden">
            {/* Left half: real-world location photo */}
            <div className="relative h-full w-full overflow-hidden">
              <img
                src={map.realImageUrl}
                alt={`${map.realLocationName ?? map.displayName} — ubicación real`}
                referrerPolicy="no-referrer"
                loading={shouldLazyLoad ? 'lazy' : undefined}
                decoding="async"
                onError={() => setRealImgFailed(true)}
                className="h-full w-full object-cover object-center transition-transform duration-500 ease-out group-hover:scale-[1.05]"
              />
              <span className="pointer-events-none absolute top-2.5 left-2.5 rounded-full bg-zinc-950/75 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-white backdrop-blur-xs">
                Real
              </span>
            </div>

            {/* Right half: in-game BeamNG preview */}
            <div className="relative h-full w-full overflow-hidden">
              {!gameImgFailed ? (
                <img
                  src={map.gameImageUrl}
                  alt={`${map.displayName} — vista en BeamNG`}
                  loading={shouldLazyLoad ? 'lazy' : undefined}
                  decoding="async"
                  onError={() => setGameImgFailed(true)}
                  className="h-full w-full object-cover object-center transition-transform duration-500 ease-out group-hover:scale-[1.05]"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center bg-zinc-800 text-xs font-semibold text-zinc-300">
                  BeamNG
                </div>
              )}
              <span className="pointer-events-none absolute top-2.5 right-2.5 rounded-full bg-teal-500/90 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-zinc-950 shadow-xs">
                Juego
              </span>
            </div>

            {/* Crisp center seam divider */}
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-y-0 left-1/2 w-[2.5px] -translate-x-1/2 bg-white shadow-[0_0_8px_rgba(0,0,0,0.5)]"
            />
          </div>
        ) : !gameImgFailed ? (
          <div className="relative h-full w-full overflow-hidden">
            <img
              src={map.gameImageUrl}
              alt={`${map.displayName} — vista previa en BeamNG`}
              loading={shouldLazyLoad ? 'lazy' : undefined}
              decoding="async"
              onError={() => setGameImgFailed(true)}
              className="h-full w-full object-cover object-center transition-transform duration-500 ease-out group-hover:scale-[1.04]"
            />
            <span className="pointer-events-none absolute top-2.5 right-2.5 inline-flex items-center gap-1 rounded-full bg-zinc-950/70 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white backdrop-blur-xs">
              <Sparkles className="h-2.5 w-2.5 text-amber-300" aria-hidden="true" />
              Original
            </span>
          </div>
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-zinc-100 p-4 text-center text-zinc-500">
            <MapPin className="h-8 w-8 text-zinc-400" aria-hidden="true" />
            <span className="text-xs font-semibold text-zinc-700">{map.displayName}</span>
          </div>
        )}

        {/* Hover / focus caption */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-zinc-950/92 via-zinc-950/55 to-transparent px-3.5 pt-12 pb-3 opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus:opacity-100 group-focus-within:opacity-100">
          <p className="truncate text-sm font-bold text-white drop-shadow-sm">
            {map.displayName}
          </p>
          {map.isRealWorld && map.realLocationName && (
            <p className="mt-0.5 flex items-center gap-1 truncate text-[11px] font-medium text-teal-300">
              <MapPin className="h-3 w-3 shrink-0" aria-hidden="true" />
              <span className="truncate">{map.realLocationName}</span>
            </p>
          )}
          <p className="mt-0.5 truncate font-mono text-[11px] text-zinc-300/90">
            {map.zipName}
          </p>
        </div>
      </div>
    </article>
  );
}
