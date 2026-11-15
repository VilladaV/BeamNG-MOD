import { MapPinCard } from '@/components/MapPinCard';
import type { MapModItem } from '@/types/mods';

interface MapsMasonryGalleryProps {
  maps: MapModItem[];
  searchQuery: string;
  isActiveSection: boolean;
}

export function MapsMasonryGallery({
  maps,
  searchQuery,
  isActiveSection,
}: MapsMasonryGalleryProps) {
  if (maps.length === 0) {
    return (
      <div className="mx-auto max-w-md rounded-2xl border-2 border-dashed border-zinc-300 bg-white/80 px-6 py-12 text-center">
        <p className="font-comic-display text-lg font-bold text-zinc-800">
          No encontramos mapas para &ldquo;{searchQuery}&rdquo;
        </p>
        <p className="mt-1 text-sm text-zinc-500">
          Prueba con otro nombre interno, ubicación real o archivo `.zip`.
        </p>
      </div>
    );
  }

  return (
    <section aria-label="Galería de mapas y lugares reales">
      <div className="columns-2 gap-4 sm:columns-3 md:columns-4 lg:columns-5">
        {maps.map((map, index) => (
          <MapPinCard
            key={map.id}
            map={map}
            index={index}
            isActiveSection={isActiveSection}
          />
        ))}
      </div>
    </section>
  );
}
