/**
 * Byzantine Consensus Visualization Component
 *
 * Displays real-time weighted voting progress showing how the multi-agent
 * system reaches consensus through Byzantine fault-tolerant decision making.
 */

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { motion, AnimatePresence } from "framer-motion";

interface AgentVote {
  agent_type: string;
  agent_name: string;
  confidence: number;
  weight: number;
  status: "voting" | "agreed" | "abstained" | "error" | "informational";
  reasoning_summary?: string;
}

interface ConsensusState {
  agents: AgentVote[];
  weighted_consensus: number;
  consensus_threshold: number;
  consensus_reached: boolean;
  decision: "pending" | "approved" | "rejected";
  timestamp: Date;
}

interface ByzantineConsensusVisualizationProps {
  consensusState: ConsensusState;
  showDetails?: boolean;
}

export function ByzantineConsensusVisualization({
  consensusState,
  showDetails = true,
}: ByzantineConsensusVisualizationProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    // Animate progress bar smoothly
    const timer = setTimeout(() => {
      setAnimatedProgress(consensusState.weighted_consensus * 100);
    }, 100);
    return () => clearTimeout(timer);
  }, [consensusState.weighted_consensus]);

  const getAgentIcon = (type: string) => {
    const icons: Record<string, string> = {
      detection: "🔍",
      diagnosis: "🔬",
      prediction: "🔮",
      resolution: "⚙️",
      communication: "📢",
    };
    return icons[type.toLowerCase()] || "🤖";
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      voting: "text-blue-500",
      agreed: "text-green-500",
      abstained: "text-gray-500",
      error: "text-red-500",
    };
    return colors[status] || "text-gray-500";
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      voting: "⏳",
      agreed: "✅",
      abstained: "⊖",
      error: "❌",
    };
    return icons[status] || "?";
  };

  return (
    <Card className="border-2 border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-purple-500/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <span className="text-2xl">🔷</span>
            Byzantine Consensus Progress
          </CardTitle>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Badge
                  variant={consensusState.consensus_reached ? "default" : "secondary"}
                  className="cursor-help"
                >
                  {consensusState.consensus_reached ? "✓ Consensus Reached" : "⏳ Building Consensus"}
                </Badge>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="font-semibold mb-1">Byzantine Fault Tolerance</p>
                <p className="text-sm">
                  Agents vote with different weights based on their specialty. Requires weighted consensus above{" "}
                  {Math.round(consensusState.consensus_threshold * 100)}% threshold before autonomous action.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Individual Agent Votes */}
        <div className="space-y-3">
          {consensusState.agents.map((agent, index) => (
            <motion.div
              key={agent.agent_type}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger className="w-full">
                    <div className="flex items-center gap-3 p-3 border rounded-lg hover:border-blue-500/50 transition-all">
                      <span className="text-2xl">{getAgentIcon(agent.agent_type)}</span>

                      <div className="flex-1 text-left">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{agent.agent_name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">
                              Weight: {(agent.weight * 100).toFixed(0)}%
                            </span>
                            <span className={`text-lg ${getStatusColor(agent.status)}`}>
                              {getStatusIcon(agent.status)}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Progress
                            value={agent.confidence * 100}
                            className="h-2 flex-1"
                            style={{
                              // Color based on weight
                              "--progress-background":
                                agent.weight >= 0.4
                                  ? "hsl(var(--primary))"
                                  : agent.weight >= 0.3
                                  ? "hsl(217 91% 60%)"
                                  : "hsl(217 91% 80%)",
                            } as React.CSSProperties}
                          />
                          <span className="text-sm font-bold min-w-[3ch] text-right">
                            {Math.round(agent.confidence * 100)}%
                          </span>
                        </div>

                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <span>Contribution:</span>
                          <span className="font-mono">
                            {Math.round(agent.confidence * 100)}% × {(agent.weight * 100).toFixed(0)}% ={" "}
                            {(agent.confidence * agent.weight * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </TooltipTrigger>
                  {agent.reasoning_summary && (
                    <TooltipContent side="left" className="max-w-sm">
                      <p className="font-semibold mb-1">{agent.agent_name}</p>
                      <p className="text-sm">{agent.reasoning_summary}</p>
                    </TooltipContent>
                  )}
                </Tooltip>
              </TooltipProvider>
            </motion.div>
          ))}
        </div>

        {/* Overall Consensus */}
        <div className="pt-4 border-t space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Total Weighted Consensus</span>
            <span className="text-2xl font-bold tabular-nums">
              {Math.round(consensusState.weighted_consensus * 100)}%
            </span>
          </div>

          <div className="relative">
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.5 }}
              className="origin-left"
            >
              <Progress
                value={animatedProgress}
                className="h-6"
                style={
                  {
                    "--progress-background": consensusState.consensus_reached
                      ? "hsl(142 71% 45%)"
                      : "hsl(217 91% 60%)",
                  } as React.CSSProperties
                }
              />
            </motion.div>

            {/* Threshold line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-yellow-500"
              style={{ left: `${consensusState.consensus_threshold * 100}%` }}
            >
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <Badge variant="outline" className="text-xs bg-background">
                  Threshold: {Math.round(consensusState.consensus_threshold * 100)}%
                </Badge>
              </div>
            </div>
          </div>

          {/* Status Message */}
          <AnimatePresence mode="wait">
            {consensusState.consensus_reached ? (
              <motion.div
                key="reached"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">✅</span>
                  <div>
                    <p className="font-semibold text-green-500">Consensus Achieved</p>
                    <p className="text-sm text-muted-foreground">
                      {Math.round(consensusState.weighted_consensus * 100)}% weighted agreement across all agents.
                      Autonomous action approved.
                    </p>
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="building"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">⏳</span>
                  <div>
                    <p className="font-semibold text-blue-500">Building Consensus</p>
                    <p className="text-sm text-muted-foreground">
                      Need {Math.round((consensusState.consensus_threshold - consensusState.weighted_consensus) * 100)}
                      % more for consensus. Agents continue analysis...
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Voting Details */}
        {showDetails && (
          <div className="pt-4 border-t">
            <details className="cursor-pointer">
              <summary className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                View consensus calculation details
              </summary>
              <div className="mt-3 p-3 bg-muted/50 rounded-lg font-mono text-xs space-y-1">
                <p className="font-semibold mb-2">Weighted Consensus Formula:</p>
                {consensusState.agents.map((agent) => (
                  <p key={agent.agent_type}>
                    {agent.agent_name}: {(agent.confidence * 100).toFixed(1)}% ×{" "}
                    {(agent.weight * 100).toFixed(1)}% = {(agent.confidence * agent.weight * 100).toFixed(2)}%
                  </p>
                ))}
                <p className="pt-2 border-t border-muted-foreground/20 font-bold">
                  Total Consensus ={" "}
                  {consensusState.agents
                    .reduce((sum, agent) => sum + agent.confidence * agent.weight, 0)
                    .toFixed(2)}
                  {" = "}
                  {Math.round(consensusState.weighted_consensus * 100)}%
                </p>
                <p className="pt-2 text-muted-foreground">
                  {consensusState.weighted_consensus >= consensusState.consensus_threshold
                    ? `✓ Above threshold (${Math.round(consensusState.consensus_threshold * 100)}%)`
                    : `✗ Below threshold (${Math.round(consensusState.consensus_threshold * 100)}%)`}
                </p>
              </div>
            </details>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Example usage with sample data:
 *
 * const sampleConsensus: ConsensusState = {
 *   agents: [
 *     {
 *       agent_type: "detection",
 *       agent_name: "Detection Agent",
 *       confidence: 0.94,
 *       weight: 0.2,
 *       status: "agreed",
 *       reasoning_summary: "Anomaly correlation across 143 telemetry signals"
 *     },
 *     {
 *       agent_type: "diagnosis",
 *       agent_name: "Diagnosis Agent",
 *       confidence: 0.97,
 *       weight: 0.4,
 *       status: "agreed",
 *       reasoning_summary: "Root cause identified via Bedrock AgentCore"
 *     },
 *     {
 *       agent_type: "prediction",
 *       agent_name: "Prediction Agent",
 *       confidence: 0.73,
 *       weight: 0.3,
 *       status: "voting",
 *       reasoning_summary: "Nova Act evaluating cascade probability"
 *     },
 *     {
 *       agent_type: "resolution",
 *       agent_name: "Resolution Agent",
 *       confidence: 0.91,
 *       weight: 0.1,
 *       status: "agreed",
 *       reasoning_summary: "Remediation plan validated"
 *     },
 *     {
 *       agent_type: "communication",
 *       agent_name: "Communication Agent",
 *       confidence: 0.88,
 *       weight: 0,
 *       status: "informational",
 *       reasoning_summary: "Stakeholder notifications ready (non-voting)"
 *     }
 *   ],
 *   weighted_consensus: 0.854,
 *   consensus_threshold: 0.85,
 *   consensus_reached: true,
 *   decision: "approved",
 *   timestamp: new Date()
 * };
 *
 * <ByzantineConsensusVisualization consensusState={sampleConsensus} />
 */
