/**
 * useConflictResolution Hook
 * React hook for managing conflict resolution and consensus visualization
 * Requirements: 3.4 - Highlight consensus resolution processes when agents disagree
 */

import { useState, useEffect, useCallback } from "react";
import {
  ConflictResolutionManager,
  ConflictResolution,
  AgentRecommendation,
  ConflictMetrics,
  conflictResolutionManager,
} from "../conflict-resolution-manager";

export interface UseConflictResolutionReturn {
  recentConflicts: ConflictResolution[];
  activeConflicts: ConflictResolution[];
  metrics: ConflictMetrics;
  registerConflict: (
    recommendations: AgentRecommendation[],
    conflictType?: ConflictResolution["conflictType"]
  ) => ConflictResolution;
  manuallyResolve: (
    conflictId: string,
    selectedRecommendation: AgentRecommendation
  ) => void;
  clearHistory: () => void;
  hasActiveConflicts: boolean;
  lastConflict: ConflictResolution | null;
  lastResolution: ConflictResolution | null;
}

export function useConflictResolution(
  manager: ConflictResolutionManager = conflictResolutionManager,
  maxRecentConflicts: number = 10
): UseConflictResolutionReturn {
  const [recentConflicts, setRecentConflicts] = useState<ConflictResolution[]>(
    manager.getRecentConflicts(maxRecentConflicts)
  );
  const [activeConflicts, setActiveConflicts] = useState<ConflictResolution[]>(
    manager.getActiveConflicts()
  );
  const [metrics, setMetrics] = useState<ConflictMetrics>(manager.getMetrics());
  const [lastConflict, setLastConflict] = useState<ConflictResolution | null>(
    null
  );
  const [lastResolution, setLastResolution] =
    useState<ConflictResolution | null>(null);

  // Subscribe to conflict events
  useEffect(() => {
    const unsubscribeConflict = manager.onConflict(
      (conflict: ConflictResolution) => {
        setRecentConflicts(manager.getRecentConflicts(maxRecentConflicts));
        setActiveConflicts(manager.getActiveConflicts());
        setMetrics(manager.getMetrics());
        setLastConflict(conflict);
      }
    );

    const unsubscribeResolution = manager.onResolution(
      (resolution: ConflictResolution) => {
        setRecentConflicts(manager.getRecentConflicts(maxRecentConflicts));
        setActiveConflicts(manager.getActiveConflicts());
        setMetrics(manager.getMetrics());
        setLastResolution(resolution);
      }
    );

    return () => {
      unsubscribeConflict();
      unsubscribeResolution();
    };
  }, [manager, maxRecentConflicts]);

  const registerConflict = useCallback(
    (
      recommendations: AgentRecommendation[],
      conflictType?: ConflictResolution["conflictType"]
    ) => {
      return manager.registerConflict(recommendations, conflictType);
    },
    [manager]
  );

  const manuallyResolve = useCallback(
    (conflictId: string, selectedRecommendation: AgentRecommendation) => {
      manager.manuallyResolve(conflictId, selectedRecommendation);
    },
    [manager]
  );

  const clearHistory = useCallback(() => {
    manager.clearHistory();
    setRecentConflicts([]);
    setActiveConflicts([]);
    setMetrics(manager.getMetrics());
    setLastConflict(null);
    setLastResolution(null);
  }, [manager]);

  return {
    recentConflicts,
    activeConflicts,
    metrics,
    registerConflict,
    manuallyResolve,
    clearHistory,
    hasActiveConflicts: activeConflicts.length > 0,
    lastConflict,
    lastResolution,
  };
}
