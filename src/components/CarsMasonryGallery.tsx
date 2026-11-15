import { CarPinCard } from '@/components/CarPinCard';
import type { CarModItem } from '@/types/mods';

interface CarsMasonryGalleryProps {
  cars: CarModItem[];
  searchQuery: string;
}

export function CarsMasonryGallery({ cars, searchQuery }: CarsMasonryGalleryProps) {
  if (cars.length === 0) {
    return (
      <div className="mx-auto max-w-md rounded-2xl border-2 border-dashed border-zinc-300 bg-white/80 px-6 py-12 text-center">
        <p className="font-comic-display text-lg font-bold text-zinc-800">
          No encontramos autos para &ldquo;{searchQuery}&rdquo;
        </p>
        <p className="mt-1 text-sm text-zinc-500">
          Prueba con otra marca, modelo o nombre del archivo `.zip`.
        </p>
      </div>
    );
  }

  return (
    <section aria-label="Galería de autos reales">
      <div className="columns-2 gap-4 sm:columns-3 md:columns-4 lg:columns-5">
        {cars.map((car, index) => (
          <CarPinCard key={car.id} car={car} index={index} />
        ))}
      </div>
    </section>
  );
}
