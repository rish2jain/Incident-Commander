import React, { useCallback, useMemo, useRef, useEffect } from "react";

/**
 * Performance optimization utilities for efficient DOM updates
 * Handles React re-renders with proper memoization and high-frequency scenarios
 */

export interface PerformanceConfig {
  enableVirtualization: boolean;
  batchUpdateDelay: number;
  maxItemsBeforeVirtualization: number;
  debounceDelay: number;
  throttleDelay: number;
}

export const DEFAULT_PERFORMANCE_CONFIG: PerformanceConfig = {
  enableVirtualization: true,
  batchUpdateDelay: 16, // ~60fps
  maxItemsBeforeVirtualization: 100,
  debounceDelay: 100,
  throttleDelay: 50,
};

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * Throttle function for performance optimization
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;
  let timeoutId: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    const now = Date.now();

    if (now - lastCall >= delay) {
      lastCall = now;
      func(...args);
    } else if (!timeoutId) {
      timeoutId = setTimeout(() => {
        lastCall = Date.now();
        timeoutId = null;
        func(...args);
      }, delay - (now - lastCall));
    }
  };
}

/**
 * Batch DOM updates using requestAnimationFrame
 */
export class BatchUpdateManager {
  private pendingUpdates: Set<() => void> = new Set();
  private isScheduled = false;

  scheduleUpdate(updateFn: () => void): void {
    this.pendingUpdates.add(updateFn);

    if (!this.isScheduled) {
      this.isScheduled = true;
      requestAnimationFrame(() => {
        this.flushUpdates();
      });
    }
  }

  private flushUpdates(): void {
    const updates = Array.from(this.pendingUpdates);
    this.pendingUpdates.clear();
    this.isScheduled = false;

    // Execute all pending updates in a single frame
    updates.forEach((update) => {
      try {
        update();
      } catch (error) {
        console.error("Error in batched update:", error);
      }
    });
  }

  clear(): void {
    this.pendingUpdates.clear();
    this.isScheduled = false;
  }
}

/**
 * Hook for efficient list rendering with memoization
 */
export function useOptimizedList<T>(
  items: T[],
  keyExtractor: (item: T, index: number) => string,
  config: Partial<PerformanceConfig> = {}
) {
  const fullConfig = { ...DEFAULT_PERFORMANCE_CONFIG, ...config };
  const previousItemsRef = useRef<T[]>([]);
  const memoizedItemsRef = useRef<Map<string, T>>(new Map());

  // Detect if we need virtualization
  const shouldVirtualize = useMemo(() => {
    return (
      fullConfig.enableVirtualization &&
      items.length > fullConfig.maxItemsBeforeVirtualization
    );
  }, [
    items.length,
    fullConfig.enableVirtualization,
    fullConfig.maxItemsBeforeVirtualization,
  ]);

  // Memoize items to prevent unnecessary re-renders
  const optimizedItems = useMemo(() => {
    const newItemsMap = new Map<string, T>();
    const result: T[] = [];

    items.forEach((item, index) => {
      const key = keyExtractor(item, index);

      // Reuse memoized item if it hasn't changed
      if (memoizedItemsRef.current.has(key)) {
        const memoizedItem = memoizedItemsRef.current.get(key)!;
        // Simple shallow comparison - in real apps, you might want deep comparison
        if (JSON.stringify(memoizedItem) === JSON.stringify(item)) {
          newItemsMap.set(key, memoizedItem);
          result.push(memoizedItem);
          return;
        }
      }

      // Store new/changed item
      newItemsMap.set(key, item);
      result.push(item);
    });

    // Update memoized items
    memoizedItemsRef.current = newItemsMap;
    previousItemsRef.current = result;

    return result;
  }, [items, keyExtractor]);

  // Calculate visible range for virtualization
  const getVisibleRange = useCallback(
    (containerHeight: number, itemHeight: number, scrollTop: number) => {
      if (!shouldVirtualize) {
        return { start: 0, end: optimizedItems.length };
      }

      const visibleCount = Math.ceil(containerHeight / itemHeight);
      const start = Math.floor(scrollTop / itemHeight);
      const end = Math.min(start + visibleCount + 5, optimizedItems.length); // +5 for buffer

      return { start: Math.max(0, start - 2), end }; // -2 for buffer
    },
    [shouldVirtualize, optimizedItems.length]
  );

  return {
    items: optimizedItems,
    shouldVirtualize,
    getVisibleRange,
    totalCount: items.length,
  };
}

/**
 * Hook for efficient re-render prevention with deep comparison
 */
