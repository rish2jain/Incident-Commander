/**
 * Progress Timeline Manager
 * Manages real-time progress tracking with estimated completion times
 * Requirements: 3.3 - Display Status_Timeline with real-time progress and estimated completion times
 */

import { IncidentPhase } from "./phase-transition-manager";
import { AgentType } from "./agent-completion-manager";

export interface TimelineEvent {
  id: string;
  timestamp: Date;
  phase: IncidentPhase;
  agentType?: AgentType;
  title: string;
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  estimatedDuration?: number; // in milliseconds
  actualDuration?: number; // in milliseconds
  progress: number; // 0-100
  confidence?: number;
}

export interface ProgressEstimate {
  phase: IncidentPhase;
  estimatedCompletion: Date;
  confidence: number;
  basedOnHistoricalData: boolean;
}

export interface TimelineMetrics {
  totalEstimatedTime: number;
  elapsedTime: number;
  remainingTime: number;
  overallProgress: number;
  currentPhaseProgress: number;
  estimatedCompletion: Date;
  isOnTrack: boolean;
  delayMinutes: number;
}

export class ProgressTimelineManager {
  private events: TimelineEvent[] = [];
  private startTime: Date | null = null;
  private estimates: Map<IncidentPhase, ProgressEstimate> = new Map();
  private historicalData: Map<IncidentPhase, number[]> = new Map(); // Historical durations
  private updateCallbacks: Array<(metrics: TimelineMetrics) => void> = [];

  // Default phase durations in milliseconds (based on requirements)
  private readonly DEFAULT_PHASE_DURATIONS: Record<IncidentPhase, number> = {
    detection: 30000, // 30 seconds (Requirements: Detection 30s target)
    diagnosis: 120000, // 2 minutes (Requirements: Diagnosis 120s target)
    prediction: 90000, // 1.5 minutes (Requirements: Prediction 90s target)
    resolution: 180000, // 3 minutes (Requirements: Resolution 180s target)
    communication: 10000, // 10 seconds (Requirements: Communication 10s target)
    resolved: 0, // Instant
  };

  constructor() {
    this.initializeHistoricalData();
  }

  /**
   * Start a new incident timeline
   */
  public startIncident(incidentId: string): void {
    this.startTime = new Date();
    this.events = [];
    this.estimates.clear();
    this.generateInitialEstimates();
  }

