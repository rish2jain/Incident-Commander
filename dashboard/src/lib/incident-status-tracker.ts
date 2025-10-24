/**
 * IncidentStatusTracker - Core class for monitoring incident progress and status
 *
 * Features:
 * - Track incident progress through all phases
 * - Calculate completion estimates
 * - Handle phase transitions
 * - Maintain status history
 * - Trigger resolution callbacks
 */

export interface IncidentStatus {
  id: string;
  phase:
    | "detection"
    | "diagnosis"
    | "prediction"
    | "resolution"
    | "communication"
    | "resolved";
  progress: number; // 0-100
  startTime: Date;
  estimatedCompletion?: Date;
  isComplete: boolean;
  resolutionTime?: number;
  severity?: "low" | "medium" | "high" | "critical";
  title?: string;
  description?: string;
}

export interface StatusTransition {
  from: string;
  to: string;
  timestamp: Date;
  duration: number;
}

export interface IncidentResolution {
  incidentId: string;
  isResolved: boolean;
  resolutionTime: number; // in seconds
  totalPhases: number;
  completedPhases: number;
  currentPhase?: string;
  resolutionSummary?: string;
  actionsPerformed: string[];
  businessImpact: {
    costSaved: number;
    downtime: number;
    affectedUsers: number;
  };
  showCelebration: boolean;
  celebrationDuration: number;
  fadeOutDelay: number;
}

export type IncidentStatusCallback = (incident: IncidentStatus) => void;
export type ResolutionCallback = (resolution: IncidentResolution) => void;
export type PhaseTransitionCallback = (transition: StatusTransition) => void;

/**
 * Phase configuration with expected durations and weights
 */
const PHASE_CONFIG = {
  detection: { duration: 30, weight: 0.15, order: 0 },
  diagnosis: { duration: 120, weight: 0.3, order: 1 },
  prediction: { duration: 90, weight: 0.2, order: 2 },
  resolution: { duration: 180, weight: 0.25, order: 3 },
  communication: { duration: 10, weight: 0.1, order: 4 },
} as const;

export class IncidentStatusTracker {
  private currentIncident: IncidentStatus | null = null;
  private statusHistory: StatusTransition[] = [];
  private completionCallbacks: ResolutionCallback[] = [];
  private statusCallbacks: IncidentStatusCallback[] = [];
  private phaseCallbacks: PhaseTransitionCallback[] = [];
  private phaseStartTimes: Map<string, Date> = new Map();
  private observers: Set<(status: IncidentStatus | null) => void> = new Set();

  constructor() {
    // Initialize with empty state
  }

  /**
   * Start tracking a new incident
   */
  public startIncident(incident: Partial<IncidentStatus>): void {
    const now = new Date();

    this.currentIncident = {
      id: incident.id || `incident-${Date.now()}`,
      phase: incident.phase || "detection",
      progress: incident.progress || 0,
      startTime: incident.startTime || now,
      isComplete: false,
      severity: incident.severity || "medium",
      title: incident.title || "Incident in Progress",
      description: incident.description || "System incident detected",
      ...incident,
    };

    this.phaseStartTimes.clear();
    this.statusHistory = [];

    // Mark all previous phases as completed if starting in a later phase
    const currentPhaseConfig =
      PHASE_CONFIG[this.currentIncident.phase as keyof typeof PHASE_CONFIG];
    if (currentPhaseConfig) {
      Object.entries(PHASE_CONFIG).forEach(([phase, config]) => {
        if (config.order < currentPhaseConfig.order) {
          // Mark previous phases as completed
          const phaseStartTime = new Date(
            now.getTime() - config.duration * 1000
          );
          const phaseEndTime = new Date(
            phaseStartTime.getTime() + config.duration * 1000
          );
          this.phaseStartTimes.set(phase, phaseEndTime);

          // Add to history
          this.statusHistory.push({
            from:
              config.order === 0
                ? "initial"
                : Object.keys(PHASE_CONFIG)[config.order - 1],
            to: phase,
            timestamp: phaseEndTime,
            duration: config.duration,
          });
        }
      });
    }

    this.phaseStartTimes.set(this.currentIncident.phase, now);

    this.notifyObservers();
    this.notifyStatusCallbacks(this.currentIncident);
  }

  /**
   * Update incident status with new information
   */
  public updateIncidentStatus(update: Partial<IncidentStatus>): void {
    if (!this.currentIncident) {
      console.warn("No active incident to update");
      return;
    }

    const previousPhase = this.currentIncident.phase;
    const now = new Date();

    // Update incident properties
    this.currentIncident = {
      ...this.currentIncident,
      ...update,
    };

    // Handle phase transitions
    if (update.phase && update.phase !== previousPhase) {
      this.handlePhaseTransition(previousPhase, update.phase, now);
    }

    // Update progress and estimated completion
    this.updateProgress();
    this.updateEstimatedCompletion();

    this.notifyObservers();
    this.notifyStatusCallbacks(this.currentIncident);
  }

