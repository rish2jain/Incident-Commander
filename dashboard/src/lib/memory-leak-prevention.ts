import { useCallback, useEffect, useRef } from "react";

/**
 * Memory leak prevention utilities
 * Implements cleanup for event listeners, timers, and memory usage monitoring
 */

export interface MemoryConfig {
  enableMonitoring: boolean;
  monitoringInterval: number;
  memoryThreshold: number; // MB
  leakDetectionSamples: number;
  autoCleanup: boolean;
  maxEventListeners: number;
  maxTimers: number;
}

export const DEFAULT_MEMORY_CONFIG: MemoryConfig = {
  enableMonitoring: true,
  monitoringInterval: 5000, // 5 seconds
  memoryThreshold: 100, // 100MB
  leakDetectionSamples: 10,
  autoCleanup: true,
  maxEventListeners: 50,
  maxTimers: 20,
};

export interface MemoryStats {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
  memoryUsageMB: number;
  isMemoryAvailable: boolean;
  trend: "increasing" | "decreasing" | "stable";
  leakSuspected: boolean;
}

export interface ResourceTracker {
  eventListeners: Map<string, Set<EventListenerInfo>>;
  timers: Map<string, Set<TimerInfo>>;
  observers: Map<string, Set<ObserverInfo>>;
  subscriptions: Map<string, Set<SubscriptionInfo>>;
}

export interface EventListenerInfo {
  id: string;
  element: EventTarget;
  event: string;
  handler: EventListener;
  options?: AddEventListenerOptions;
  addedAt: number;
}

export interface TimerInfo {
  id: string;
  type: "timeout" | "interval";
  timerId: NodeJS.Timeout;
  callback: Function;
  delay: number;
  createdAt: number;
}

export interface ObserverInfo {
  id: string;
  type: "mutation" | "intersection" | "resize" | "performance";
  observer: any;
  createdAt: number;
}

export interface SubscriptionInfo {
  id: string;
  name: string;
  unsubscribe: () => void;
  createdAt: number;
}

/**
 * Memory leak prevention and monitoring manager
 */
export class MemoryLeakPrevention {
  private config: MemoryConfig;
  private memoryHistory: number[] = [];
  private resourceTracker: ResourceTracker;
  private monitoringTimer: NodeJS.Timeout | null = null;
  private componentId: string;
  private isDestroyed = false;

  // Callbacks
  private memoryWarningCallbacks = new Set<(stats: MemoryStats) => void>();
  private leakDetectedCallbacks = new Set<(stats: MemoryStats) => void>();

  constructor(componentId: string, config: Partial<MemoryConfig> = {}) {
    this.componentId = componentId;
    this.config = { ...DEFAULT_MEMORY_CONFIG, ...config };

    this.resourceTracker = {
      eventListeners: new Map(),
      timers: new Map(),
      observers: new Map(),
      subscriptions: new Map(),
    };

    if (this.config.enableMonitoring) {
      this.startMonitoring();
    }
  }

  /**
   * Add event listener with automatic cleanup tracking
   */
  addEventListener(
    element: EventTarget,
    event: string,
    handler: EventListener,
    options?: AddEventListenerOptions
  ): () => void {
    const id = this.generateId();
    const listenerInfo: EventListenerInfo = {
      id,
      element,
      event,
      handler,
      options,
      addedAt: Date.now(),
    };

    // Add to tracker
    if (!this.resourceTracker.eventListeners.has(this.componentId)) {
      this.resourceTracker.eventListeners.set(this.componentId, new Set());
    }
    this.resourceTracker.eventListeners
      .get(this.componentId)!
      .add(listenerInfo);

    // Check limits
    this.checkEventListenerLimits();

    // Add the actual event listener
    element.addEventListener(event, handler, options);

    // Return cleanup function
    return () => {
      this.removeEventListener(id);
    };
  }

  /**
   * Remove specific event listener
   */
  removeEventListener(id: string): void {
    const listeners = this.resourceTracker.eventListeners.get(this.componentId);
    if (!listeners) return;

    Array.from(listeners).forEach((listener) => {
      if (listener.id === id) {
        listener.element.removeEventListener(
          listener.event,
          listener.handler,
          listener.options
        );
        listeners.delete(listener);
      }
    });
  }