  /**
   * Add a timeline event
   */
  public addEvent(
    event: Omit<TimelineEvent, "id" | "timestamp">
  ): TimelineEvent {
    const timelineEvent: TimelineEvent = {
      id: `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ...event,
    };

    this.events.push(timelineEvent);
    this.updateEstimates();
    this.notifyCallbacks();

    return timelineEvent;
  }

  /**
   * Update an existing event
   */
  public updateEvent(eventId: string, updates: Partial<TimelineEvent>): void {
    const eventIndex = this.events.findIndex((e) => e.id === eventId);
    if (eventIndex !== -1) {
      this.events[eventIndex] = { ...this.events[eventIndex], ...updates };
      this.updateEstimates();
      this.notifyCallbacks();
    }
  }

  /**
   * Get current timeline metrics
   */
  public getMetrics(): TimelineMetrics {
    if (!this.startTime) {
      return this.getEmptyMetrics();
    }

    const now = new Date();
    const elapsedTime = now.getTime() - this.startTime.getTime();
    const overallProgress = this.calculateOverallProgress();
    const currentPhase = this.getCurrentPhase();
    const currentPhaseProgress = this.getCurrentPhaseProgress();

    const totalEstimatedTime = this.calculateTotalEstimatedTime();
    const remainingTime = Math.max(0, totalEstimatedTime - elapsedTime);
    const estimatedCompletion = new Date(
      this.startTime.getTime() + totalEstimatedTime
    );

    const isOnTrack = elapsedTime <= totalEstimatedTime * 1.1; // 10% buffer
    const delayMinutes = Math.max(
      0,
      (elapsedTime - totalEstimatedTime) / 60000
    );

    return {
      totalEstimatedTime,
      elapsedTime,
      remainingTime,
      overallProgress,
      currentPhaseProgress,
      estimatedCompletion,
      isOnTrack,
      delayMinutes,
    };
  }

  /**
   * Get timeline events
   */
  public getEvents(): TimelineEvent[] {
    return [...this.events].sort(
      (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
    );
  }

  /**
   * Get phase estimates
   */
  public getEstimates(): ProgressEstimate[] {
    return Array.from(this.estimates.values());
  }

  /**
   * Subscribe to timeline updates
   */
  public onUpdate(callback: (metrics: TimelineMetrics) => void): () => void {
    this.updateCallbacks.push(callback);

    return () => {
      const index = this.updateCallbacks.indexOf(callback);
      if (index > -1) {
        this.updateCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Add historical data for better estimates
   */
  public addHistoricalData(phase: IncidentPhase, duration: number): void {
    if (!this.historicalData.has(phase)) {
      this.historicalData.set(phase, []);
    }

    const data = this.historicalData.get(phase)!;
    data.push(duration);

    // Keep only last 20 data points
    if (data.length > 20) {
      data.shift();
    }
  }

  /**
   * Reset the timeline
   */
  public reset(): void {
    this.events = [];
    this.startTime = null;
    this.estimates.clear();
    this.notifyCallbacks();
  }

  /**
   * Get current active phase
   */
  private getCurrentPhase(): IncidentPhase | null {
    const activeEvents = this.events.filter((e) => e.status === "in_progress");
    if (activeEvents.length === 0) return null;

    // Return the most recent active phase
    return activeEvents[activeEvents.length - 1].phase;
  }

  /**
   * Calculate current phase progress
   */
  private getCurrentPhaseProgress(): number {
    const currentPhase = this.getCurrentPhase();
    if (!currentPhase) return 0;

    const phaseEvents = this.events.filter((e) => e.phase === currentPhase);
    if (phaseEvents.length === 0) return 0;

    // Average progress of all events in current phase
    const totalProgress = phaseEvents.reduce(
      (sum, event) => sum + event.progress,
      0
    );
    return totalProgress / phaseEvents.length;
  }

  /**
   * Calculate overall progress across all phases
   */
  private calculateOverallProgress(): number {
    const phaseOrder: IncidentPhase[] = [
      "detection",
      "diagnosis",
      "prediction",
      "resolution",
      "communication",
      "resolved",
    ];
    let totalProgress = 0;

    for (const phase of phaseOrder) {
      const phaseEvents = this.events.filter((e) => e.phase === phase);
      if (phaseEvents.length === 0) continue;

      const phaseProgress =
        phaseEvents.reduce((sum, event) => sum + event.progress, 0) /
        phaseEvents.length;
      totalProgress += phaseProgress / phaseOrder.length;
    }

    return Math.min(100, totalProgress);
  }

  /**
   * Calculate total estimated time for incident resolution
   */
  private calculateTotalEstimatedTime(): number {
    let total = 0;

    for (const estimate of Array.from(this.estimates.values())) {
      const phaseDuration = this.getEstimatedPhaseDuration(estimate.phase);
      total += phaseDuration;
    }

    return total;
  }

  /**
   * Get estimated duration for a phase
   */
  private getEstimatedPhaseDuration(phase: IncidentPhase): number {
    const historicalData = this.historicalData.get(phase);

    if (historicalData && historicalData.length > 0) {
      // Use median of historical data
      const sorted = [...historicalData].sort((a, b) => a - b);
      const mid = Math.floor(sorted.length / 2);
      return sorted.length % 2 === 0
        ? (sorted[mid - 1] + sorted[mid]) / 2
        : sorted[mid];
    }

    return this.DEFAULT_PHASE_DURATIONS[phase];
  }

  /**
   * Generate initial estimates for all phases
   */
  private generateInitialEstimates(): void {
    const phaseOrder: IncidentPhase[] = [
      "detection",
      "diagnosis",
      "prediction",
      "resolution",
      "communication",
      "resolved",
    ];
    let cumulativeTime = 0;

    for (const phase of phaseOrder) {
      const duration = this.getEstimatedPhaseDuration(phase);
      cumulativeTime += duration;

      const estimate: ProgressEstimate = {
        phase,
        estimatedCompletion: new Date(
          (this.startTime?.getTime() || 0) + cumulativeTime
        ),
        confidence: this.historicalData.has(phase) ? 0.8 : 0.6,
        basedOnHistoricalData: this.historicalData.has(phase),
      };

      this.estimates.set(phase, estimate);
    }
  }

  /**
   * Update estimates based on current progress
   */
  private updateEstimates(): void {
    if (!this.startTime) return;

    const now = new Date();
    const elapsedTime = now.getTime() - this.startTime.getTime();

    // Recalculate estimates based on current progress
    this.generateInitialEstimates();

    // Adjust estimates based on actual progress
    const currentPhase = this.getCurrentPhase();
    if (currentPhase) {
      const currentProgress = this.getCurrentPhaseProgress();
      const estimate = this.estimates.get(currentPhase);

      if (estimate && currentProgress > 0) {
        const phaseDuration = this.getEstimatedPhaseDuration(currentPhase);
        const adjustedDuration = (phaseDuration * 100) / currentProgress;

        // Update estimate with adjusted duration
        estimate.estimatedCompletion = new Date(
          this.startTime.getTime() +
            elapsedTime +
            (adjustedDuration * (100 - currentProgress)) / 100
        );
        estimate.confidence = Math.min(0.9, estimate.confidence + 0.1);
      }
    }
  }

  /**
   * Initialize with some sample historical data
   */
  private initializeHistoricalData(): void {
    // Sample historical data for better initial estimates
    this.historicalData.set("detection", [25000, 35000, 28000, 32000, 30000]);
    this.historicalData.set(
      "diagnosis",
      [110000, 130000, 125000, 115000, 120000]
    );
    this.historicalData.set("prediction", [85000, 95000, 88000, 92000, 90000]);
    this.historicalData.set(
      "resolution",
      [170000, 190000, 185000, 175000, 180000]
    );
    this.historicalData.set("communication", [8000, 12000, 9000, 11000, 10000]);
  }

  /**
   * Get empty metrics for when no incident is active
   */
  private getEmptyMetrics(): TimelineMetrics {
    return {
      totalEstimatedTime: 0,
      elapsedTime: 0,
      remainingTime: 0,
      overallProgress: 0,
      currentPhaseProgress: 0,
      estimatedCompletion: new Date(),
      isOnTrack: true,
      delayMinutes: 0,
    };
  }

  /**
   * Notify all callbacks of updates
   */
  private notifyCallbacks(): void {
    const metrics = this.getMetrics();
    this.updateCallbacks.forEach((callback) => callback(metrics));
  }

  /**
   * Format duration for display
   */
  public static formatDuration(milliseconds: number): string {
    if (milliseconds < 1000) {
      return `${Math.round(milliseconds)}ms`;
    } else if (milliseconds < 60000) {
      return `${Math.round(milliseconds / 1000)}s`;
    } else {
      const minutes = Math.floor(milliseconds / 60000);
      const seconds = Math.round((milliseconds % 60000) / 1000);
      return `${minutes}m ${seconds}s`;
    }
  }

  /**
   * Format time for display
   */
  public static formatTime(date: Date): string {
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }
}

// Create singleton instance
export const progressTimelineManager = new ProgressTimelineManager();
