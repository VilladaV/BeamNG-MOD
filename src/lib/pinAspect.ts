import type { PinAspectRatio } from '@/types/mods';

const PIN_ASPECT_CLASSES: Record<PinAspectRatio, string> = {
  tall: 'aspect-[3/4]',
  medium: 'aspect-[4/3]',
  wide: 'aspect-[16/10]',
  square: 'aspect-square',
};

/**
 * Returns the fixed Tailwind aspect-ratio utility class for a masonry pin
 * so images reserve exact vertical space before decoding (preventing CLS).
 */
export function getPinAspectClass(aspectRatio: PinAspectRatio): string {
  return PIN_ASPECT_CLASSES[aspectRatio];
}