  /**
   * Set timeout with automatic cleanup tracking
   */
  setTimeout(callback: Function, delay: number): NodeJS.Timeout {
    const id = this.generateId();
    const timerId = setTimeout(() => {
      callback();
      this.removeTimer(id);
    }, delay) as NodeJS.Timeout;

    const timerInfo: TimerInfo = {
      id,
      type: "timeout",
      timerId,
      callback,
      delay,
      createdAt: Date.now(),
    };

    // Add to tracker
    if (!this.resourceTracker.timers.has(this.componentId)) {
      this.resourceTracker.timers.set(this.componentId, new Set());
    }
    this.resourceTracker.timers.get(this.componentId)!.add(timerInfo);

    this.checkTimerLimits();

    return timerId;
  }

  /**
   * Set interval with automatic cleanup tracking
   */
  setInterval(callback: Function, delay: number): NodeJS.Timeout {
    const id = this.generateId();
    const timerId = setInterval(callback, delay) as unknown as NodeJS.Timeout;

    const timerInfo: TimerInfo = {
      id,
      type: "interval",
      timerId,
      callback,
      delay,
      createdAt: Date.now(),
    };

    // Add to tracker
    if (!this.resourceTracker.timers.has(this.componentId)) {
      this.resourceTracker.timers.set(this.componentId, new Set());
    }
    this.resourceTracker.timers.get(this.componentId)!.add(timerInfo);

    this.checkTimerLimits();

    return timerId;
  }

  /**
   * Remove specific timer
   */
  removeTimer(id: string): void {
    const timers = this.resourceTracker.timers.get(this.componentId);
    if (!timers) return;

    Array.from(timers).forEach((timer) => {
      if (timer.id === id) {
        if (timer.type === "timeout") {
          clearTimeout(timer.timerId);
        } else {
          clearInterval(timer.timerId);
        }
        timers.delete(timer);
      }
    });
  }

  /**
   * Track observer with automatic cleanup
   */
  trackObserver(
    type: "mutation" | "intersection" | "resize" | "performance",
    observer: any
  ): () => void {
    const id = this.generateId();
    const observerInfo: ObserverInfo = {
      id,
      type,
      observer,
      createdAt: Date.now(),
    };

    // Add to tracker
    if (!this.resourceTracker.observers.has(this.componentId)) {
      this.resourceTracker.observers.set(this.componentId, new Set());
    }
    this.resourceTracker.observers.get(this.componentId)!.add(observerInfo);

    // Return cleanup function
    return () => {
      this.removeObserver(id);
    };
  }

  /**
   * Remove specific observer
   */
  removeObserver(id: string): void {
    const observers = this.resourceTracker.observers.get(this.componentId);
    if (!observers) return;

    Array.from(observers).forEach((observer) => {
      if (observer.id === id) {
        if (
          observer.observer &&
          typeof observer.observer.disconnect === "function"
        ) {
          observer.observer.disconnect();
        }
        observers.delete(observer);
      }
    });
  }

  /**
   * Track subscription with automatic cleanup
   */
  trackSubscription(name: string, unsubscribe: () => void): () => void {
    const id = this.generateId();
    const subscriptionInfo: SubscriptionInfo = {
      id,
      name,
      unsubscribe,
      createdAt: Date.now(),
    };

    // Add to tracker
    if (!this.resourceTracker.subscriptions.has(this.componentId)) {
      this.resourceTracker.subscriptions.set(this.componentId, new Set());
    }
    this.resourceTracker.subscriptions
      .get(this.componentId)!
      .add(subscriptionInfo);

    // Return cleanup function
    return () => {
      this.removeSubscription(id);
    };
  }

  /**
   * Remove specific subscription
   */
  removeSubscription(id: string): void {
    const subscriptions = this.resourceTracker.subscriptions.get(
      this.componentId
    );
    if (!subscriptions) return;

    Array.from(subscriptions).forEach((subscription) => {
      if (subscription.id === id) {
        subscription.unsubscribe();
        subscriptions.delete(subscription);
      }
    });
  }

  /**
   * Get current memory statistics
   */
  getMemoryStats(): MemoryStats {
    const stats: MemoryStats = {
      usedJSHeapSize: 0,
      totalJSHeapSize: 0,
      jsHeapSizeLimit: 0,
      memoryUsageMB: 0,
      isMemoryAvailable: false,
      trend: "stable",
      leakSuspected: false,
    };

    if ("memory" in performance) {
      const memory = (performance as any).memory;
      stats.usedJSHeapSize = memory.usedJSHeapSize;
      stats.totalJSHeapSize = memory.totalJSHeapSize;
      stats.jsHeapSizeLimit = memory.jsHeapSizeLimit;
      stats.memoryUsageMB = memory.usedJSHeapSize / (1024 * 1024);
      stats.isMemoryAvailable = true;

      // Calculate trend
      if (this.memoryHistory.length >= 2) {
        const recent = this.memoryHistory.slice(-3);
        const isIncreasing = recent.every(
          (val, i) => i === 0 || val > recent[i - 1]
        );
        const isDecreasing = recent.every(
          (val, i) => i === 0 || val < recent[i - 1]
        );

        stats.trend = isIncreasing
          ? "increasing"
          : isDecreasing
          ? "decreasing"
          : "stable";
      }

      // Detect potential leaks
      stats.leakSuspected = this.detectMemoryLeak();
    }

    return stats;
  }

