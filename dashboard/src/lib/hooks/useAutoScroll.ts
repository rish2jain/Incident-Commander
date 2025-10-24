/**
 * useAutoScroll - React hook for integrating AutoScrollManager with components
 *
 * Features:
 * - Automatic lifecycle management
 * - State synchronization with React
 * - Performance optimizations
 * - Easy integration with existing components
 */

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
  AutoScrollManager,
  AutoScrollConfig,
  ScrollState,
} from "../auto-scroll-manager";

export interface UseAutoScrollOptions extends Partial<AutoScrollConfig> {
  enabled?: boolean;
  dependencies?: any[]; // Dependencies that trigger new message detection
}

export interface UseAutoScrollReturn {
  // Refs
  scrollRef: React.RefObject<HTMLElement>;

  // State
  scrollState: ScrollState;
  isAutoScrollEnabled: boolean;
  isNearBottom: boolean;
  isPaused: boolean;

  // Actions
  scrollToBottom: (smooth?: boolean) => void;
  pauseAutoScroll: () => void;
  resumeAutoScroll: () => void;
  handleNewMessage: () => void;

  // Utilities
  shouldShowScrollToBottom: boolean;
  manager: AutoScrollManager | null;
}

/**
 * Custom hook for managing auto-scroll behavior in React components
 */
export function useAutoScroll(
  options: UseAutoScrollOptions = {}
): UseAutoScrollReturn {
  const { enabled = true, dependencies = [], ...config } = options;

  // Refs
  const scrollRef = useRef<HTMLElement>(null);
  const managerRef = useRef<AutoScrollManager | null>(null);
  const previousDepsRef = useRef<any[]>([]);

  // State
  const [scrollState, setScrollState] = useState<ScrollState>({
    isAutoScrollEnabled: true,
    isUserScrolling: false,
    isNearBottom: true,
    lastScrollPosition: 0,
    messageCount: 0,
    isPaused: false,
    lastUserInteraction: 0,
  });

  // Initialize manager
  useEffect(() => {
    if (!enabled) return;

    const manager = new AutoScrollManager(config);
    managerRef.current = manager;

    // Subscribe to state changes
    const unsubscribe = manager.addObserver(setScrollState);

    return () => {
      unsubscribe();
      manager.destroy();
      managerRef.current = null;
    };
  }, [enabled]); // Only recreate when enabled changes

  // Update config when options change
  useEffect(() => {
    if (managerRef.current && enabled) {
      managerRef.current.updateConfig(config);
    }
  }, [
    enabled,
    config.threshold,
    config.resumeDelay,
    config.smoothScroll,
    config.maxScrollSpeed,
    config.debounceDelay,
  ]);

  // Attach/detach from container
  useEffect(() => {
    const manager = managerRef.current;
    const container = scrollRef.current;

    if (manager && container && enabled) {
      manager.attachToContainer(container);

      return () => {
        manager.detachFromContainer();
      };
    }
  }, [enabled]);

  // Handle new messages when dependencies change
  useEffect(() => {
    const manager = managerRef.current;
    if (!manager || !enabled) return;

    // Check if dependencies actually changed (deep comparison for arrays)
    const depsChanged =
      dependencies.length !== previousDepsRef.current.length ||
      dependencies.some((dep, index) => {
        const prevDep = previousDepsRef.current[index];

        // Handle array dependencies (like message lists)
        if (Array.isArray(dep) && Array.isArray(prevDep)) {
          return (
            dep.length !== prevDep.length ||
            dep.some((item, i) => item !== prevDep[i])
          );
        }

        return dep !== prevDep;
      });

    if (depsChanged) {
      // Detect if new messages were added (common case: array length increased)
      const hasNewMessages = dependencies.some((dep, index) => {
        const prevDep = previousDepsRef.current[index];
        return (
          Array.isArray(dep) &&
          Array.isArray(prevDep) &&
          dep.length > prevDep.length
        );
      });

      if (hasNewMessages) {
        manager.handleNewMessage();
      }

      previousDepsRef.current = [...dependencies];
    }
  }, dependencies);

  // Memoized actions
  const scrollToBottom = useCallback((smooth?: boolean) => {
    managerRef.current?.scrollToBottom(smooth);
  }, []);

  const pauseAutoScroll = useCallback(() => {
    managerRef.current?.pauseAutoScroll();
  }, []);

  const resumeAutoScroll = useCallback(() => {
    managerRef.current?.resumeAutoScroll();
  }, []);

  const handleNewMessage = useCallback(() => {
    managerRef.current?.handleNewMessage();
  }, []);

  // Computed values
  const shouldShowScrollToBottom = useMemo(() => {
    return (
      enabled &&
      scrollState.isPaused &&
      !scrollState.isNearBottom &&
      !scrollState.isUserScrolling
    );
  }, [
    enabled,
    scrollState.isPaused,
    scrollState.isNearBottom,
    scrollState.isUserScrolling,
  ]);

  return {
    // Refs
    scrollRef,

    // State
    scrollState,
    isAutoScrollEnabled: scrollState.isAutoScrollEnabled,
    isNearBottom: scrollState.isNearBottom,
    isPaused: scrollState.isPaused,

    // Actions
    scrollToBottom,
    pauseAutoScroll,
    resumeAutoScroll,
    handleNewMessage,

    // Utilities
    shouldShowScrollToBottom,
    manager: managerRef.current,
  };
}

/**
 * Hook for simple auto-scroll behavior with minimal configuration
 */
export function useSimpleAutoScroll(
  dependencies: any[] = [],
  enabled: boolean = true
): Pick<
  UseAutoScrollReturn,
  "scrollRef" | "scrollToBottom" | "shouldShowScrollToBottom"
> {
  const { scrollRef, scrollToBottom, shouldShowScrollToBottom } = useAutoScroll(
    {
      enabled,
      dependencies,
      threshold: 50, // Smaller threshold for simple use case
      resumeDelay: 1000, // Faster resume
      smoothScroll: true,
    }
  );

  return {
    scrollRef,
    scrollToBottom,
    shouldShowScrollToBottom,
  };
}

/**
 * Hook for high-performance auto-scroll with optimizations for rapid updates
 */
export function useHighPerformanceAutoScroll(
  dependencies: any[] = [],
  enabled: boolean = true
): UseAutoScrollReturn {
  return useAutoScroll({
    enabled,
    dependencies,
    threshold: 100,
    resumeDelay: 500, // Faster resume for high-frequency updates
    smoothScroll: false, // Disable smooth scroll for performance
    maxScrollSpeed: 5, // Faster scrolling
    debounceDelay: 50, // Lower debounce for responsiveness
  });
}
