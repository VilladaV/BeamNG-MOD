import { useState } from 'react';
import { CarFront } from 'lucide-react';
import type { CarModItem } from '@/types/mods';

interface CarPinCardProps {
  car: CarModItem;
  index: number;
}

export function CarPinCard({ car, index }: CarPinCardProps) {
  const [fallbackLevel, setFallbackLevel] = useState<'real' | 'game' | 'none'>('real');

  const isLcpCandidate = index < 2;
  const isBelowFold = index >= 12;

  const activeSrc =
    fallbackLevel === 'real'
      ? car.realImageUrl
      : fallbackLevel === 'game' && car.gamePreviewUrl
        ? car.gamePreviewUrl
        : null;

  const handleImageError = () => {
    if (fallbackLevel === 'real' && car.gamePreviewUrl) {
      setFallbackLevel('game');
    } else {
      setFallbackLevel('none');
    }
  };

  return (
    <article
      tabIndex={0}
      aria-label={`${car.displayName} (${car.zipName})`}
      className="group relative overflow-hidden rounded-2xl bg-zinc-200/80 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950"
    >
      <div
        className="relative w-full overflow-hidden"
        style={{ aspectRatio: `${car.aspectWidth} / ${car.aspectHeight}` }}
      >
        {activeSrc ? (
          <img
            src={activeSrc}
            alt={`${car.displayName} — foto real`}
            referrerPolicy="no-referrer"
            loading={isBelowFold ? 'lazy' : undefined}
            fetchPriority={isLcpCandidate ? 'high' : undefined}
            decoding={isLcpCandidate ? 'sync' : 'async'}
            onError={handleImageError}
            className="h-full w-full object-cover object-center transition-transform duration-500 ease-out group-hover:scale-[1.04]"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-zinc-100 p-4 text-center text-zinc-500">
            <CarFront className="h-8 w-8 text-zinc-400" aria-hidden="true" />
            <span className="text-xs font-semibold text-zinc-700">{car.displayName}</span>
          </div>
        )}

        {/* Subtle Pinterest-style hover/focus caption overlay */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-zinc-950/90 via-zinc-950/45 to-transparent px-3.5 pt-10 pb-3 opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus:opacity-100 group-focus-within:opacity-100">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-sm font-bold text-white drop-shadow-sm">
              {car.displayName}
            </p>
            {car.category === 'camion' && (
              <span className="shrink-0 rounded-full bg-amber-400/95 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-zinc-950">
                Camión
              </span>
            )}
          </div>
          <p className="mt-0.5 truncate font-mono text-[11px] text-zinc-300/90">
            {car.zipName}
          </p>
        </div>
      </div>
    </article>
  );
}