export function useDeepMemo<T>(value: T, deps: React.DependencyList): T {
  const ref = useRef<T>(value);
  const depsRef = useRef(deps);

  return useMemo(() => {
    // Check if dependencies have changed
    const depsChanged = deps.some((dep, index) => {
      const prevDep = depsRef.current[index];
      return !Object.is(dep, prevDep);
    });

    if (depsChanged) {
      ref.current = value;
      depsRef.current = deps;
    }

    return ref.current;
  }, deps);
}

/**
 * Hook for performance monitoring and optimization
 */
export function usePerformanceMonitor(componentName: string) {
  const renderCountRef = useRef(0);
  const lastRenderTimeRef = useRef(Date.now());
  const performanceDataRef = useRef({
    averageRenderTime: 0,
    maxRenderTime: 0,
    renderCount: 0,
  });

  useEffect(() => {
    const now = Date.now();
    const renderTime = now - lastRenderTimeRef.current;

    renderCountRef.current++;
    performanceDataRef.current.renderCount = renderCountRef.current;

    // Update performance metrics
    const data = performanceDataRef.current;
    data.averageRenderTime =
      (data.averageRenderTime * (data.renderCount - 1) + renderTime) /
      data.renderCount;
    data.maxRenderTime = Math.max(data.maxRenderTime, renderTime);

    // Log performance warnings
    if (renderTime > 16) {
      // More than one frame at 60fps
      console.warn(
        `${componentName} render took ${renderTime}ms (>16ms threshold)`
      );
    }

    if (data.renderCount % 100 === 0) {
      console.log(`${componentName} performance:`, {
        renders: data.renderCount,
        avgTime: data.averageRenderTime.toFixed(2) + "ms",
        maxTime: data.maxRenderTime + "ms",
      });
    }

    lastRenderTimeRef.current = now;
  });

  return performanceDataRef.current;
}

/**
 * Hook for efficient event handler memoization
 */
export function useStableCallback<T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T {
  const callbackRef = useRef<T>(callback);
  const depsRef = useRef(deps);

  // Update callback if dependencies changed
  useEffect(() => {
    callbackRef.current = callback;
    depsRef.current = deps;
  }, deps);

  // Return stable callback reference
  return useCallback((...args: Parameters<T>) => {
    return callbackRef.current(...args);
  }, []) as T;
}

/**
 * Memory usage monitoring utilities
 */
export class MemoryMonitor {
  private static instance: MemoryMonitor;
  private measurements: number[] = [];
  private maxMeasurements = 100;

  static getInstance(): MemoryMonitor {
    if (!MemoryMonitor.instance) {
      MemoryMonitor.instance = new MemoryMonitor();
    }
    return MemoryMonitor.instance;
  }

  measureMemory(): number | null {
    if ("memory" in performance) {
      const memory = (performance as any).memory;
      const usedJSHeapSize = memory.usedJSHeapSize;

      this.measurements.push(usedJSHeapSize);
      if (this.measurements.length > this.maxMeasurements) {
        this.measurements.shift();
      }

      return usedJSHeapSize;
    }
    return null;
  }

  getMemoryStats() {
    if (this.measurements.length === 0) return null;

    const latest = this.measurements[this.measurements.length - 1];
    const average =
      this.measurements.reduce((a, b) => a + b, 0) / this.measurements.length;
    const max = Math.max(...this.measurements);
    const min = Math.min(...this.measurements);

    return {
      current: latest,
      average,
      max,
      min,
      trend:
        this.measurements.length > 1
          ? latest - this.measurements[this.measurements.length - 2]
          : 0,
    };
  }

  checkMemoryLeak(): boolean {
    if (this.measurements.length < 10) return false;

    // Check if memory is consistently increasing
    const recentMeasurements = this.measurements.slice(-10);
    let increasingCount = 0;

    for (let i = 1; i < recentMeasurements.length; i++) {
      if (recentMeasurements[i] > recentMeasurements[i - 1]) {
        increasingCount++;
      }
    }

    // If memory increased in 80% of recent measurements, potential leak
    return increasingCount >= 8;
  }
}

/**
 * Hook for memory monitoring
 */
export function useMemoryMonitor(interval: number = 5000) {
  const memoryMonitor = MemoryMonitor.getInstance();
  const [memoryStats, setMemoryStats] = React.useState<any>(null);

  useEffect(() => {
    const measureInterval = setInterval(() => {
      memoryMonitor.measureMemory();
      const stats = memoryMonitor.getMemoryStats();
      setMemoryStats(stats);

      // Check for memory leaks
      if (memoryMonitor.checkMemoryLeak()) {
        console.warn("Potential memory leak detected!", stats);
      }
    }, interval);

    return () => clearInterval(measureInterval);
  }, [interval, memoryMonitor]);

  return memoryStats;
}
