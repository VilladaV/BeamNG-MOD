import rawCatalog from './modsCatalog.json';
import type { ModsCatalog } from '@/types/mods';

/**
 * Strongly typed catalog of locally installed BeamNG.drive car and map mods.
 */
export const modsCatalog = rawCatalog as ModsCatalog;
