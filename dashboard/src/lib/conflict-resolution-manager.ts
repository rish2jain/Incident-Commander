/**
 * Conflict Resolution Manager
 * Manages multi-agent decision making and consensus visualization
 * Requirements: 3.4 - Highlight consensus resolution processes when agents disagree
 */

import { AgentType } from "./agent-completion-manager";

export interface AgentRecommendation {
  agentType: AgentType;
  actionId: string;
  title: string;
  description: string;
  confidence: number;
  reasoning: string;
  timestamp: Date;
  priority: "low" | "medium" | "high" | "critical";
  estimatedImpact: string;
  riskLevel: "low" | "medium" | "high";
}

export interface ConflictResolution {
  id: string;
  timestamp: Date;
  conflictType:
    | "action_disagreement"
    | "priority_conflict"
    | "confidence_gap"
    | "timing_dispute";
  recommendations: AgentRecommendation[];
  consensusMethod:
    | "weighted_voting"
    | "confidence_threshold"
    | "human_escalation"
    | "majority_rule";
  resolution: AgentRecommendation | null;
  resolutionTime: number; // milliseconds
  participatingAgents: AgentType[];
  consensusScore: number; // 0-1, how much agents agreed
  isResolved: boolean;
  escalatedToHuman: boolean;
}

export interface ConsensusWeights {
  detection: number;
  diagnosis: number;
  prediction: number;
  resolution: number;
  communication: number;
}

export interface ConflictMetrics {
  totalConflicts: number;
  resolvedConflicts: number;
  averageResolutionTime: number;
  consensusSuccessRate: number;
  humanEscalationRate: number;
  agentAgreementScores: Record<AgentType, number>;
}

export class ConflictResolutionManager {
  private conflicts: ConflictResolution[] = [];
  private conflictCallbacks: Array<(conflict: ConflictResolution) => void> = [];
  private resolutionCallbacks: Array<(resolution: ConflictResolution) => void> =
    [];

  // Default consensus weights (from architecture requirements)
  private readonly DEFAULT_WEIGHTS: ConsensusWeights = {
    detection: 0.2,
    diagnosis: 0.4,
    prediction: 0.3,
    resolution: 0.1,
    communication: 0.05,
  };

  private readonly CONFIDENCE_THRESHOLD = 0.7;
  private readonly CONSENSUS_THRESHOLD = 0.6;

  constructor() {}

