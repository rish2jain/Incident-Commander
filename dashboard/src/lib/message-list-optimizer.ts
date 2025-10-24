import { useCallback, useEffect, useMemo, useRef, useState } from "react";

/**
 * Message list performance optimization utilities
 * Handles 100+ messages per second without performance degradation
 * Implements message pruning for long-running sessions
 */

export interface MessageListConfig {
  maxMessages: number;
  pruneThreshold: number;
  batchSize: number;
  updateInterval: number;
  enablePruning: boolean;
  enableBatching: boolean;
  performanceMode: "normal" | "high-frequency" | "ultra-performance";
}

export const DEFAULT_MESSAGE_CONFIG: MessageListConfig = {
  maxMessages: 1000,
  pruneThreshold: 1500,
  batchSize: 10,
  updateInterval: 100, // ms
  enablePruning: true,
  enableBatching: true,
  performanceMode: "normal",
};

export const HIGH_FREQUENCY_CONFIG: MessageListConfig = {
  maxMessages: 500,
  pruneThreshold: 750,
  batchSize: 25,
  updateInterval: 50,
  enablePruning: true,
  enableBatching: true,
  performanceMode: "high-frequency",
};

export const ULTRA_PERFORMANCE_CONFIG: MessageListConfig = {
  maxMessages: 200,
  pruneThreshold: 300,
  batchSize: 50,
  updateInterval: 25,
  enablePruning: true,
  enableBatching: true,
  performanceMode: "ultra-performance",
};

export interface MessageItem {
  id: string;
  timestamp: string;
  priority?: "low" | "medium" | "high" | "critical";
  size?: number; // Estimated memory size
  [key: string]: any;
}

export interface MessageBatch<T extends MessageItem> {
  messages: T[];
  timestamp: number;
  batchId: string;
}

export interface PerformanceMetrics {
  messagesPerSecond: number;
  averageProcessingTime: number;
  memoryUsage: number;
  droppedMessages: number;
  batchesProcessed: number;
  pruningEvents: number;
}

/**
 * High-performance message list manager
 */
export class MessageListOptimizer<T extends MessageItem> {
  private messages: T[] = [];
  private pendingBatches: MessageBatch<T>[] = [];
  private config: MessageListConfig;
  private metrics: PerformanceMetrics = {
    messagesPerSecond: 0,
    averageProcessingTime: 0,
    memoryUsage: 0,
    droppedMessages: 0,
    batchesProcessed: 0,
    pruningEvents: 0,
  };

  private messageCountHistory: number[] = [];
  private processingTimes: number[] = [];
  private lastPruneTime = 0;
  private batchTimer: NodeJS.Timeout | null = null;
  private metricsTimer: NodeJS.Timeout | null = null;

  constructor(config: Partial<MessageListConfig> = {}) {
    this.config = { ...DEFAULT_MESSAGE_CONFIG, ...config };
    this.startMetricsCollection();
  }

  /**
   * Add messages with automatic batching and performance optimization
   */
  addMessages(newMessages: T[]): void {
    const startTime = performance.now();

    if (this.config.enableBatching && newMessages.length > 1) {
      this.addToBatch(newMessages);
    } else {
      this.processMessages(newMessages);
    }

    // Track processing time
    const processingTime = performance.now() - startTime;
    this.processingTimes.push(processingTime);
    if (this.processingTimes.length > 100) {
      this.processingTimes.shift();
    }
  }

  /**
   * Add single message with immediate processing
   */
  addMessage(message: T): void {
    this.addMessages([message]);
  }

  /**
   * Get current messages with optional filtering
   */
  getMessages(filter?: (message: T) => boolean): T[] {
    if (filter) {
      return this.messages.filter(filter);
    }
    return [...this.messages];
  }

  /**
   * Get messages in chunks for virtualization
   */
  getMessageChunk(startIndex: number, count: number): T[] {
    return this.messages.slice(startIndex, startIndex + count);
  }

  /**
   * Get performance metrics
   */
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Clear all messages and reset state
   */
  clear(): void {
    this.messages = [];
    this.pendingBatches = [];
    this.messageCountHistory = [];
    this.processingTimes = [];
    this.metrics.droppedMessages = 0;
    this.metrics.batchesProcessed = 0;
    this.metrics.pruningEvents = 0;
  }

  /**
   * Update configuration and adapt performance mode
   */
  updateConfig(newConfig: Partial<MessageListConfig>): void {
    this.config = { ...this.config, ...newConfig };

    // Adapt to performance mode
    if (this.config.performanceMode === "high-frequency") {
      this.config = { ...this.config, ...HIGH_FREQUENCY_CONFIG, ...newConfig };
    } else if (this.config.performanceMode === "ultra-performance") {
      this.config = {
        ...this.config,
        ...ULTRA_PERFORMANCE_CONFIG,
        ...newConfig,
      };
    }

    // Trigger immediate pruning if needed
    if (this.messages.length > this.config.maxMessages) {
      this.pruneMessages();
    }
  }

