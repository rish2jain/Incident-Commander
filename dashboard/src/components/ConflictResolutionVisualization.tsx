/**
 * Conflict Resolution Visualization Component
 * Visual indicators for multi-agent decision making and consensus
 * Requirements: 3.4 - Highlight consensus resolution processes when agents disagree
 */

"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  Activity,
  TrendingUp,
  Shield,
  Users,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Target,
  Scale,
  Brain,
  Vote,
  AlertCircle,
  User,
  Gavel,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import {
  ConflictResolution,
  AgentRecommendation,
  ConflictMetrics,
} from "../lib/conflict-resolution-manager";
import { AgentType } from "../lib/agent-completion-manager";
import { useConflictResolution } from "../lib/hooks/useConflictResolution";

const AGENT_ICONS = {
  detection: AlertTriangle,
  diagnosis: Activity,
  prediction: TrendingUp,
  resolution: Shield,
  communication: Users,
};

const AGENT_COLORS = {
  detection: "text-orange-600 dark:text-orange-400",
  diagnosis: "text-blue-600 dark:text-blue-400",
  prediction: "text-purple-600 dark:text-purple-400",
  resolution: "text-red-600 dark:text-red-400",
  communication: "text-indigo-600 dark:text-indigo-400",
};

const CONSENSUS_METHOD_ICONS = {
  weighted_voting: Scale,
  confidence_threshold: Target,
  human_escalation: User,
  majority_rule: Vote,
};

interface ConflictResolutionVisualizationProps {
  showActiveConflicts?: boolean;
  showRecentConflicts?: boolean;
  showMetrics?: boolean;
  maxRecentItems?: number;
  className?: string;
}

const ConflictAlert = ({
  conflict,
  isVisible,
}: {
  conflict: ConflictResolution;
  isVisible: boolean;
}) => {
  const MethodIcon = CONSENSUS_METHOD_ICONS[conflict.consensusMethod];

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8, y: -50 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: -50 }}
          transition={{
            type: "spring",
            stiffness: 400,
            damping: 25,
          }}
          className="fixed top-4 right-4 z-50 max-w-md"
        >
          <div className="p-4 rounded-lg border-2 border-yellow-500/50 bg-yellow-500/10 backdrop-blur-xl shadow-2xl">
            <div className="flex items-start gap-3">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.5, repeat: 3 }}
                className="p-2 rounded-lg bg-yellow-500/20 text-yellow-600"
              >
                <AlertCircle className="w-5 h-5" />
              </motion.div>

              <div className="flex-1">
                <h4 className="font-semibold text-yellow-700 dark:text-yellow-300 mb-1">
                  Agent Conflict Detected
                </h4>
                <p className="text-sm text-yellow-600 dark:text-yellow-400 mb-2">
                  {conflict.participatingAgents.length} agents have conflicting
                  recommendations
                </p>

                <div className="flex items-center gap-2">
                  <MethodIcon className="w-4 h-4 text-yellow-600" />
                  <span className="text-xs text-yellow-700 dark:text-yellow-300 capitalize">
                    Using {conflict.consensusMethod.replace("_", " ")}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const RecommendationCard = ({
  recommendation,
  isSelected,
  onSelect,
}: {
  recommendation: AgentRecommendation;
  isSelected: boolean;
  onSelect?: () => void;
}) => {
  const Icon = AGENT_ICONS[recommendation.agentType];
  const colorClass = AGENT_COLORS[recommendation.agentType];

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "high":
        return "text-red-600 bg-red-500/10 border-red-500/30";
      case "medium":
        return "text-yellow-600 bg-yellow-500/10 border-yellow-500/30";
      case "low":
        return "text-green-600 bg-green-500/10 border-green-500/30";
      default:
        return "text-gray-600 bg-gray-500/10 border-gray-500/30";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "bg-red-500 text-white";
      case "high":
        return "bg-orange-500 text-white";
      case "medium":
        return "bg-yellow-500 text-white";
      case "low":
        return "bg-blue-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      className={`
        relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-300
        ${
          isSelected
            ? "border-primary bg-primary/10 shadow-lg shadow-primary/20"
            : "border-border bg-card hover:border-primary/50"
        }
      `}
      onClick={onSelect}
    >
      {/* Agent Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg bg-muted ${colorClass}`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className={`font-semibold text-sm capitalize ${colorClass}`}>
            {recommendation.agentType}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Badge className={getPriorityColor(recommendation.priority)}>
            {recommendation.priority}
          </Badge>
          {isSelected && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="w-5 h-5 bg-primary rounded-full flex items-center justify-center"
            >
              <CheckCircle className="w-3 h-3 text-white" />
            </motion.div>
          )}
        </div>
      </div>

      {/* Recommendation Content */}
      <div className="space-y-3">
        <div>
          <h4 className="font-semibold text-sm mb-1">{recommendation.title}</h4>
          <p className="text-xs text-muted-foreground line-clamp-2">
            {recommendation.description}
          </p>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Confidence</span>
              <span className="text-xs font-mono">
                {Math.round(recommendation.confidence * 100)}%
              </span>
            </div>
            <Progress
              value={recommendation.confidence * 100}
              className="h-1.5"
            />
          </div>

          <div
            className={`p-2 rounded text-center border ${getRiskColor(
              recommendation.riskLevel
            )}`}
          >
            <div className="text-xs font-semibold capitalize">
              {recommendation.riskLevel} Risk
            </div>
          </div>
        </div>

        {/* Reasoning */}
        <div className="p-2 rounded bg-muted/50 border">
          <div className="text-xs text-muted-foreground mb-1">Reasoning:</div>
          <div className="text-xs line-clamp-2">{recommendation.reasoning}</div>
        </div>

        {/* Impact */}
        <div className="text-xs">
          <span className="text-muted-foreground">Expected Impact: </span>
          <span className="font-medium">{recommendation.estimatedImpact}</span>
        </div>
      </div>
    </motion.div>
  );
};