  /**
   * Get resource usage summary
   */
  getResourceSummary() {
    const eventListeners =
      this.resourceTracker.eventListeners.get(this.componentId)?.size || 0;
    const timers = this.resourceTracker.timers.get(this.componentId)?.size || 0;
    const observers =
      this.resourceTracker.observers.get(this.componentId)?.size || 0;
    const subscriptions =
      this.resourceTracker.subscriptions.get(this.componentId)?.size || 0;

    return {
      eventListeners,
      timers,
      observers,
      subscriptions,
      total: eventListeners + timers + observers + subscriptions,
    };
  }

  /**
   * Force garbage collection (if available)
   */
  forceGarbageCollection(): void {
    if ("gc" in window && typeof (window as any).gc === "function") {
      (window as any).gc();
    }
  }

  /**
   * Subscribe to memory warnings
   */
  onMemoryWarning(callback: (stats: MemoryStats) => void): () => void {
    this.memoryWarningCallbacks.add(callback);
    return () => this.memoryWarningCallbacks.delete(callback);
  }

  /**
   * Subscribe to leak detection
   */
  onLeakDetected(callback: (stats: MemoryStats) => void): () => void {
    this.leakDetectedCallbacks.add(callback);
    return () => this.leakDetectedCallbacks.delete(callback);
  }

  /**
   * Clean up all resources for this component
   */
  cleanup(): void {
    if (this.isDestroyed) return;

    // Clean up event listeners
    const listeners = this.resourceTracker.eventListeners.get(this.componentId);
    if (listeners) {
      listeners.forEach((listener) => {
        listener.element.removeEventListener(
          listener.event,
          listener.handler,
          listener.options
        );
      });
      listeners.clear();
    }

    // Clean up timers
    const timers = this.resourceTracker.timers.get(this.componentId);
    if (timers) {
      timers.forEach((timer) => {
        if (timer.type === "timeout") {
          clearTimeout(timer.timerId);
        } else {
          clearInterval(timer.timerId);
        }
      });
      timers.clear();
    }

    // Clean up observers
    const observers = this.resourceTracker.observers.get(this.componentId);
    if (observers) {
      observers.forEach((observer) => {
        if (
          observer.observer &&
          typeof observer.observer.disconnect === "function"
        ) {
          observer.observer.disconnect();
        }
      });
      observers.clear();
    }

    // Clean up subscriptions
    const subscriptions = this.resourceTracker.subscriptions.get(
      this.componentId
    );
    if (subscriptions) {
      subscriptions.forEach((subscription) => {
        subscription.unsubscribe();
      });
      subscriptions.clear();
    }

    // Stop monitoring
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
      this.monitoringTimer = null;
    }

    this.isDestroyed = true;
  }

  private startMonitoring(): void {
    this.monitoringTimer = setInterval(() => {
      if (this.isDestroyed) return;

      const stats = this.getMemoryStats();

      if (stats.isMemoryAvailable) {
        // Add to history
        this.memoryHistory.push(stats.usedJSHeapSize);
        if (this.memoryHistory.length > this.config.leakDetectionSamples) {
          this.memoryHistory.shift();
        }

        // Check thresholds
        if (stats.memoryUsageMB > this.config.memoryThreshold) {
          this.notifyMemoryWarning(stats);
        }

        if (stats.leakSuspected) {
          this.notifyLeakDetected(stats);
        }
      }
    }, this.config.monitoringInterval);
  }

  private detectMemoryLeak(): boolean {
    if (this.memoryHistory.length < this.config.leakDetectionSamples) {
      return false;
    }

    // Check if memory is consistently increasing
    let increasingCount = 0;
    for (let i = 1; i < this.memoryHistory.length; i++) {
      if (this.memoryHistory[i] > this.memoryHistory[i - 1]) {
        increasingCount++;
      }
    }

    // If 80% of samples show increase, suspect a leak
    return increasingCount >= this.config.leakDetectionSamples * 0.8;
  }

  private checkEventListenerLimits(): void {
    const count =
      this.resourceTracker.eventListeners.get(this.componentId)?.size || 0;
    if (count > this.config.maxEventListeners) {
      console.warn(
        `Component ${this.componentId} has ${count} event listeners (limit: ${this.config.maxEventListeners})`
      );
    }
  }

  private checkTimerLimits(): void {
    const count = this.resourceTracker.timers.get(this.componentId)?.size || 0;
    if (count > this.config.maxTimers) {
      console.warn(
        `Component ${this.componentId} has ${count} timers (limit: ${this.config.maxTimers})`
      );
    }
  }

  private notifyMemoryWarning(stats: MemoryStats): void {
    this.memoryWarningCallbacks.forEach((callback) => {
      try {
        callback(stats);
      } catch (error) {
        console.error("Memory warning callback error:", error);
      }
    });
  }

  private notifyLeakDetected(stats: MemoryStats): void {
    this.leakDetectedCallbacks.forEach((callback) => {
      try {
        callback(stats);
      } catch (error) {
        console.error("Leak detection callback error:", error);
      }
    });
  }

  private generateId(): string {
    return `${this.componentId}-${Date.now()}-${Math.random()
      .toString(36)
      .substr(2, 9)}`;
  }
}

