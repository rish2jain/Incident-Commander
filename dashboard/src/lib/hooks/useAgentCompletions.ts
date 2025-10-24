/**
 * useAgentCompletions Hook
 * React hook for managing agent completion animations and feedback
 * Requirements: 3.2 - Show completion animations and success indicators when agents finish tasks
 */

import { useState, useEffect, useCallback } from "react";
import {
  AgentCompletionManager,
  AgentCompletionEvent,
  AgentType,
  agentCompletionManager,
} from "../agent-completion-manager";
import { AgentAction } from "../../types";

export interface UseAgentCompletionsReturn {
  recentCompletions: AgentCompletionEvent[];
  completionStats: {
    totalCompletions: number;
    successRate: number;
    averageCompletionTime: number;
    agentPerformance: Record<
      AgentType,
      { completions: number; successRate: number; avgTime: number }
    >;
  };
  registerCompletion: (
    agentType: AgentType,
    action: AgentAction,
    completionTime: number,
    success?: boolean
  ) => void;
  clearHistory: () => void;
  isShowingCompletion: boolean;
  lastCompletion: AgentCompletionEvent | null;
}

export function useAgentCompletions(
  manager: AgentCompletionManager = agentCompletionManager,
  maxRecentCompletions: number = 10
): UseAgentCompletionsReturn {
  const [recentCompletions, setRecentCompletions] = useState<
    AgentCompletionEvent[]
  >(manager.getRecentCompletions(maxRecentCompletions));
  const [completionStats, setCompletionStats] = useState(
    manager.getCompletionStats()
  );
  const [isShowingCompletion, setIsShowingCompletion] = useState(false);
  const [lastCompletion, setLastCompletion] =
    useState<AgentCompletionEvent | null>(null);

  // Subscribe to completion events
  useEffect(() => {
    const unsubscribe = manager.onCompletion((event: AgentCompletionEvent) => {
      setRecentCompletions(manager.getRecentCompletions(maxRecentCompletions));
      setCompletionStats(manager.getCompletionStats());
      setLastCompletion(event);

      // Show completion animation
      setIsShowingCompletion(true);

      // Hide completion animation after celebration duration
      const config = manager.getConfig();
      const timer = setTimeout(() => {
        setIsShowingCompletion(false);
      }, config.celebrationDuration);

      return () => clearTimeout(timer);
    });

    return unsubscribe;
  }, [manager, maxRecentCompletions]);

  const registerCompletion = useCallback(
    (
      agentType: AgentType,
      action: AgentAction,
      completionTime: number,
      success: boolean = true
    ) => {
      manager.registerCompletion(agentType, action, completionTime, success);
    },
    [manager]
  );

  const clearHistory = useCallback(() => {
    manager.clearHistory();
    setRecentCompletions([]);
    setCompletionStats(manager.getCompletionStats());
    setLastCompletion(null);
    setIsShowingCompletion(false);
  }, [manager]);

  return {
    recentCompletions,
    completionStats,
    registerCompletion,
    clearHistory,
    isShowingCompletion,
    lastCompletion,
  };
}