const ConflictItem = ({
  conflict,
  index,
  onManualResolve,
}: {
  conflict: ConflictResolution;
  index: number;
  onManualResolve?: (
    conflictId: string,
    recommendation: AgentRecommendation
  ) => void;
}) => {
  const [selectedRecommendation, setSelectedRecommendation] =
    React.useState<AgentRecommendation | null>(null);

  const MethodIcon = CONSENSUS_METHOD_ICONS[conflict.consensusMethod];

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  const getConflictTypeColor = (type: string) => {
    switch (type) {
      case "action_disagreement":
        return "text-red-600 bg-red-500/10";
      case "priority_conflict":
        return "text-orange-600 bg-orange-500/10";
      case "confidence_gap":
        return "text-yellow-600 bg-yellow-500/10";
      case "timing_dispute":
        return "text-blue-600 bg-blue-500/10";
      default:
        return "text-gray-600 bg-gray-500/10";
    }
  };

  const handleResolve = () => {
    if (selectedRecommendation && onManualResolve) {
      onManualResolve(conflict.id, selectedRecommendation);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`
        p-6 rounded-lg border-2 
        ${
          conflict.isResolved
            ? "border-green-500/30 bg-green-500/5"
            : conflict.escalatedToHuman
            ? "border-yellow-500/30 bg-yellow-500/5"
            : "border-red-500/30 bg-red-500/5"
        }
      `}
    >
      {/* Conflict Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${getConflictTypeColor(
              conflict.conflictType
            )}`}
          >
            <Brain className="w-5 h-5" />
          </div>

          <div>
            <h4 className="font-semibold text-sm capitalize">
              {conflict.conflictType.replace("_", " ")}
            </h4>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{conflict.timestamp.toLocaleTimeString()}</span>
              {conflict.isResolved && (
                <span>• Resolved in {formatTime(conflict.resolutionTime)}</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Consensus Score */}
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Consensus</div>
            <div className="text-sm font-bold">
              {Math.round(conflict.consensusScore * 100)}%
            </div>
          </div>

          {/* Status Badge */}
          <Badge
            variant={
              conflict.isResolved
                ? "default"
                : conflict.escalatedToHuman
                ? "secondary"
                : "destructive"
            }
            className="flex items-center gap-1"
          >
            <MethodIcon className="w-3 h-3" />
            {conflict.isResolved
              ? "Resolved"
              : conflict.escalatedToHuman
              ? "Human Review"
              : "Active"}
          </Badge>
        </div>
      </div>

      {/* Participating Agents */}
      <div className="mb-4">
        <div className="text-sm font-medium mb-2">Participating Agents:</div>
        <div className="flex items-center gap-2">
          {conflict.participatingAgents.map((agentType) => {
            const Icon = AGENT_ICONS[agentType];
            const colorClass = AGENT_COLORS[agentType];

            return (
              <div
                key={agentType}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${colorClass}`}
              >
                <Icon className="w-3 h-3" />
                <span className="capitalize">{agentType}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-4">
        <div className="text-sm font-medium">Agent Recommendations:</div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {conflict.recommendations.map((rec, recIndex) => (
            <RecommendationCard
              key={`${rec.agentType}-${recIndex}`}
              recommendation={rec}
              isSelected={
                conflict.resolution?.actionId === rec.actionId ||
                selectedRecommendation?.actionId === rec.actionId
              }
              onSelect={
                !conflict.isResolved
                  ? () => setSelectedRecommendation(rec)
                  : undefined
              }
            />
          ))}
        </div>

        {/* Manual Resolution Controls */}
        {!conflict.isResolved &&
          conflict.escalatedToHuman &&
          selectedRecommendation && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-between p-3 rounded-lg bg-primary/10 border border-primary/30"
            >
              <div className="text-sm">
                <span className="font-medium">Selected: </span>
                <span>{selectedRecommendation.title}</span>
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleResolve}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium flex items-center gap-2"
              >
                <Gavel className="w-4 h-4" />
                Resolve Conflict
              </motion.button>
            </motion.div>
          )}

        {/* Resolution Summary */}
        {conflict.isResolved && conflict.resolution && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-3 rounded-lg bg-green-500/10 border border-green-500/30"
          >
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="font-medium text-green-700 dark:text-green-300">
                Resolved by {conflict.consensusMethod.replace("_", " ")}
              </span>
            </div>

            <div className="text-sm text-green-600 dark:text-green-400">
              <span className="font-medium">Selected Action: </span>
              {conflict.resolution.title}
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

const MetricsPanel = ({ metrics }: { metrics: ConflictMetrics }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6"
    >
      {/* Total Conflicts */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-red-500/10 to-red-600/10 border border-red-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {metrics.totalConflicts}
            </div>
            <div className="text-sm text-red-700 dark:text-red-300">
              Total Conflicts
            </div>
          </div>
          <AlertTriangle className="w-6 h-6 text-red-500" />
        </div>
      </div>

      {/* Success Rate */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {Math.round(metrics.consensusSuccessRate * 100)}%
            </div>
            <div className="text-sm text-green-700 dark:text-green-300">
              Success Rate
            </div>
          </div>
          <CheckCircle className="w-6 h-6 text-green-500" />
        </div>
      </div>

      {/* Avg Resolution Time */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {metrics.averageResolutionTime < 1000
                ? `${Math.round(metrics.averageResolutionTime)}ms`
                : `${(metrics.averageResolutionTime / 1000).toFixed(1)}s`}
            </div>
            <div className="text-sm text-blue-700 dark:text-blue-300">
              Avg Resolution
            </div>
          </div>
          <Zap className="w-6 h-6 text-blue-500" />
        </div>
      </div>

      {/* Human Escalation Rate */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border border-yellow-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {Math.round(metrics.humanEscalationRate * 100)}%
            </div>
            <div className="text-sm text-yellow-700 dark:text-yellow-300">
              Human Escalation
            </div>
          </div>
          <User className="w-6 h-6 text-yellow-500" />
        </div>
      </div>
    </motion.div>
  );
};

export default function ConflictResolutionVisualization({
  showActiveConflicts = true,
  showRecentConflicts = true,
  showMetrics = true,
  maxRecentItems = 5,
  className = "",
}: ConflictResolutionVisualizationProps) {
  const {
    recentConflicts,
    activeConflicts,
    metrics,
    manuallyResolve,
    hasActiveConflicts,
    lastConflict,
  } = useConflictResolution(undefined, maxRecentItems);

  return (
    <>
      {/* Conflict Alert Overlay */}
      {lastConflict && !lastConflict.isResolved && (
        <ConflictAlert conflict={lastConflict} isVisible={hasActiveConflicts} />
      )}

      {/* Main Component */}
      <Card className={`relative overflow-hidden ${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Conflict Resolution
            {hasActiveConflicts && (
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="ml-auto flex items-center gap-2"
              >
                <div className="w-2 h-2 bg-red-500 rounded-full" />
                <span className="text-sm text-red-600 font-medium">
                  {activeConflicts.length} Active
                </span>
              </motion.div>
            )}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Metrics Panel */}
          {showMetrics && metrics.totalConflicts > 0 && (
            <MetricsPanel metrics={metrics} />
          )}

          {/* Active Conflicts */}
          {showActiveConflicts && activeConflicts.length > 0 && (
            <div>
              <h4 className="text-md font-semibold mb-4 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500" />
                Active Conflicts ({activeConflicts.length})
              </h4>

              <div className="space-y-4">
                {activeConflicts.map((conflict, index) => (
                  <ConflictItem
                    key={conflict.id}
                    conflict={conflict}
                    index={index}
                    onManualResolve={manuallyResolve}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Recent Conflicts */}
          {showRecentConflicts && (
            <div>
              <h4 className="text-md font-semibold mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Recent Conflicts
              </h4>

              {recentConflicts.length > 0 ? (
                <div className="space-y-4">
                  {recentConflicts.map((conflict, index) => (
                    <ConflictItem
                      key={conflict.id}
                      conflict={conflict}
                      index={index}
                      onManualResolve={manuallyResolve}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No conflicts detected</p>
                  <p className="text-xs mt-1">Agents are in consensus</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
