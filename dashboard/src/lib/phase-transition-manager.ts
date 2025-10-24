/**
 * Phase Transition Manager
 * Handles smooth visual transitions between incident phases
 * Requirements: 3.1 - Add visual transitions between incident phases
 */

import { motion, Variants } from "framer-motion";

export type IncidentPhase =
  | "detection"
  | "diagnosis"
  | "prediction"
  | "resolution"
  | "communication"
  | "resolved";

export interface PhaseTransition {
  from: IncidentPhase | null;
  to: IncidentPhase;
  timestamp: Date;
  duration: number;
}

export interface PhaseConfig {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: string;
  description: string;
}

export const PHASE_CONFIGS: Record<IncidentPhase, PhaseConfig> = {
  detection: {
    label: "Detection",
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/30",
    icon: "AlertTriangle",
    description: "Identifying anomalies and potential incidents",
  },
  diagnosis: {
    label: "Diagnosis",
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    icon: "Activity",
    description: "Analyzing root cause and impact assessment",
  },
  prediction: {
    label: "Prediction",
    color: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    icon: "TrendingUp",
    description: "Forecasting incident escalation and business impact",
  },
  resolution: {
    label: "Resolution",
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    icon: "Shield",
    description: "Executing automated remediation actions",
  },
  communication: {
    label: "Communication",
    color: "text-indigo-600 dark:text-indigo-400",
    bgColor: "bg-indigo-500/10",
    borderColor: "border-indigo-500/30",
    icon: "Users",
    description: "Notifying stakeholders and updating status",
  },
  resolved: {
    label: "Resolved",
    color: "text-green-600 dark:text-green-400",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/30",
    icon: "CheckCircle",
    description: "Incident successfully resolved",
  },
};

export const PHASE_ORDER: IncidentPhase[] = [
  "detection",
  "diagnosis",
  "prediction",
  "resolution",
  "communication",
  "resolved",
];

export class PhaseTransitionManager {
  private currentPhase: IncidentPhase | null = null;
  private transitionHistory: PhaseTransition[] = [];
  private transitionCallbacks: Array<(transition: PhaseTransition) => void> =
    [];

  constructor() {
    this.currentPhase = null;
  }

  /**
   * Transition to a new phase with animation support
   */
  public transitionToPhase(newPhase: IncidentPhase): PhaseTransition {
    const transition: PhaseTransition = {
      from: this.currentPhase,
      to: newPhase,
      timestamp: new Date(),
      duration: this.calculateTransitionDuration(this.currentPhase, newPhase),
    };

    this.transitionHistory.push(transition);
    this.currentPhase = newPhase;

    // Notify callbacks
    this.transitionCallbacks.forEach((callback) => callback(transition));

    return transition;
  }

  /**
   * Get the current phase
   */
  public getCurrentPhase(): IncidentPhase | null {
    return this.currentPhase;
  }

  /**
   * Get transition history
   */
  public getTransitionHistory(): PhaseTransition[] {
    return [...this.transitionHistory];
  }

  /**
   * Subscribe to phase transitions
   */
  public onPhaseTransition(
    callback: (transition: PhaseTransition) => void
  ): () => void {
    this.transitionCallbacks.push(callback);

    // Return unsubscribe function
    return () => {
      const index = this.transitionCallbacks.indexOf(callback);
      if (index > -1) {
        this.transitionCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Calculate transition duration based on phase complexity
   */
  private calculateTransitionDuration(
    from: IncidentPhase | null,
    to: IncidentPhase
  ): number {
    // Base duration in milliseconds
    const baseDuration = 800;

    // Add complexity based on phase
    const phaseComplexity: Record<IncidentPhase, number> = {
      detection: 1.0,
      diagnosis: 1.5,
      prediction: 1.2,
      resolution: 2.0,
      communication: 0.8,
      resolved: 1.5,
    };

    return baseDuration * phaseComplexity[to];
  }

  /**
   * Reset the phase manager
   */
  public reset(): void {
    this.currentPhase = null;
    this.transitionHistory = [];
  }

  /**
   * Get phase progress (0-100) based on current position in workflow
   */
  public getPhaseProgress(phase: IncidentPhase): number {
    if (!this.currentPhase) return 0;

    const currentIndex = PHASE_ORDER.indexOf(this.currentPhase);
    const targetIndex = PHASE_ORDER.indexOf(phase);

    if (targetIndex < currentIndex) return 100; // Completed
    if (targetIndex === currentIndex) return 75; // In progress
    return 0; // Not started
  }

  /**
   * Check if a phase is active
   */
  public isPhaseActive(phase: IncidentPhase): boolean {
    return this.currentPhase === phase;
  }

  /**
   * Check if a phase is completed
   */
  public isPhaseCompleted(phase: IncidentPhase): boolean {
    if (!this.currentPhase) return false;

    const currentIndex = PHASE_ORDER.indexOf(this.currentPhase);
    const targetIndex = PHASE_ORDER.indexOf(phase);

    return targetIndex < currentIndex || this.currentPhase === "resolved";
  }
}

// Animation variants for phase transitions
export const phaseTransitionVariants: Variants = {
  initial: {
    opacity: 0,
    scale: 0.8,
    y: 20,
  },
  enter: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 25,
      duration: 0.6,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    y: -10,
    transition: {
      duration: 0.3,
    },
  },
};

export const phaseIndicatorVariants: Variants = {
  inactive: {
    scale: 1,
    opacity: 0.6,
    borderWidth: 1,
  },
  active: {
    scale: 1.1,
    opacity: 1,
    borderWidth: 2,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 20,
    },
  },
  completed: {
    scale: 1,
    opacity: 1,
    borderWidth: 2,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 25,
    },
  },
};

export const phaseProgressVariants: Variants = {
  initial: { width: 0 },
  animate: (progress: number) => ({
    width: `${progress}%`,
    transition: {
      duration: 1.2,
      ease: "easeOut",
    },
  }),
};

// Create singleton instance
export const phaseTransitionManager = new PhaseTransitionManager();
