import { useEffect, useMemo, useState, type ReactNode } from 'react';

export interface MasonryAspectItem {
  id: string;
  aspectWidth: number;
  aspectHeight: number;
}

interface MasonryGridProps<T extends MasonryAspectItem> {
  items: T[];
  renderItem: (item: T, originalIndex: number) => ReactNode;
}

function resolveColumnCount(): number {
  if (typeof window === 'undefined') return 5;
  if (window.matchMedia('(min-width: 1024px)').matches) return 5;
  if (window.matchMedia('(min-width: 768px)').matches) return 4;
  if (window.matchMedia('(min-width: 640px)').matches) return 3;
  return 2;
}

function useResponsiveColumns(): number {
  const [columnCount, setColumnCount] = useState<number>(resolveColumnCount);

  useEffect(() => {
    const queries = [
      window.matchMedia('(min-width: 1024px)'),
      window.matchMedia('(min-width: 768px)'),
      window.matchMedia('(min-width: 640px)'),
    ];

    const handleChange = () => setColumnCount(resolveColumnCount());
    handleChange();

    for (const mq of queries) {
      mq.addEventListener('change', handleChange);
    }

    return () => {
      for (const mq of queries) {
        mq.removeEventListener('change', handleChange);
      }
    };
  }, []);

  return columnCount;
}

/**
 * Deterministic multi-column masonry layout.
 * Assigns each item to the shortest column using its precomputed aspect ratio
 * so cards never reflow or switch columns while scrolling.
 */
export function MasonryGrid<T extends MasonryAspectItem>({
  items,
  renderItem,
}: MasonryGridProps<T>) {
  const columnCount = useResponsiveColumns();

  const columns = useMemo(() => {
    const cols: Array<Array<{ item: T; originalIndex: number }>> = Array.from(
      { length: columnCount },
      () => []
    );
    const heights = new Array<number>(columnCount).fill(0);

    items.forEach((item, originalIndex) => {
      let shortestCol = 0;
      for (let c = 1; c < columnCount; c++) {
        if (heights[c] < heights[shortestCol]) {
          shortestCol = c;
        }
      }
      const w = item.aspectWidth > 0 ? item.aspectWidth : 4;
      const h = item.aspectHeight > 0 ? item.aspectHeight : 3;
      cols[shortestCol].push({ item, originalIndex });
      heights[shortestCol] += h / w + 0.06;
    });

    return cols;
  }, [items, columnCount]);

  return (
    <div className="flex items-start gap-4">
      {columns.map((columnItems, columnIndex) => (
        <div key={columnIndex} className="flex min-w-0 flex-1 flex-col gap-4">
          {columnItems.map(({ item, originalIndex }) => (
            <div key={item.id}>{renderItem(item, originalIndex)}</div>
          ))}
        </div>
      ))}
    </div>
  );
}