  /**
   * Mark incident as resolved
   */
  public markIncidentResolved(resolutionTime?: number): void {
    if (!this.currentIncident) {
      console.warn("No active incident to resolve");
      return;
    }

    const now = new Date();
    const actualResolutionTime =
      resolutionTime ||
      Math.floor(
        (now.getTime() - this.currentIncident.startTime.getTime()) / 1000
      );

    // Handle final phase transition if not already resolved
    if (this.currentIncident.phase !== "resolved") {
      this.handlePhaseTransition(this.currentIncident.phase, "resolved", now);
    }

    this.currentIncident = {
      ...this.currentIncident,
      phase: "resolved",
      progress: 100,
      isComplete: true,
      resolutionTime: actualResolutionTime,
    };

    // Create resolution object
    const resolution: IncidentResolution = {
      incidentId: this.currentIncident.id,
      isResolved: true,
      resolutionTime: actualResolutionTime,
      totalPhases: Object.keys(PHASE_CONFIG).length,
      completedPhases: Object.keys(PHASE_CONFIG).length,
      currentPhase: "resolved",
      resolutionSummary: `Incident resolved in ${this.formatDuration(
        actualResolutionTime
      )}`,
      actionsPerformed: this.getActionsPerformed(),
      businessImpact: this.calculateBusinessImpact(actualResolutionTime),
      showCelebration: true,
      celebrationDuration: 3000, // 3 seconds
      fadeOutDelay: 30000, // 30 seconds as per requirements
    };

    this.notifyObservers();
    this.notifyStatusCallbacks(this.currentIncident);
    this.notifyCompletionCallbacks(resolution);
  }

  /**
   * Clear current incident
   */
  public clearIncident(): void {
    this.currentIncident = null;
    this.statusHistory = [];
    this.phaseStartTimes.clear();
    this.notifyObservers();
  }

  /**
   * Calculate overall progress based on current phase and phase progress
   */
  public calculateProgress(): number {
    if (!this.currentIncident) return 0;

    const currentPhase = this.currentIncident.phase;
    if (currentPhase === "resolved") return 100;

    const phaseConfig = PHASE_CONFIG[currentPhase as keyof typeof PHASE_CONFIG];
    if (!phaseConfig) return 0;

    // Calculate progress based on completed phases and current phase progress
    let totalProgress = 0;

    // Add progress from completed phases
    Object.entries(PHASE_CONFIG).forEach(([phase, config]) => {
      if (config.order < phaseConfig.order) {
        totalProgress += config.weight * 100;
      }
    });

    // Add progress from current phase (assume 50% if no specific progress given)
    const currentPhaseProgress = this.getCurrentPhaseProgress();
    totalProgress += phaseConfig.weight * 100 * (currentPhaseProgress / 100);

    return Math.min(100, Math.max(0, totalProgress));
  }

  /**
   * Estimate completion time based on current progress and historical data
   */
  public estimateCompletion(): Date | null {
    if (!this.currentIncident) return null;

    const currentPhase = this.currentIncident.phase;
    if (currentPhase === "resolved") return new Date();

    const now = new Date();
    const elapsed = now.getTime() - this.currentIncident.startTime.getTime();

    // Calculate remaining time based on phase durations
    let remainingTime = 0;
    const currentPhaseConfig =
      PHASE_CONFIG[currentPhase as keyof typeof PHASE_CONFIG];

    if (currentPhaseConfig) {
      // Add remaining time for current phase
      const phaseStartTime = this.phaseStartTimes.get(currentPhase);
      if (phaseStartTime) {
        const phaseElapsed = (now.getTime() - phaseStartTime.getTime()) / 1000;
        remainingTime += Math.max(
          0,
          currentPhaseConfig.duration - phaseElapsed
        );
      } else {
        remainingTime += currentPhaseConfig.duration;
      }

      // Add time for remaining phases
      Object.entries(PHASE_CONFIG).forEach(([phase, config]) => {
        if (config.order > currentPhaseConfig.order) {
          remainingTime += config.duration;
        }
      });
    }

    return new Date(now.getTime() + remainingTime * 1000);
  }

  /**
   * Get progress for a specific phase
   */
  public getPhaseProgress(phase: string): number {
    if (!this.currentIncident) return 0;

    const currentPhase = this.currentIncident.phase;
    const phaseConfig = PHASE_CONFIG[phase as keyof typeof PHASE_CONFIG];
    const currentPhaseConfig =
      PHASE_CONFIG[currentPhase as keyof typeof PHASE_CONFIG];

    if (!phaseConfig || !currentPhaseConfig) return 0;

    if (phaseConfig.order < currentPhaseConfig.order) {
      return 100; // Completed phase
    } else if (phaseConfig.order === currentPhaseConfig.order) {
      return this.getCurrentPhaseProgress(); // Current phase
    } else {
      return 0; // Future phase
    }
  }

