/**
 * Fallback Handlers - Comprehensive fallback mechanisms for dashboard features
 *
 * Features:
 * - Auto-scroll fallback when manager fails
 * - Connection fallback when WebSocket fails
 * - Incident tracking fallback when tracker fails
 * - Performance fallback when system is overloaded
 * - Data fallback when real-time updates fail
 */

import React, { useEffect, useCallback } from "react";
import { AgentAction, Incident, MetricData } from "../types";

export interface FallbackConfig {
  enableAutoScroll: boolean;
  enableConnectionFallback: boolean;
  enableIncidentTracking: boolean;
  enablePerformanceOptimization: boolean;
  enableDataFallback: boolean;
  maxRetries: number;
  retryDelay: number;
}

export interface FallbackState {
  autoScrollFailed: boolean;
  connectionFailed: boolean;
  incidentTrackingFailed: boolean;
  performanceIssues: boolean;
  dataFallbackActive: boolean;
  lastError: Error | null;
  retryCount: number;
}

export class FallbackManager {
  private config: FallbackConfig;
  private state: FallbackState;
  private observers: Set<(state: FallbackState) => void> = new Set();
  private retryTimers: Map<string, NodeJS.Timeout> = new Map();

  constructor(config: Partial<FallbackConfig> = {}) {
    this.config = {
      enableAutoScroll: true,
      enableConnectionFallback: true,
      enableIncidentTracking: true,
      enablePerformanceOptimization: true,
      enableDataFallback: true,
      maxRetries: 3,
      retryDelay: 1000,
      ...config,
    };

    this.state = {
      autoScrollFailed: false,
      connectionFailed: false,
      incidentTrackingFailed: false,
      performanceIssues: false,
      dataFallbackActive: false,
      lastError: null,
      retryCount: 0,
    };
  }

  /**
   * Auto-scroll fallback - Basic scroll to bottom when AutoScrollManager fails
   */
  public handleAutoScrollFallback(container: HTMLElement | null): boolean {
    if (!this.config.enableAutoScroll || !container) return false;

    try {
      // Simple scroll to bottom
      container.scrollTop = container.scrollHeight;

      // Reset failure state if successful
      if (this.state.autoScrollFailed) {
        this.updateState({ autoScrollFailed: false });
      }

      return true;
    } catch (error) {
      console.error("Auto-scroll fallback failed:", error);
      this.updateState({
        autoScrollFailed: true,
        lastError: error as Error,
      });
      return false;
    }
  }

  /**
   * Connection fallback - Polling mode when WebSocket fails
   */
  public async handleConnectionFallback(
    apiEndpoint: string,
    onData: (data: any) => void
  ): Promise<void> {
    if (!this.config.enableConnectionFallback) return;

    const pollData = async () => {
      try {
        const response = await fetch(apiEndpoint);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        onData(data);

        // Reset failure state if successful
        if (this.state.connectionFailed) {
          this.updateState({ connectionFailed: false });
        }
      } catch (error) {
        console.error("Connection fallback polling failed:", error);
        this.updateState({
          connectionFailed: true,
          lastError: error as Error,
        });
      }
    };

    // Start polling every 5 seconds
    const pollInterval = setInterval(pollData, 5000);

    // Initial poll
    await pollData();

    // Store interval for cleanup
    this.retryTimers.set("connection-fallback", pollInterval);
  }

  /**
   * Incident tracking fallback - Local state management when tracker fails
   */
  public handleIncidentTrackingFallback(): {
    startIncident: (incident: any) => void;
    updateIncident: (update: any) => void;
    resolveIncident: () => void;
    getCurrentIncident: () => any;
  } {
    let localIncident: any = null;

    return {
      startIncident: (incident: any) => {
        try {
          localIncident = {
            ...incident,
            startTime: new Date(),
            progress: 0,
            phase: "detection",
          };

          console.log("Fallback: Started incident tracking locally");

          // Reset failure state
          if (this.state.incidentTrackingFailed) {
            this.updateState({ incidentTrackingFailed: false });
          }
        } catch (error) {
          console.error("Incident tracking fallback failed:", error);
          this.updateState({
            incidentTrackingFailed: true,
            lastError: error as Error,
          });
        }
      },

      updateIncident: (update: any) => {
        try {
          if (localIncident) {
            localIncident = { ...localIncident, ...update };
            console.log("Fallback: Updated incident locally");
          }
        } catch (error) {
          console.error("Incident update fallback failed:", error);
        }
      },

      resolveIncident: () => {
        try {
          if (localIncident) {
            const resolutionTime = Math.floor(
              (Date.now() - localIncident.startTime.getTime()) / 1000
            );
            localIncident = {
              ...localIncident,
              isComplete: true,
              resolutionTime,
              phase: "resolved",
            };
            console.log("Fallback: Resolved incident locally");
          }
        } catch (error) {
          console.error("Incident resolution fallback failed:", error);
        }
      },

      getCurrentIncident: () => localIncident,
    };
  }

  /**
   * Performance fallback - Reduce features when performance issues detected
   */
  public handlePerformanceFallback(): {
    shouldDisableAnimations: boolean;
    shouldReduceUpdates: boolean;
    shouldLimitMessages: boolean;
    getOptimizedConfig: () => any;
  } {
    const performanceIssues = this.detectPerformanceIssues();

    if (performanceIssues && !this.state.performanceIssues) {
      this.updateState({ performanceIssues: true });
      console.warn("Performance issues detected, enabling fallback mode");
    }

    return {
      shouldDisableAnimations: performanceIssues,
      shouldReduceUpdates: performanceIssues,
      shouldLimitMessages: performanceIssues,
      getOptimizedConfig: () => ({
        autoScroll: {
          smoothScroll: !performanceIssues,
          debounceDelay: performanceIssues ? 200 : 100,
          maxScrollSpeed: performanceIssues ? 1 : 2,
        },
        updates: {
          interval: performanceIssues ? 2000 : 1000,
          batchSize: performanceIssues ? 5 : 10,
        },
        animations: {
          enabled: !performanceIssues,
          duration: performanceIssues ? 0 : 300,
        },
      }),
    };
  }

