/**
 * useProgressTimeline Hook
 * React hook for managing real-time progress timeline
 * Requirements: 3.3 - Display Status_Timeline with real-time progress and estimated completion times
 */

import { useState, useEffect, useCallback } from "react";
import {
  ProgressTimelineManager,
  TimelineEvent,
  TimelineMetrics,
  ProgressEstimate,
  progressTimelineManager,
} from "../progress-timeline-manager";
import { IncidentPhase } from "../phase-transition-manager";
import { AgentType } from "../agent-completion-manager";

export interface UseProgressTimelineReturn {
  metrics: TimelineMetrics;
  events: TimelineEvent[];
  estimates: ProgressEstimate[];
  startIncident: (incidentId: string) => void;
  addEvent: (event: Omit<TimelineEvent, "id" | "timestamp">) => TimelineEvent;
  updateEvent: (eventId: string, updates: Partial<TimelineEvent>) => void;
  reset: () => void;
  isActive: boolean;
}

export function useProgressTimeline(
  manager: ProgressTimelineManager = progressTimelineManager,
  updateInterval: number = 1000 // Update every second
): UseProgressTimelineReturn {
  const [metrics, setMetrics] = useState<TimelineMetrics>(manager.getMetrics());
  const [events, setEvents] = useState<TimelineEvent[]>(manager.getEvents());
  const [estimates, setEstimates] = useState<ProgressEstimate[]>(
    manager.getEstimates()
  );
  const [isActive, setIsActive] = useState(false);

  // Subscribe to timeline updates
  useEffect(() => {
    const unsubscribe = manager.onUpdate((newMetrics: TimelineMetrics) => {
      setMetrics(newMetrics);
      setEvents(manager.getEvents());
      setEstimates(manager.getEstimates());
      setIsActive(newMetrics.elapsedTime > 0);
    });

    return unsubscribe;
  }, [manager]);

  // Real-time updates for elapsed time and progress
  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      const currentMetrics = manager.getMetrics();
      setMetrics(currentMetrics);
    }, updateInterval);

    return () => clearInterval(interval);
  }, [manager, isActive, updateInterval]);

  const startIncident = useCallback(
    (incidentId: string) => {
      manager.startIncident(incidentId);
      setIsActive(true);
    },
    [manager]
  );

  const addEvent = useCallback(
    (event: Omit<TimelineEvent, "id" | "timestamp">) => {
      return manager.addEvent(event);
    },
    [manager]
  );

  const updateEvent = useCallback(
    (eventId: string, updates: Partial<TimelineEvent>) => {
      manager.updateEvent(eventId, updates);
    },
    [manager]
  );

  const reset = useCallback(() => {
    manager.reset();
    setIsActive(false);
  }, [manager]);

  return {
    metrics,
    events,
    estimates,
    startIncident,
    addEvent,
    updateEvent,
    reset,
    isActive,
  };
}