  /**
   * Get current incident status
   */
  public getCurrentIncident(): IncidentStatus | null {
    return this.currentIncident;
  }

  /**
   * Get status transition history
   */
  public getStatusHistory(): StatusTransition[] {
    return [...this.statusHistory];
  }

  /**
   * Register callback for incident resolution
   */
  public onIncidentResolved(callback: ResolutionCallback): () => void {
    this.completionCallbacks.push(callback);
    return () => {
      const index = this.completionCallbacks.indexOf(callback);
      if (index > -1) {
        this.completionCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Register callback for status updates
   */
  public onStatusUpdate(callback: IncidentStatusCallback): () => void {
    this.statusCallbacks.push(callback);
    return () => {
      const index = this.statusCallbacks.indexOf(callback);
      if (index > -1) {
        this.statusCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Register callback for phase transitions
   */
  public onPhaseTransition(callback: PhaseTransitionCallback): () => void {
    this.phaseCallbacks.push(callback);
    return () => {
      const index = this.phaseCallbacks.indexOf(callback);
      if (index > -1) {
        this.phaseCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Add observer for state changes (for React integration)
   */
  public addObserver(
    callback: (status: IncidentStatus | null) => void
  ): () => void {
    this.observers.add(callback);
    return () => {
      this.observers.delete(callback);
    };
  }

  /**
   * Get phase configuration
   */
  public getPhaseConfig() {
    return PHASE_CONFIG;
  }

  // Private methods

  private handlePhaseTransition(
    from: string,
    to: string,
    timestamp: Date
  ): void {
    const fromStartTime = this.phaseStartTimes.get(from);
    const duration = fromStartTime
      ? (timestamp.getTime() - fromStartTime.getTime()) / 1000
      : 0;

    const transition: StatusTransition = {
      from,
      to,
      timestamp,
      duration,
    };

    this.statusHistory.push(transition);
    this.phaseStartTimes.set(to, timestamp);

    this.notifyPhaseCallbacks(transition);
  }

  private getCurrentPhaseProgress(): number {
    if (!this.currentIncident) return 0;

    const currentPhase = this.currentIncident.phase;
    const phaseStartTime = this.phaseStartTimes.get(currentPhase);
    const phaseConfig = PHASE_CONFIG[currentPhase as keyof typeof PHASE_CONFIG];

    if (!phaseStartTime || !phaseConfig) return 0;

    const elapsed = (Date.now() - phaseStartTime.getTime()) / 1000;
    const progress = Math.min(100, (elapsed / phaseConfig.duration) * 100);

    return progress;
  }

  private updateProgress(): void {
    if (this.currentIncident) {
      this.currentIncident.progress = this.calculateProgress();
    }
  }

  private updateEstimatedCompletion(): void {
    if (this.currentIncident) {
      const estimated = this.estimateCompletion();
      this.currentIncident.estimatedCompletion = estimated || undefined;
    }
  }

  private getActionsPerformed(): string[] {
    // This would typically be populated from actual agent actions
    // For now, return a default set based on phases completed
    const actions: string[] = [];

    this.statusHistory.forEach((transition) => {
      switch (transition.to) {
        case "detection":
          actions.push("Anomaly detected in system metrics");
          break;
        case "diagnosis":
          actions.push("Root cause analysis completed");
          break;
        case "prediction":
          actions.push("Impact assessment and prediction generated");
          break;
        case "resolution":
          actions.push("Automated remediation actions executed");
          break;
        case "communication":
          actions.push("Stakeholders notified of resolution");
          break;
      }
    });

    return actions;
  }

  private calculateBusinessImpact(resolutionTime: number) {
    // Calculate business impact based on resolution time and severity
    const severity = this.currentIncident?.severity || "medium";

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
      affectedUsers: Math.floor(Math.random() * 10000) + 1000, // Simulated
    };
  }

  private formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  private notifyObservers(): void {
    this.observers.forEach((callback) => {
      try {
        callback(this.currentIncident);
      } catch (error) {
        console.error("Error in incident status observer:", error);
      }
    });
  }

  private notifyCompletionCallbacks(resolution: IncidentResolution): void {
    this.completionCallbacks.forEach((callback) => {
      try {
        callback(resolution);
      } catch (error) {
        console.error("Error in completion callback:", error);
      }
    });
  }

  private notifyStatusCallbacks(status: IncidentStatus): void {
    this.statusCallbacks.forEach((callback) => {
      try {
        callback(status);
      } catch (error) {
        console.error("Error in status callback:", error);
      }
    });
  }

  private notifyPhaseCallbacks(transition: StatusTransition): void {
    this.phaseCallbacks.forEach((callback) => {
      try {
        callback(transition);
      } catch (error) {
        console.error("Error in phase transition callback:", error);
      }
    });
  }
}

// Export singleton instance for global use
export const globalIncidentTracker = new IncidentStatusTracker();
