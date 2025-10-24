/**
 * usePhaseTransitions Hook
 * React hook for managing phase transitions with animations
 * Requirements: 3.1 - Add visual transitions between incident phases
 */

import { useState, useEffect, useCallback } from "react";
import {
  PhaseTransitionManager,
  IncidentPhase,
  PhaseTransition,
  phaseTransitionManager,
} from "../phase-transition-manager";

export interface UsePhaseTransitionsReturn {
  currentPhase: IncidentPhase | null;
  transitionHistory: PhaseTransition[];
  transitionToPhase: (phase: IncidentPhase) => void;
  getPhaseProgress: (phase: IncidentPhase) => number;
  isPhaseActive: (phase: IncidentPhase) => boolean;
  isPhaseCompleted: (phase: IncidentPhase) => boolean;
  reset: () => void;
  isTransitioning: boolean;
  lastTransition: PhaseTransition | null;
}

export function usePhaseTransitions(
  manager: PhaseTransitionManager = phaseTransitionManager
): UsePhaseTransitionsReturn {
  const [currentPhase, setCurrentPhase] = useState<IncidentPhase | null>(
    manager.getCurrentPhase()
  );
  const [transitionHistory, setTransitionHistory] = useState<PhaseTransition[]>(
    manager.getTransitionHistory()
  );
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [lastTransition, setLastTransition] = useState<PhaseTransition | null>(
    null
  );

  // Subscribe to phase transitions
  useEffect(() => {
    const unsubscribe = manager.onPhaseTransition(
      (transition: PhaseTransition) => {
        setCurrentPhase(transition.to);
        setTransitionHistory(manager.getTransitionHistory());
        setLastTransition(transition);

        // Set transitioning state
        setIsTransitioning(true);

        // Clear transitioning state after animation duration
        const timer = setTimeout(() => {
          setIsTransitioning(false);
        }, transition.duration);

        return () => clearTimeout(timer);
      }
    );

    return unsubscribe;
  }, [manager]);

  const transitionToPhase = useCallback(
    (phase: IncidentPhase) => {
      manager.transitionToPhase(phase);
    },
    [manager]
  );

  const getPhaseProgress = useCallback(
    (phase: IncidentPhase) => {
      return manager.getPhaseProgress(phase);
    },
    [manager, currentPhase]
  );

  const isPhaseActive = useCallback(
    (phase: IncidentPhase) => {
      return manager.isPhaseActive(phase);
    },
    [manager, currentPhase]
  );

  const isPhaseCompleted = useCallback(
    (phase: IncidentPhase) => {
      return manager.isPhaseCompleted(phase);
    },
    [manager, currentPhase]
  );

  const reset = useCallback(() => {
    manager.reset();
    setCurrentPhase(null);
    setTransitionHistory([]);
    setLastTransition(null);
    setIsTransitioning(false);
  }, [manager]);

  return {
    currentPhase,
    transitionHistory,
    transitionToPhase,
    getPhaseProgress,
    isPhaseActive,
    isPhaseCompleted,
    reset,
    isTransitioning,
    lastTransition,
  };
}
