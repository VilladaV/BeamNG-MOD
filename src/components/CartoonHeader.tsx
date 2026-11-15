import { useRef, useState } from 'react';
import { CarFront, Map as MapIcon, Search, X } from 'lucide-react';

export type GallerySection = 'cars' | 'maps';

interface CartoonHeaderProps {
  activeTab: GallerySection;
  onTabChange: (tab: GallerySection) => void;
  totalCars: number;
  totalMaps: number;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

interface TitleGlyph {
  char: string;
  color: string;
  tilt: string;
  hoverTilt: string;
  delay: string;
}

const TITLE_GLYPHS: TitleGlyph[] = [
  { char: 'B', color: '#FF6B35', tilt: '-4deg', hoverTilt: '-8deg', delay: '0ms' },
  { char: 'e', color: '#FF9F1C', tilt: '3deg', hoverTilt: '7deg', delay: '120ms' },
  { char: 'a', color: '#FFBE0B', tilt: '-2deg', hoverTilt: '-6deg', delay: '240ms' },
  { char: 'm', color: '#FF6B35', tilt: '4deg', hoverTilt: '9deg', delay: '360ms' },
  { char: 'N', color: '#2EC4B6', tilt: '-3deg', hoverTilt: '-7deg', delay: '480ms' },
  { char: 'G', color: '#38BDF8', tilt: '3deg', hoverTilt: '8deg', delay: '600ms' },
  { char: '-', color: '#FFBE0B', tilt: '0deg', hoverTilt: '12deg', delay: '720ms' },
  { char: 'M', color: '#FB7185', tilt: '-4deg', hoverTilt: '-8deg', delay: '840ms' },
  { char: 'o', color: '#FF9F1C', tilt: '3deg', hoverTilt: '6deg', delay: '960ms' },
  { char: 'd', color: '#2EC4B6', tilt: '-3deg', hoverTilt: '-7deg', delay: '1080ms' },
  { char: 's', color: '#FFBE0B', tilt: '4deg', hoverTilt: '8deg', delay: '1200ms' },
];

export function CartoonHeader({
  activeTab,
  onTabChange,
  totalCars,
  totalMaps,
  searchQuery,
  onSearchChange,
}: CartoonHeaderProps) {
  const [searchOpen, setSearchOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const openSearch = () => {
    setSearchOpen(true);
    window.setTimeout(() => {
      inputRef.current?.focus();
    }, 30);
  };

  const clearOrCloseSearch = () => {
    if (searchQuery) {
      onSearchChange('');
      inputRef.current?.focus();
    } else {
      setSearchOpen(false);
    }
  };

  return (
    <header className="relative pt-8 pb-6 px-4 sm:px-6 overflow-x-clip">
      <div className="max-w-5xl mx-auto flex flex-col items-center">
        <div className="relative inline-flex items-center justify-center">
          {/* Comic sparkle accents */}
          <svg
            aria-hidden="true"
            viewBox="0 0 40 40"
            className="cartoon-sparkle hidden sm:block absolute -left-11 -top-3 w-8 h-8 text-[#FFBE0B] drop-shadow-[2px_2px_0_#18181b] pointer-events-none"
            style={{ ['--sparkle-delay' as string]: '0ms' }}
          >
            <path
              d="M20 2 L24.5 14.5 L38 20 L24.5 25.5 L20 38 L15.5 25.5 L2 20 L15.5 14.5 Z"
              fill="currentColor"
              stroke="#18181b"
              strokeWidth="2.5"
              strokeLinejoin="round"
            />
          </svg>

          <svg
            aria-hidden="true"
            viewBox="0 0 32 32"
            className="cartoon-sparkle hidden sm:block absolute -right-10 -bottom-1 w-7 h-7 text-[#2EC4B6] drop-shadow-[2px_2px_0_#18181b] pointer-events-none"
            style={{ ['--sparkle-delay' as string]: '650ms' }}
          >
            <path
              d="M16 1 L19.8 11.2 L30 15 L19.8 18.8 L16 29 L12.2 18.8 L2 15 L12.2 11.2 Z"
              fill="currentColor"
              stroke="#18181b"
              strokeWidth="2.5"
              strokeLinejoin="round"
            />
          </svg>

          <h1
            aria-label="BeamNG-Mods"
            className="font-cartoon text-[2.7rem] sm:text-6xl md:text-[4.4rem] tracking-tight select-none flex flex-wrap items-center justify-center leading-none py-2"
          >
            {TITLE_GLYPHS.map((glyph, index) => (
              <span
                key={`${glyph.char}-${index}`}
                aria-hidden="true"
                className="cartoon-letter cursor-default px-[0.015em]"
                style={{
                  color: glyph.color,
                  ['--base-tilt' as string]: glyph.tilt,
                  ['--hover-tilt' as string]: glyph.hoverTilt,
                  ['--letter-delay' as string]: glyph.delay,
                }}
              >
                {glyph.char}
              </span>
            ))}
          </h1>
        </div>

        {/* Minimalist section switcher + compact search */}
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2.5">
          <div
            role="tablist"
            aria-label="Secciones de galería"
            className="inline-flex items-center gap-2.5"
          >
            <button
              id="tab-cars"
              type="button"
              role="tab"
              aria-selected={activeTab === 'cars'}
              aria-controls="panel-cars"
              onClick={() => onTabChange('cars')}
              className={`cartoon-pill font-comic-display inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm sm:text-base font-bold cursor-pointer ${
                activeTab === 'cars'
                  ? 'bg-[#FFBE0B] text-zinc-950'
                  : 'bg-white text-zinc-800 hover:bg-amber-50'
              }`}
            >
              <CarFront className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Autos</span>
              <span className="rounded-full bg-zinc-950/10 px-2 py-0.5 text-xs font-extrabold tabular-nums">
                {totalCars}
              </span>
            </button>

            <button
              id="tab-maps"
              type="button"
              role="tab"
              aria-selected={activeTab === 'maps'}
              aria-controls="panel-maps"
              onClick={() => onTabChange('maps')}
              className={`cartoon-pill font-comic-display inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm sm:text-base font-bold cursor-pointer ${
                activeTab === 'maps'
                  ? 'bg-[#2EC4B6] text-zinc-950'
                  : 'bg-white text-zinc-800 hover:bg-teal-50'
              }`}
            >
              <MapIcon className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Mapas</span>
              <span className="rounded-full bg-zinc-950/10 px-2 py-0.5 text-xs font-extrabold tabular-nums">
                {totalMaps}
              </span>
            </button>
          </div>

          {!searchOpen && !searchQuery ? (
            <button
              type="button"
              onClick={openSearch}
              aria-label="Buscar mods"
              title="Buscar mods"
              className="cartoon-pill inline-flex items-center justify-center rounded-full bg-white text-zinc-800 hover:bg-zinc-100 w-9 h-9 sm:w-10 sm:h-10 cursor-pointer"
            >
              <Search className="w-4 h-4" aria-hidden="true" />
            </button>
          ) : (
            <div className="cartoon-pill inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-sm">
              <Search className="w-4 h-4 text-zinc-500 shrink-0" aria-hidden="true" />
              <input
                ref={inputRef}
                type="search"
                value={searchQuery}
                onChange={(event) => onSearchChange(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Escape') {
                    onSearchChange('');
                    setSearchOpen(false);
                  }
                }}
                placeholder={activeTab === 'cars' ? 'Filtrar autos o .zip...' : 'Filtrar mapas o lugar...'}
                aria-label="Filtrar mods por nombre o archivo"
                className="w-40 sm:w-52 bg-transparent text-sm font-medium text-zinc-900 placeholder:text-zinc-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={clearOrCloseSearch}
                aria-label={searchQuery ? 'Limpiar búsqueda' : 'Cerrar búsqueda'}
                className="rounded-full p-0.5 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
