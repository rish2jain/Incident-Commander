/**
 * Agent Completion Manager
 * Handles visual feedback for agent task completion
 * Requirements: 3.2 - Show completion animations and success indicators when agents finish tasks
 */

import { AgentAction } from "../types";

export type AgentType =
  | "detection"
  | "diagnosis"
  | "prediction"
  | "resolution"
  | "communication";

export interface AgentCompletionEvent {
  agentType: AgentType;
  action: AgentAction;
  timestamp: Date;
  completionTime: number; // Duration in milliseconds
  success: boolean;
  confidence?: number;
}

export interface AgentCompletionConfig {
  showSuccessAnimation: boolean;
  showConfidenceIndicator: boolean;
  celebrationDuration: number;
  fadeOutDelay: number;
  soundEnabled: boolean;
}

export const AGENT_CONFIGS = {
  detection: {
    name: "Detection Agent",
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/30",
    successColor: "text-orange-500",
    icon: "AlertTriangle",
    description: "Anomaly detection and incident identification",
  },
  diagnosis: {
    name: "Diagnosis Agent",
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    successColor: "text-blue-500",
    icon: "Activity",
    description: "Root cause analysis and impact assessment",
  },
  prediction: {
    name: "Prediction Agent",
    color: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    successColor: "text-purple-500",
    icon: "TrendingUp",
    description: "Incident escalation forecasting",
  },
  resolution: {
    name: "Resolution Agent",
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    successColor: "text-red-500",
    icon: "Shield",
    description: "Automated remediation execution",
  },
  communication: {
    name: "Communication Agent",
    color: "text-indigo-600 dark:text-indigo-400",
    bgColor: "bg-indigo-500/10",
    borderColor: "border-indigo-500/30",
    successColor: "text-indigo-500",
    icon: "Users",
    description: "Stakeholder notification and updates",
  },
};

export class AgentCompletionManager {
  private completionEvents: AgentCompletionEvent[] = [];
  private completionCallbacks: Array<(event: AgentCompletionEvent) => void> =
    [];
  private config: AgentCompletionConfig;

  constructor(config: Partial<AgentCompletionConfig> = {}) {
    this.config = {
      showSuccessAnimation: true,
      showConfidenceIndicator: true,
      celebrationDuration: 2000,
      fadeOutDelay: 3000,
      soundEnabled: false,
      ...config,
    };
  }

  /**
   * Register an agent completion event
   */
  public registerCompletion(
    agentType: AgentType,
    action: AgentAction,
    completionTime: number,
    success: boolean = true
  ): AgentCompletionEvent {
    const event: AgentCompletionEvent = {
      agentType,
      action,
      timestamp: new Date(),
      completionTime,
      success,
      confidence: action.confidence,
    };

    this.completionEvents.push(event);

    // Notify callbacks
    this.completionCallbacks.forEach((callback) => callback(event));

    return event;
  }

  /**
   * Subscribe to completion events
   */
  public onCompletion(
    callback: (event: AgentCompletionEvent) => void
  ): () => void {
    this.completionCallbacks.push(callback);

    return () => {
      const index = this.completionCallbacks.indexOf(callback);
      if (index > -1) {
        this.completionCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Get recent completion events
   */
  public getRecentCompletions(limit: number = 10): AgentCompletionEvent[] {
    return this.completionEvents
      .slice(-limit)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Get completion statistics
   */
  public getCompletionStats(): {
    totalCompletions: number;
    successRate: number;
    averageCompletionTime: number;
    agentPerformance: Record<
      AgentType,
      { completions: number; successRate: number; avgTime: number }
    >;
  } {
    const total = this.completionEvents.length;
    const successful = this.completionEvents.filter((e) => e.success).length;
    const avgTime =
      total > 0
        ? this.completionEvents.reduce((sum, e) => sum + e.completionTime, 0) /
          total
        : 0;

    const agentPerformance: Record<
      string,
      { completions: number; successRate: number; avgTime: number }
    > = {};

    Object.keys(AGENT_CONFIGS).forEach((agentType) => {
      const agentEvents = this.completionEvents.filter(
        (e) => e.agentType === agentType
      );
      const agentSuccessful = agentEvents.filter((e) => e.success).length;
      const agentAvgTime =
        agentEvents.length > 0
          ? agentEvents.reduce((sum, e) => sum + e.completionTime, 0) /
            agentEvents.length
          : 0;

      agentPerformance[agentType] = {
        completions: agentEvents.length,
        successRate:
          agentEvents.length > 0 ? agentSuccessful / agentEvents.length : 0,
        avgTime: agentAvgTime,
      };
    });

    return {
      totalCompletions: total,
      successRate: total > 0 ? successful / total : 0,
      averageCompletionTime: avgTime,
      agentPerformance: agentPerformance as Record<
        AgentType,
        { completions: number; successRate: number; avgTime: number }
      >,
    };
  }

  /**
   * Clear completion history
   */
  public clearHistory(): void {
    this.completionEvents = [];
  }

  /**
   * Update configuration
   */
  public updateConfig(newConfig: Partial<AgentCompletionConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  public getConfig(): AgentCompletionConfig {
    return { ...this.config };
  }

  /**
   * Calculate confidence level description
   */
  public getConfidenceLevel(confidence?: number): {
    level: "low" | "medium" | "high" | "very_high";
    description: string;
    color: string;
  } {
    if (!confidence) {
      return {
        level: "medium",
        description: "Standard confidence",
        color: "text-gray-500",
      };
    }

    if (confidence >= 0.9) {
      return {
        level: "very_high",
        description: "Very high confidence",
        color: "text-green-600",
      };
    } else if (confidence >= 0.75) {
      return {
        level: "high",
        description: "High confidence",
        color: "text-blue-600",
      };
    } else if (confidence >= 0.6) {
      return {
        level: "medium",
        description: "Medium confidence",
        color: "text-yellow-600",
      };
    } else {
      return {
        level: "low",
        description: "Low confidence",
        color: "text-red-600",
      };
    }
  }

  /**
   * Format completion time for display
   */
  public formatCompletionTime(milliseconds: number): string {
    if (milliseconds < 1000) {
      return `${milliseconds}ms`;
    } else if (milliseconds < 60000) {
      return `${(milliseconds / 1000).toFixed(1)}s`;
    } else {
      const minutes = Math.floor(milliseconds / 60000);
      const seconds = Math.floor((milliseconds % 60000) / 1000);
      return `${minutes}m ${seconds}s`;
    }
  }
}

// Create singleton instance
export const agentCompletionManager = new AgentCompletionManager();
