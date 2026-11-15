import { useMemo, useState } from 'react';
import { CartoonHeader, type GallerySection } from '@/components/CartoonHeader';
import { CarsMasonryGallery } from '@/components/CarsMasonryGallery';
import { MapsMasonryGallery } from '@/components/MapsMasonryGallery';
import { modsCatalog } from '@/data/catalog';

function normalizeText(value: string): string {
  return value.trim().toLowerCase();
}

export default function App() {
  const [activeTab, setActiveTab] = useState<GallerySection>('cars');
  const [searchQuery, setSearchQuery] = useState('');

  const normalizedQuery = normalizeText(searchQuery);

  const filteredCars = useMemo(() => {
    if (!normalizedQuery) return modsCatalog.cars;
    return modsCatalog.cars.filter(
      (car) =>
        car.displayName.toLowerCase().includes(normalizedQuery) ||
        car.brand.toLowerCase().includes(normalizedQuery) ||
        car.realCarQuery.toLowerCase().includes(normalizedQuery) ||
        car.zipName.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery]);

  const filteredMaps = useMemo(() => {
    if (!normalizedQuery) return modsCatalog.maps;
    return modsCatalog.maps.filter(
      (map) =>
        map.displayName.toLowerCase().includes(normalizedQuery) ||
        map.internalId.toLowerCase().includes(normalizedQuery) ||
        (map.realLocationName?.toLowerCase().includes(normalizedQuery) ?? false) ||
        map.zipName.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery]);

  return (
    <div className="min-h-screen bg-[#fbfaf8] text-zinc-900">
      <CartoonHeader
        activeTab={activeTab}
        onTabChange={setActiveTab}
        totalCars={modsCatalog.stats.totalCars}
        totalMaps={modsCatalog.stats.totalMaps}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      <main className="mx-auto max-w-[1680px] px-3 pb-14 sm:px-6 lg:px-8">
        <div
          id="panel-cars"
          role="tabpanel"
          aria-labelledby="tab-cars"
          aria-hidden={activeTab !== 'cars'}
          className={`cached-view ${activeTab === 'cars' ? 'is-active' : ''}`}
        >
          <CarsMasonryGallery cars={filteredCars} searchQuery={searchQuery} />
        </div>

        <div
          id="panel-maps"
          role="tabpanel"
          aria-labelledby="tab-maps"
          aria-hidden={activeTab !== 'maps'}
          className={`cached-view ${activeTab === 'maps' ? 'is-active' : ''}`}
        >
          <MapsMasonryGallery
            maps={filteredMaps}
            searchQuery={searchQuery}
            isActiveSection={activeTab === 'maps'}
          />
        </div>
      </main>
    </div>
  );
}
