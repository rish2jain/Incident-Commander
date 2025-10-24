/**
 * useIncidentStatus - React hook for integrating IncidentStatusTracker with components
 *
 * Features:
 * - Automatic lifecycle management
 * - State synchronization with React
 * - Real-time progress updates
 * - Resolution notifications
 * - Phase transition handling
 */

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import {
  IncidentStatusTracker,
  IncidentStatus,
  IncidentResolution,
  StatusTransition,
  globalIncidentTracker,
} from "../incident-status-tracker";

export interface UseIncidentStatusOptions {
  tracker?: IncidentStatusTracker;
  autoUpdate?: boolean;
  updateInterval?: number;
  enableNotifications?: boolean;
}

export interface UseIncidentStatusReturn {
  // Current state
  currentIncident: IncidentStatus | null;
  isActive: boolean;
  isResolved: boolean;
  progress: number;
  currentPhase: string | null;
  estimatedCompletion: Date | null;
  resolutionTime: number | null;

  // History and transitions
  statusHistory: StatusTransition[];
  lastTransition: StatusTransition | null;

  // Phase information
  phaseProgress: Record<string, number>;
  completedPhases: string[];
  remainingPhases: string[];

  // Actions
  startIncident: (incident: Partial<IncidentStatus>) => void;
  updateStatus: (update: Partial<IncidentStatus>) => void;
  markResolved: (resolutionTime?: number) => void;
  clearIncident: () => void;

  // Event handlers
  onResolution: (
    callback: (resolution: IncidentResolution) => void
  ) => () => void;
  onPhaseTransition: (
    callback: (transition: StatusTransition) => void
  ) => () => void;
  onStatusUpdate: (callback: (status: IncidentStatus) => void) => () => void;

  // Utilities
  getPhaseConfig: () => any;
  formatDuration: (seconds: number) => string;
  getBusinessImpact: () => any;
}

/**
 * Main hook for incident status management
 */
