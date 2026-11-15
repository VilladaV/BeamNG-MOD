import { initializeApp } from 'firebase/app';
import {
  doc,
  getFirestore,
  onSnapshot,
  setDoc,
  type Unsubscribe,
} from 'firebase/firestore';

export interface CloudPinCoord {
  x: number;
  y: number;
}

export type CloudPinMap = Record<string, CloudPinCoord>;

const firebaseConfig = {
  apiKey: 'AIzaSyD_igqzrQz6k-fDiD8IQxueSfYHDipmRb0',
  authDomain: 'beamng-mods-villadav-2026.firebaseapp.com',
  projectId: 'beamng-mods-villadav-2026',
  storageBucket: 'beamng-mods-villadav-2026.firebasestorage.app',
  messagingSenderId: '54944437789',
  appId: '1:54944437789:web:39745d7b3d56bc57f718f4',
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);

const SHARED_PINS_DOC = doc(db, 'worldMap', 'sharedPins');

function clampCoord(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function sanitizePinsRecord(raw: unknown, validIds: Set<string>): CloudPinMap {
  if (!raw || typeof raw !== 'object') return {};
  const clean: CloudPinMap = {};
  for (const [id, coord] of Object.entries(raw as Record<string, unknown>)) {
    if (!validIds.has(id) || !coord || typeof coord !== 'object') continue;
    const c = coord as { x?: unknown; y?: unknown };
    if (typeof c.x === 'number' && Number.isFinite(c.x) && typeof c.y === 'number' && Number.isFinite(c.y)) {
      clean[id] = {
        x: Number(clampCoord(c.x, 1.2, 98.8).toFixed(2)),
        y: Number(clampCoord(c.y, 1.5, 98.5).toFixed(2)),
      };
    }
  }
  return clean;
}

/**
 * Subscribe in real time to the shared Cartoon World Map pin coordinates.
 * Real-time `onSnapshot` is required so placements made on PC or mobile
 * propagate immediately across connected devices without page reload.
 */
export function subscribeToSharedWorldPins(
  validIds: Set<string>,
  handlers: {
    onRemotePins: (pins: CloudPinMap) => void;
    onMissingRemote: () => CloudPinMap;
    onError: (err: Error) => void;
  }
): Unsubscribe {
  return onSnapshot(
    SHARED_PINS_DOC,
    (snapshot) => {
      if (!snapshot.exists()) {
        const seedPins = handlers.onMissingRemote();
        void saveSharedWorldPins(seedPins).catch((err: unknown) => {
          handlers.onError(err instanceof Error ? err : new Error(String(err)));
        });
        return;
      }

      const data = snapshot.data() as { pins?: unknown } | undefined;
      const clean = sanitizePinsRecord(data?.pins, validIds);
      handlers.onRemotePins(clean);
    },
    (err) => {
      handlers.onError(err);
    }
  );
}

/** Persist the shared Cartoon World Map pin coordinates to Cloud Firestore. */
export async function saveSharedWorldPins(pins: CloudPinMap): Promise<void> {
  await setDoc(SHARED_PINS_DOC, {
    pins,
    updatedAt: new Date().toISOString(),
  });
}