  /**
   * Destroy optimizer and cleanup resources
   */
  destroy(): void {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
    }
    if (this.metricsTimer) {
      clearInterval(this.metricsTimer);
    }
    this.clear();
  }

  private addToBatch(messages: T[]): void {
    const batch: MessageBatch<T> = {
      messages,
      timestamp: Date.now(),
      batchId: `batch-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };

    this.pendingBatches.push(batch);

    // Process batch immediately if it's large enough or after timeout
    if (this.pendingBatches.length >= this.config.batchSize) {
      this.processPendingBatches();
    } else if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => {
        this.processPendingBatches();
      }, this.config.updateInterval);
    }
  }

  private processPendingBatches(): void {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    const allMessages = this.pendingBatches.flatMap((batch) => batch.messages);
    this.pendingBatches = [];

    if (allMessages.length > 0) {
      this.processMessages(allMessages);
      this.metrics.batchesProcessed++;
    }
  }

  private processMessages(newMessages: T[]): void {
    // Sort messages by timestamp for consistent ordering
    const sortedMessages = [...newMessages].sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // Add messages to the list
    this.messages.unshift(...sortedMessages);

    // Check if pruning is needed
    if (this.config.enablePruning && this.shouldPrune()) {
      this.pruneMessages();
    }

    // Update message count history for metrics
    this.messageCountHistory.push(this.messages.length);
    if (this.messageCountHistory.length > 60) {
      // Keep last 60 measurements
      this.messageCountHistory.shift();
    }
  }

  private shouldPrune(): boolean {
    const now = Date.now();
    const timeSinceLastPrune = now - this.lastPruneTime;

    return (
      this.messages.length > this.config.pruneThreshold ||
      (this.messages.length > this.config.maxMessages &&
        timeSinceLastPrune > 5000) // 5 seconds
    );
  }

  private pruneMessages(): void {
    const startTime = performance.now();
    const originalLength = this.messages.length;

    if (this.messages.length <= this.config.maxMessages) {
      return;
    }

    // Strategy 1: Remove oldest messages first, but keep high priority ones
    const priorityMessages = this.messages.filter(
      (msg) => msg.priority === "critical" || msg.priority === "high"
    );

    const normalMessages = this.messages.filter(
      (msg) => msg.priority !== "critical" && msg.priority !== "high"
    );

    // Keep all priority messages and trim normal messages
    const maxNormalMessages = Math.max(
      0,
      this.config.maxMessages - priorityMessages.length
    );

    const prunedNormalMessages = normalMessages.slice(0, maxNormalMessages);
    this.messages = [...priorityMessages, ...prunedNormalMessages];

    // Sort by timestamp again
    this.messages.sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    const pruned = originalLength - this.messages.length;
    this.metrics.droppedMessages += pruned;
    this.metrics.pruningEvents++;
    this.lastPruneTime = Date.now();

    const pruningTime = performance.now() - startTime;
    console.log(`Pruned ${pruned} messages in ${pruningTime.toFixed(2)}ms`);
  }

  private startMetricsCollection(): void {
    this.metricsTimer = setInterval(() => {
      this.updateMetrics();
    }, 1000); // Update metrics every second
  }

  private updateMetrics(): void {
    // Calculate messages per second
    if (this.messageCountHistory.length >= 2) {
      const currentCount =
        this.messageCountHistory[this.messageCountHistory.length - 1];
      const previousCount =
        this.messageCountHistory[this.messageCountHistory.length - 2];
      this.metrics.messagesPerSecond = Math.max(
        0,
        currentCount - previousCount
      );
    }

    // Calculate average processing time
    if (this.processingTimes.length > 0) {
      this.metrics.averageProcessingTime =
        this.processingTimes.reduce((a, b) => a + b, 0) /
        this.processingTimes.length;
    }

    // Estimate memory usage (rough calculation)
    this.metrics.memoryUsage = this.messages.reduce((total, msg) => {
      return total + (msg.size || this.estimateMessageSize(msg));
    }, 0);
  }

  private estimateMessageSize(message: T): number {
    // Rough estimation of message size in bytes
    const jsonString = JSON.stringify(message);
    return jsonString.length * 2; // Approximate UTF-16 encoding
  }
}

/**
 * React hook for optimized message list management
 */
export function useOptimizedMessageList<T extends MessageItem>(
  initialMessages: T[] = [],
  config: Partial<MessageListConfig> = {}
) {
  const optimizerRef = useRef<MessageListOptimizer<T>>();
  const [messages, setMessages] = useState<T[]>(initialMessages);
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    messagesPerSecond: 0,
    averageProcessingTime: 0,
    memoryUsage: 0,
    droppedMessages: 0,
    batchesProcessed: 0,
    pruningEvents: 0,
  });

  // Initialize optimizer
  useEffect(() => {
    optimizerRef.current = new MessageListOptimizer<T>(config);

    if (initialMessages.length > 0) {
      optimizerRef.current.addMessages(initialMessages);
      setMessages(optimizerRef.current.getMessages());
    }

    return () => {
      optimizerRef.current?.destroy();
    };
  }, []);

  // Update metrics periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (optimizerRef.current) {
        setMetrics(optimizerRef.current.getMetrics());
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const addMessages = useCallback((newMessages: T[]) => {
    if (optimizerRef.current) {
      optimizerRef.current.addMessages(newMessages);
      setMessages(optimizerRef.current.getMessages());
    }
  }, []);

  const addMessage = useCallback(
    (message: T) => {
      addMessages([message]);
    },
    [addMessages]
  );

  const getMessageChunk = useCallback((startIndex: number, count: number) => {
    return optimizerRef.current?.getMessageChunk(startIndex, count) || [];
  }, []);

  const clearMessages = useCallback(() => {
    if (optimizerRef.current) {
      optimizerRef.current.clear();
      setMessages([]);
    }
  }, []);

  const updateConfig = useCallback((newConfig: Partial<MessageListConfig>) => {
    if (optimizerRef.current) {
      optimizerRef.current.updateConfig(newConfig);
    }
  }, []);

  // Auto-adapt performance mode based on message frequency
  useEffect(() => {
    if (metrics.messagesPerSecond > 100) {
      updateConfig({ performanceMode: "ultra-performance" });
    } else if (metrics.messagesPerSecond > 50) {
      updateConfig({ performanceMode: "high-frequency" });
    } else if (metrics.messagesPerSecond < 10) {
      updateConfig({ performanceMode: "normal" });
    }
  }, [metrics.messagesPerSecond, updateConfig]);

  return {
    messages,
    metrics,
    addMessage,
    addMessages,
    getMessageChunk,
    clearMessages,
    updateConfig,
    totalCount: messages.length,
    isHighFrequency: metrics.messagesPerSecond > 50,
    isUltraPerformance: metrics.messagesPerSecond > 100,
  };
}

/**
 * Hook for message list virtualization with performance optimization
 */
export function useVirtualizedMessageList<T extends MessageItem>(
  messages: T[],
  containerHeight: number,
  itemHeight: number,
  overscan: number = 5
) {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleRange = useMemo(() => {
    const visibleStart = Math.floor(scrollTop / itemHeight);
    const visibleEnd = Math.min(
      visibleStart + Math.ceil(containerHeight / itemHeight),
      messages.length
    );

    return {
      start: Math.max(0, visibleStart - overscan),
      end: Math.min(messages.length, visibleEnd + overscan),
    };
  }, [scrollTop, itemHeight, containerHeight, messages.length, overscan]);

  const visibleMessages = useMemo(() => {
    return messages.slice(visibleRange.start, visibleRange.end);
  }, [messages, visibleRange.start, visibleRange.end]);

  const totalHeight = messages.length * itemHeight;
  const offsetY = visibleRange.start * itemHeight;

  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);

  return {
    visibleMessages,
    visibleRange,
    totalHeight,
    offsetY,
    handleScroll,
    isVirtualized: messages.length > 50, // Virtualize for large lists
  };
}

/**
 * Performance monitoring hook for message lists
 */
export function useMessageListPerformance() {
  const [performanceData, setPerformanceData] = useState({
    renderTime: 0,
    memoryUsage: 0,
    fps: 60,
    isOptimal: true,
  });

  const measureRenderTime = useCallback((renderFn: () => void) => {
    const start = performance.now();
    renderFn();
    const end = performance.now();
    const renderTime = end - start;

    setPerformanceData((prev) => ({
      ...prev,
      renderTime,
      isOptimal: renderTime < 16, // 60fps threshold
    }));
  }, []);

  useEffect(() => {
    // Monitor memory usage if available
    const interval = setInterval(() => {
      if ("memory" in performance) {
        const memory = (performance as any).memory;
        setPerformanceData((prev) => ({
          ...prev,
          memoryUsage: memory.usedJSHeapSize,
        }));
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return {
    performanceData,
    measureRenderTime,
  };
}