export function useIncidentStatus(
  options: UseIncidentStatusOptions = {}
): UseIncidentStatusReturn {
  const {
    tracker = globalIncidentTracker,
    autoUpdate = true,
    updateInterval = 1000,
    enableNotifications = true,
  } = options;

  // State
  const [currentIncident, setCurrentIncident] = useState<IncidentStatus | null>(
    tracker.getCurrentIncident()
  );
  const [statusHistory, setStatusHistory] = useState<StatusTransition[]>(
    tracker.getStatusHistory()
  );
  const [lastTransition, setLastTransition] = useState<StatusTransition | null>(
    null
  );

  // Refs for cleanup
  const updateTimerRef = useRef<NodeJS.Timeout | null>(null);
  const unsubscribersRef = useRef<(() => void)[]>([]);

  // Initialize tracker observer
  useEffect(() => {
    const unsubscribe = tracker.addObserver((incident) => {
      setCurrentIncident(incident);
      setStatusHistory(tracker.getStatusHistory());
    });

    unsubscribersRef.current.push(unsubscribe);

    return () => {
      unsubscribe();
    };
  }, [tracker]);

  // Auto-update timer for progress calculation
  useEffect(() => {
    if (!autoUpdate || !currentIncident || currentIncident.isComplete) {
      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
        updateTimerRef.current = null;
      }
      return;
    }

    updateTimerRef.current = setInterval(() => {
      // Trigger a re-render to update progress calculations
      setCurrentIncident((prev) => (prev ? { ...prev } : null));
    }, updateInterval);

    return () => {
      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
        updateTimerRef.current = null;
      }
    };
  }, [autoUpdate, updateInterval, currentIncident?.isComplete]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      unsubscribersRef.current.forEach((unsubscribe) => unsubscribe());
      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
      }
    };
  }, []);

  // Actions
  const startIncident = useCallback(
    (incident: Partial<IncidentStatus>) => {
      tracker.startIncident(incident);
    },
    [tracker]
  );

  const updateStatus = useCallback(
    (update: Partial<IncidentStatus>) => {
      tracker.updateIncidentStatus(update);
    },
    [tracker]
  );

  const markResolved = useCallback(
    (resolutionTime?: number) => {
      tracker.markIncidentResolved(resolutionTime);
    },
    [tracker]
  );

  const clearIncident = useCallback(() => {
    tracker.clearIncident();
  }, [tracker]);

  // Event handlers
  const onResolution = useCallback(
    (callback: (resolution: IncidentResolution) => void) => {
      const unsubscribe = tracker.onIncidentResolved(callback);
      unsubscribersRef.current.push(unsubscribe);
      return unsubscribe;
    },
    [tracker]
  );

  const onPhaseTransition = useCallback(
    (callback: (transition: StatusTransition) => void) => {
      const unsubscribe = tracker.onPhaseTransition((transition) => {
        setLastTransition(transition);
        callback(transition);
      });
      unsubscribersRef.current.push(unsubscribe);
      return unsubscribe;
    },
    [tracker]
  );

  const onStatusUpdate = useCallback(
    (callback: (status: IncidentStatus) => void) => {
      const unsubscribe = tracker.onStatusUpdate(callback);
      unsubscribersRef.current.push(unsubscribe);
      return unsubscribe;
    },
    [tracker]
  );

  // Computed values
  const isActive = useMemo(() => {
    return currentIncident !== null && !currentIncident.isComplete;
  }, [currentIncident]);

  const isResolved = useMemo(() => {
    return currentIncident?.isComplete === true;
  }, [currentIncident]);

  const progress = useMemo(() => {
    return currentIncident ? tracker.calculateProgress() : 0;
  }, [currentIncident, tracker]);

  const currentPhase = useMemo(() => {
    return currentIncident?.phase || null;
  }, [currentIncident]);

  const estimatedCompletion = useMemo(() => {
    return currentIncident ? tracker.estimateCompletion() : null;
  }, [currentIncident, tracker]);

  const resolutionTime = useMemo(() => {
    return currentIncident?.resolutionTime || null;
  }, [currentIncident]);

  const phaseProgress = useMemo(() => {
    if (!currentIncident) return {};

    const phases = [
      "detection",
      "diagnosis",
      "prediction",
      "resolution",
      "communication",
    ];
    const progress: Record<string, number> = {};

    phases.forEach((phase) => {
      progress[phase] = tracker.getPhaseProgress(phase);
    });

    return progress;
  }, [currentIncident, tracker]);

  const completedPhases = useMemo(() => {
    return Object.entries(phaseProgress)
      .filter(([_, progress]) => progress === 100)
      .map(([phase]) => phase);
  }, [phaseProgress]);

  const remainingPhases = useMemo(() => {
    return Object.entries(phaseProgress)
      .filter(([_, progress]) => progress === 0)
      .map(([phase]) => phase);
  }, [phaseProgress]);

  // Utilities
  const getPhaseConfig = useCallback(() => {
    return tracker.getPhaseConfig();
  }, [tracker]);

  const formatDuration = useCallback((seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }, []);

  const getBusinessImpact = useCallback(() => {
    if (!currentIncident || !currentIncident.resolutionTime) return null;

    const severity = currentIncident.severity || "medium";
    const resolutionTime = currentIncident.resolutionTime;

    const baseCost = {
      low: 1000,
      medium: 5000,
      high: 15000,
      critical: 50000,
    }[severity];

    const costPerMinute = baseCost / 60;
    const totalCost = Math.max(
      0,
      baseCost - costPerMinute * (resolutionTime / 60)
    );

    return {
      costSaved: Math.floor(totalCost),
      downtime: resolutionTime,
      affectedUsers: Math.floor(Math.random() * 10000) + 1000,
    };
  }, [currentIncident]);

  return {
    // Current state
    currentIncident,
    isActive,
    isResolved,
    progress,
    currentPhase,
    estimatedCompletion,
    resolutionTime,

    // History and transitions
    statusHistory,
    lastTransition,

    // Phase information
    phaseProgress,
    completedPhases,
    remainingPhases,

    // Actions
    startIncident,
    updateStatus,
    markResolved,
    clearIncident,

    // Event handlers
    onResolution,
    onPhaseTransition,
    onStatusUpdate,

    // Utilities
    getPhaseConfig,
    formatDuration,
    getBusinessImpact,
  };
}

/**
 * Simplified hook for basic incident status monitoring
 */
export function useSimpleIncidentStatus(): {
  isActive: boolean;
  isResolved: boolean;
  progress: number;
  currentPhase: string | null;
  currentIncident: IncidentStatus | null;
} {
  const { isActive, isResolved, progress, currentPhase, currentIncident } =
    useIncidentStatus({
      autoUpdate: true,
      updateInterval: 2000, // Less frequent updates for simple use case
    });

  return {
    isActive,
    isResolved,
    progress,
    currentPhase,
    currentIncident,
  };
}

/**
 * Hook for monitoring incident resolution with notifications
 */
export function useIncidentResolution(): {
  isResolved: boolean;
  resolutionTime: number | null;
  businessImpact: any;
  onResolution: (
    callback: (resolution: IncidentResolution) => void
  ) => () => void;
} {
  const { isResolved, resolutionTime, getBusinessImpact, onResolution } =
    useIncidentStatus({
      enableNotifications: true,
    });

  const businessImpact = useMemo(() => {
    return getBusinessImpact();
  }, [getBusinessImpact]);

  return {
    isResolved,
    resolutionTime,
    businessImpact,
    onResolution,
  };
}

/**
 * Hook for phase transition monitoring
 */
export function usePhaseTransitions(): {
  currentPhase: string | null;
  phaseProgress: Record<string, number>;
  completedPhases: string[];
  remainingPhases: string[];
  lastTransition: StatusTransition | null;
  onPhaseTransition: (
    callback: (transition: StatusTransition) => void
  ) => () => void;
} {
  const {
    currentPhase,
    phaseProgress,
    completedPhases,
    remainingPhases,
    lastTransition,
    onPhaseTransition,
  } = useIncidentStatus();

  return {
    currentPhase,
    phaseProgress,
    completedPhases,
    remainingPhases,
    lastTransition,
    onPhaseTransition,
  };
}
