export type ModSource = 'mods' | 'repo';

export type PinAspectRatio = 'tall' | 'medium' | 'wide' | 'square';

export interface CarModItem {
  id: string;
  zipName: string;
  source: ModSource;
  displayName: string;
  brand: string;
  realCarQuery: string;
  realImageUrl: string;
  gamePreviewUrl?: string;
  category: 'auto' | 'camion';
  aspectRatio: PinAspectRatio;
}

export interface MapModItem {
  id: string;
  zipName: string;
  source: ModSource;
  internalId: string;
  displayName: string;
  description: string;
  isRealWorld: boolean;
  realLocationName?: string;
  realImageUrl?: string;
  gameImageUrl: string;
  aspectRatio: PinAspectRatio;
}

export interface ModsCatalog {
  generatedAt: string;
  stats: {
    totalCars: number;
    totalMaps: number;
    realWorldMaps: number;
    fictionalMaps: number;
  };
  cars: CarModItem[];
  maps: MapModItem[];
}