/**
 * React hook for memory leak prevention
 */
export function useMemoryLeakPrevention(
  componentName: string,
  config: Partial<MemoryConfig> = {}
) {
  const managerRef = useRef<MemoryLeakPrevention>();
  const componentId = `${componentName}-${
    useRef(Math.random().toString(36).substr(2, 9)).current
  }`;

  // Initialize manager
  useEffect(() => {
    managerRef.current = new MemoryLeakPrevention(componentId, config);

    return () => {
      managerRef.current?.cleanup();
    };
  }, [componentId]);

  // Wrapped methods for easier use
  const addEventListener = useCallback(
    (
      element: EventTarget,
      event: string,
      handler: EventListener,
      options?: AddEventListenerOptions
    ) => {
      return (
        managerRef.current?.addEventListener(
          element,
          event,
          handler,
          options
        ) || (() => {})
      );
    },
    []
  );

  const setTimeout = useCallback((callback: Function, delay: number) => {
    return managerRef.current?.setTimeout(callback, delay) || (null as any);
  }, []);

  const setInterval = useCallback((callback: Function, delay: number) => {
    return managerRef.current?.setInterval(callback, delay) || (null as any);
  }, []);

  const trackObserver = useCallback(
    (
      type: "mutation" | "intersection" | "resize" | "performance",
      observer: any
    ) => {
      return managerRef.current?.trackObserver(type, observer) || (() => {});
    },
    []
  );

  const trackSubscription = useCallback(
    (name: string, unsubscribe: () => void) => {
      return (
        managerRef.current?.trackSubscription(name, unsubscribe) || (() => {})
      );
    },
    []
  );

  const getMemoryStats = useCallback(() => {
    return (
      managerRef.current?.getMemoryStats() || {
        usedJSHeapSize: 0,
        totalJSHeapSize: 0,
        jsHeapSizeLimit: 0,
        memoryUsageMB: 0,
        isMemoryAvailable: false,
        trend: "stable" as const,
        leakSuspected: false,
      }
    );
  }, []);

  const getResourceSummary = useCallback(() => {
    return (
      managerRef.current?.getResourceSummary() || {
        eventListeners: 0,
        timers: 0,
        observers: 0,
        subscriptions: 0,
        total: 0,
      }
    );
  }, []);

  const onMemoryWarning = useCallback(
    (callback: (stats: MemoryStats) => void) => {
      return managerRef.current?.onMemoryWarning(callback) || (() => {});
    },
    []
  );

  const onLeakDetected = useCallback(
    (callback: (stats: MemoryStats) => void) => {
      return managerRef.current?.onLeakDetected(callback) || (() => {});
    },
    []
  );

  return {
    addEventListener,
    setTimeout,
    setInterval,
    trackObserver,
    trackSubscription,
    getMemoryStats,
    getResourceSummary,
    onMemoryWarning,
    onLeakDetected,
  };
}

/**
 * Hook for automatic cleanup of refs and callbacks
 */
export function useAutoCleanup() {
  const cleanupFunctions = useRef<Set<() => void>>(new Set());

  const addCleanup = useCallback((cleanup: () => void) => {
    cleanupFunctions.current.add(cleanup);
    return () => {
      cleanupFunctions.current.delete(cleanup);
    };
  }, []);

  useEffect(() => {
    return () => {
      // Execute all cleanup functions
      cleanupFunctions.current.forEach((cleanup) => {
        try {
          cleanup();
        } catch (error) {
          console.error("Cleanup function error:", error);
        }
      });
      cleanupFunctions.current.clear();
    };
  }, []);

  return { addCleanup };
}