  /**
   * Register a new conflict between agents
   */
  public registerConflict(
    recommendations: AgentRecommendation[],
    conflictType: ConflictResolution["conflictType"] = "action_disagreement"
  ): ConflictResolution {
    const conflict: ConflictResolution = {
      id: `conflict-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      conflictType,
      recommendations,
      consensusMethod: this.determineConsensusMethod(recommendations),
      resolution: null,
      resolutionTime: 0,
      participatingAgents: [
        ...Array.from(new Set(recommendations.map((r) => r.agentType))),
      ],
      consensusScore: this.calculateConsensusScore(recommendations),
      isResolved: false,
      escalatedToHuman: false,
    };

    this.conflicts.push(conflict);

    // Notify callbacks
    this.conflictCallbacks.forEach((callback) => callback(conflict));

    // Attempt automatic resolution
    this.attemptResolution(conflict);

    return conflict;
  }

  /**
   * Attempt to resolve a conflict automatically
   */
  public attemptResolution(conflict: ConflictResolution): void {
    const startTime = Date.now();
    let resolution: AgentRecommendation | null = null;

    switch (conflict.consensusMethod) {
      case "weighted_voting":
        resolution = this.resolveByWeightedVoting(conflict.recommendations);
        break;
      case "confidence_threshold":
        resolution = this.resolveByConfidenceThreshold(
          conflict.recommendations
        );
        break;
      case "majority_rule":
        resolution = this.resolveByMajorityRule(conflict.recommendations);
        break;
      case "human_escalation":
        this.escalateToHuman(conflict);
        return;
    }

    if (resolution) {
      conflict.resolution = resolution;
      conflict.resolutionTime = Date.now() - startTime;
      conflict.isResolved = true;

      // Notify resolution callbacks
      this.resolutionCallbacks.forEach((callback) => callback(conflict));
    } else {
      // Escalate to human if automatic resolution fails
      this.escalateToHuman(conflict);
    }
  }

  /**
   * Resolve conflict using weighted voting based on agent expertise
   */
  private resolveByWeightedVoting(
    recommendations: AgentRecommendation[]
  ): AgentRecommendation | null {
    const actionScores = new Map<
      string,
      { recommendation: AgentRecommendation; score: number }
    >();

    recommendations.forEach((rec) => {
      const weight = this.DEFAULT_WEIGHTS[rec.agentType];
      const score = rec.confidence * weight;

      const existing = actionScores.get(rec.actionId);
      if (!existing || score > existing.score) {
        actionScores.set(rec.actionId, { recommendation: rec, score });
      }
    });

    // Find the action with highest weighted score
    let bestAction: {
      recommendation: AgentRecommendation;
      score: number;
    } | null = null;
    for (const action of Array.from(actionScores.values())) {
      if (!bestAction || action.score > bestAction.score) {
        bestAction = action;
      }
    }

    // Only return if score meets threshold
    return bestAction && bestAction.score >= this.CONFIDENCE_THRESHOLD
      ? bestAction.recommendation
      : null;
  }

  /**
   * Resolve conflict by confidence threshold
   */
  private resolveByConfidenceThreshold(
    recommendations: AgentRecommendation[]
  ): AgentRecommendation | null {
    // Find recommendation with highest confidence above threshold
    const highConfidenceRecs = recommendations.filter(
      (rec) => rec.confidence >= this.CONFIDENCE_THRESHOLD
    );

    if (highConfidenceRecs.length === 0) return null;

    return highConfidenceRecs.reduce((best, current) =>
      current.confidence > best.confidence ? current : best
    );
  }

  /**
   * Resolve conflict by majority rule
   */
  private resolveByMajorityRule(
    recommendations: AgentRecommendation[]
  ): AgentRecommendation | null {
    const actionCounts = new Map<
      string,
      { recommendation: AgentRecommendation; count: number }
    >();

    recommendations.forEach((rec) => {
      const existing = actionCounts.get(rec.actionId);
      if (existing) {
        existing.count++;
      } else {
        actionCounts.set(rec.actionId, { recommendation: rec, count: 1 });
      }
    });

    // Find action with most votes
    let majorityAction: {
      recommendation: AgentRecommendation;
      count: number;
    } | null = null;
    for (const action of Array.from(actionCounts.values())) {
      if (!majorityAction || action.count > majorityAction.count) {
        majorityAction = action;
      }
    }

    // Require actual majority (>50%)
    const totalVotes = recommendations.length;
    return majorityAction && majorityAction.count > totalVotes / 2
      ? majorityAction.recommendation
      : null;
  }

  /**
   * Escalate conflict to human decision maker
   */
  private escalateToHuman(conflict: ConflictResolution): void {
    conflict.escalatedToHuman = true;
    conflict.consensusMethod = "human_escalation";

    // In a real system, this would trigger human notification
    console.log(`Conflict ${conflict.id} escalated to human decision maker`);
  }

  /**
   * Determine the best consensus method for given recommendations
   */
  private determineConsensusMethod(
    recommendations: AgentRecommendation[]
  ): ConflictResolution["consensusMethod"] {
    const uniqueActions = new Set(recommendations.map((r) => r.actionId)).size;
    const totalRecs = recommendations.length;
    const avgConfidence =
      recommendations.reduce((sum, r) => sum + r.confidence, 0) / totalRecs;
    const highRiskCount = recommendations.filter(
      (r) => r.riskLevel === "high"
    ).length;

    // High risk situations require human oversight
    if (highRiskCount > 0 || avgConfidence < 0.5) {
      return "human_escalation";
    }

    // If many different actions proposed, use weighted voting
    if (uniqueActions > 2) {
      return "weighted_voting";
    }

    // If high confidence recommendations exist, use confidence threshold
    if (avgConfidence >= this.CONFIDENCE_THRESHOLD) {
      return "confidence_threshold";
    }

    // Default to majority rule
    return "majority_rule";
  }

  /**
   * Calculate consensus score (how much agents agree)
   */
  private calculateConsensusScore(
    recommendations: AgentRecommendation[]
  ): number {
    if (recommendations.length <= 1) return 1.0;

    const actionCounts = new Map<string, number>();
    recommendations.forEach((rec) => {
      actionCounts.set(rec.actionId, (actionCounts.get(rec.actionId) || 0) + 1);
    });

    const maxCount = Math.max(...Array.from(actionCounts.values()));
    return maxCount / recommendations.length;
  }

  /**
   * Subscribe to conflict events
   */
  public onConflict(
    callback: (conflict: ConflictResolution) => void
  ): () => void {
    this.conflictCallbacks.push(callback);

    return () => {
      const index = this.conflictCallbacks.indexOf(callback);
      if (index > -1) {
        this.conflictCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Subscribe to resolution events
   */
  public onResolution(
    callback: (resolution: ConflictResolution) => void
  ): () => void {
    this.resolutionCallbacks.push(callback);

    return () => {
      const index = this.resolutionCallbacks.indexOf(callback);
      if (index > -1) {
        this.resolutionCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Get recent conflicts
   */
  public getRecentConflicts(limit: number = 10): ConflictResolution[] {
    return this.conflicts
      .slice(-limit)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Get conflict metrics
   */
  public getMetrics(): ConflictMetrics {
    const total = this.conflicts.length;
    const resolved = this.conflicts.filter((c) => c.isResolved).length;
    const escalated = this.conflicts.filter((c) => c.escalatedToHuman).length;

    const avgResolutionTime =
      resolved > 0
        ? this.conflicts
            .filter((c) => c.isResolved)
            .reduce((sum, c) => sum + c.resolutionTime, 0) / resolved
        : 0;

    const agentAgreementScores: Record<AgentType, number> = {
      detection: this.calculateAgentAgreementScore("detection"),
      diagnosis: this.calculateAgentAgreementScore("diagnosis"),
      prediction: this.calculateAgentAgreementScore("prediction"),
      resolution: this.calculateAgentAgreementScore("resolution"),
      communication: this.calculateAgentAgreementScore("communication"),
    };

    return {
      totalConflicts: total,
      resolvedConflicts: resolved,
      averageResolutionTime: avgResolutionTime,
      consensusSuccessRate: total > 0 ? resolved / total : 1,
      humanEscalationRate: total > 0 ? escalated / total : 0,
      agentAgreementScores,
    };
  }

  /**
   * Calculate how often an agent agrees with final resolutions
   */
  private calculateAgentAgreementScore(agentType: AgentType): number {
    const relevantConflicts = this.conflicts.filter(
      (c) =>
        c.isResolved &&
        c.resolution &&
        c.participatingAgents.includes(agentType)
    );

    if (relevantConflicts.length === 0) return 1.0;

    const agreements = relevantConflicts.filter((c) => {
      const agentRec = c.recommendations.find((r) => r.agentType === agentType);
      return agentRec && agentRec.actionId === c.resolution!.actionId;
    }).length;

    return agreements / relevantConflicts.length;
  }

  /**
   * Clear conflict history
   */
  public clearHistory(): void {
    this.conflicts = [];
  }

  /**
   * Get active (unresolved) conflicts
   */
  public getActiveConflicts(): ConflictResolution[] {
    return this.conflicts.filter((c) => !c.isResolved);
  }

  /**
   * Manually resolve a conflict (for human decisions)
   */
  public manuallyResolve(
    conflictId: string,
    selectedRecommendation: AgentRecommendation
  ): void {
    const conflict = this.conflicts.find((c) => c.id === conflictId);
    if (!conflict || conflict.isResolved) return;

    conflict.resolution = selectedRecommendation;
    conflict.isResolved = true;
    conflict.resolutionTime = Date.now() - conflict.timestamp.getTime();

    // Notify resolution callbacks
    this.resolutionCallbacks.forEach((callback) => callback(conflict));
  }
}

// Create singleton instance
export const conflictResolutionManager = new ConflictResolutionManager();