  /**
   * Data fallback - Mock data when real-time updates fail
   */
  public handleDataFallback(): {
    getMockAgentActions: () => AgentAction[];
    getMockIncident: () => Incident;
    getMockMetrics: () => MetricData[];
  } {
    if (!this.state.dataFallbackActive) {
      this.updateState({ dataFallbackActive: true });
      console.warn("Data fallback activated - using mock data");
    }

    return {
      getMockAgentActions: () => [
        {
          id: "fallback-1",
          agent_type: "detection",
          title: "System Monitoring (Fallback Mode)",
          description:
            "Dashboard running in fallback mode with limited connectivity",
          timestamp: new Date().toISOString(),
          confidence: 0.8,
          status: "completed",
          duration: 1000,
          impact: "Reduced functionality",
        },
      ],

      getMockIncident: () => ({
        id: "fallback-incident",
        title: "Connection Issues Detected",
        description:
          "Dashboard experiencing connectivity issues, running in fallback mode",
        severity: "medium",
        status: "active",
        created_at: new Date().toISOString(),
        affected_services: ["dashboard", "websocket"],
        metrics: {},
        estimated_cost: 0,
      }),

      getMockMetrics: () =>
        [
          {
            id: "fallback-status",
            label: "System Status",
            value: "Fallback Mode",
            icon: () => null,
            color: "text-yellow-600",
            bgColor: "bg-yellow-50",
            borderColor: "border-yellow-200",
            description: "Dashboard running with limited features",
          },
        ] as MetricData[],
    };
  }

  /**
   * Retry failed operations
   */
  public async retryOperation(
    operationName: string,
    operation: () => Promise<void>
  ): Promise<boolean> {
    if (this.state.retryCount >= this.config.maxRetries) {
      console.error(`Max retries exceeded for ${operationName}`);
      return false;
    }

    try {
      await operation();
      this.updateState({ retryCount: 0, lastError: null });
      console.log(`Retry successful for ${operationName}`);
      return true;
    } catch (error) {
      const newRetryCount = this.state.retryCount + 1;
      this.updateState({
        retryCount: newRetryCount,
        lastError: error as Error,
      });

      if (newRetryCount < this.config.maxRetries) {
        // Schedule retry with exponential backoff
        const delay = this.config.retryDelay * Math.pow(2, newRetryCount - 1);

        const timer = setTimeout(() => {
          this.retryOperation(operationName, operation);
        }, delay);

        this.retryTimers.set(`retry-${operationName}`, timer);
      }

      return false;
    }
  }

  /**
   * Get current fallback state
   */
  public getState(): FallbackState {
    return { ...this.state };
  }

  /**
   * Add observer for state changes
   */
  public addObserver(callback: (state: FallbackState) => void): () => void {
    this.observers.add(callback);
    return () => this.observers.delete(callback);
  }

  /**
   * Clean up resources
   */
  public destroy(): void {
    // Clear all timers
    this.retryTimers.forEach((timer) => clearTimeout(timer));
    this.retryTimers.clear();

    // Clear observers
    this.observers.clear();
  }

  // Private methods

  private detectPerformanceIssues(): boolean {
    // Simple performance detection based on frame rate and memory
    const now = performance.now();

    // Check if we have performance API
    if (!window.performance || !(window.performance as any).memory) {
      return false;
    }

    // Check memory usage (if available)
    const memory = (window.performance as any).memory;
    if (memory) {
      const memoryUsage = memory.usedJSHeapSize / memory.totalJSHeapSize;
      if (memoryUsage > 0.8) {
        return true;
      }
    }

    // Check for long tasks (simplified)
    const entries = performance.getEntriesByType("measure");
    const recentEntries = entries.filter(
      (entry) => now - entry.startTime < 5000
    );

    const hasLongTasks = recentEntries.some((entry) => entry.duration > 50);

    return hasLongTasks;
  }

  private updateState(updates: Partial<FallbackState>): void {
    this.state = { ...this.state, ...updates };
    this.notifyObservers();
  }

  private notifyObservers(): void {
    this.observers.forEach((callback) => {
      try {
        callback(this.getState());
      } catch (error) {
        console.error("Error in fallback observer:", error);
      }
    });
  }
}

// Export singleton instance
export const globalFallbackManager = new FallbackManager();

/**
 * React hook for using fallback functionality
 */
export function useFallbackManager(config?: Partial<FallbackConfig>) {
  const [manager] = React.useState(() =>
    config ? new FallbackManager(config) : globalFallbackManager
  );
  const [state, setState] = React.useState(manager.getState());

  React.useEffect(() => {
    const unsubscribe = manager.addObserver(setState);
    return unsubscribe;
  }, [manager]);

  React.useEffect(() => {
    return () => {
      if (config) {
        // Only destroy if we created a new manager
        manager.destroy();
      }
    };
  }, [manager, config]);

  return {
    state,
    handleAutoScrollFallback: manager.handleAutoScrollFallback.bind(manager),
    handleConnectionFallback: manager.handleConnectionFallback.bind(manager),
    handleIncidentTrackingFallback:
      manager.handleIncidentTrackingFallback.bind(manager),
    handlePerformanceFallback: manager.handlePerformanceFallback.bind(manager),
    handleDataFallback: manager.handleDataFallback.bind(manager),
    retryOperation: manager.retryOperation.bind(manager),
  };
}
