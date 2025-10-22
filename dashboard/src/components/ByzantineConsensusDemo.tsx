"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
  Badge,
} from "./shared";

interface Agent {
  name: string;
  weight: number;
  confidence: number;
  status: "active" | "compromised" | "offline";
  contribution: number;
}

interface ByzantineConsensusDemoProps {
  className?: string;
}

export const ByzantineConsensusDemo: React.FC<ByzantineConsensusDemoProps> = ({
  className,
}) => {
  const [agents, setAgents] = useState<Agent[]>([
    {
      name: "Detection",
      weight: 0.2,
      confidence: 0.92,
      status: "active",
      contribution: 0.184,
    },
    {
      name: "Diagnosis",
      weight: 0.4,
      confidence: 0.94,
      status: "active",
      contribution: 0.376,
    },
    {
      name: "Prediction",
      weight: 0.3,
      confidence: 0.85,
      status: "active",
      contribution: 0.255,
    },
    {
      name: "Resolution",
      weight: 0.1,
      confidence: 0.9,
      status: "active",
      contribution: 0.09,
    },
  ]);

  const [phase, setPhase] = useState<
    "initial" | "compromise" | "adaptation" | "success"
  >("initial");
  const [totalConsensus, setTotalConsensus] = useState(0.905);
  const [threshold] = useState(0.7);

  useEffect(() => {
    // Simulate Byzantine fault tolerance demo
    const demoSequence = async () => {
      // Phase 1: Initial consensus (5 seconds)
      await new Promise((resolve) => setTimeout(resolve, 5000));

      // Phase 2: Compromise Prediction agent (6 seconds)
      setPhase("compromise");
      setAgents((prev) =>
        prev.map((agent) =>
          agent.name === "Prediction"
            ? {
                ...agent,
                status: "compromised",
                confidence: 0.15,
                contribution: 0.045,
              }
            : agent
        )
      );
      setTotalConsensus(0.65); // Below threshold temporarily

      await new Promise((resolve) => setTimeout(resolve, 6000));

      // Phase 3: System adaptation (7 seconds)
      setPhase("adaptation");
      // System adapts by discounting compromised agent
      setTotalConsensus(0.72); // Above threshold with remaining agents

      await new Promise((resolve) => setTimeout(resolve, 7000));

      // Phase 4: Success (ongoing)
      setPhase("success");
    };

    demoSequence();
  }, []); // Empty dependency array is intentional for one-time demo sequence

  const getStatusColor = (status: Agent["status"]) => {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "compromised":
        return "bg-red-500";
      case "offline":
        return "bg-gray-500";
      default:
        return "bg-gray-500";
    }
  };

  const getPhaseDescription = () => {
    switch (phase) {
      case "initial":
        return "All agents participating in consensus building";
      case "compromise":
        return "SIMULATION: Prediction Agent compromised - providing conflicting data";
      case "adaptation":
        return "Byzantine consensus adapting - discounting compromised agent";
      case "success":
        return "Consensus achieved despite compromised agent - fault tolerance proven";
      default:
        return "";
    }
  };

  return (
    <Card className={`card-glass ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          🛡️ Byzantine Fault Tolerance Demo
          <Badge
            variant={totalConsensus >= threshold ? "default" : "destructive"}
          >
            {totalConsensus >= threshold
              ? "Consensus Achieved"
              : "Below Threshold"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Phase Description */}
        <div className="bg-slate-700/20 backdrop-blur-sm rounded-lg p-4">
          <h4 className="font-semibold mb-2">
            Current Phase: {phase.charAt(0).toUpperCase() + phase.slice(1)}
          </h4>
          <p className="text-sm text-status-neutral">{getPhaseDescription()}</p>
        </div>

        {/* Consensus Progress */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">
              Total Weighted Consensus
            </span>
            <span
              className={`font-mono text-lg ${
                totalConsensus >= threshold ? "text-green-400" : "text-red-400"
              }`}
            >
              {(totalConsensus * 100).toFixed(1)}%
            </span>
          </div>
          <Progress value={totalConsensus * 100} className="h-3" />
          <div className="flex justify-between text-xs text-status-neutral">
            <span>Threshold: {threshold * 100}%</span>
            <span
              className={
                totalConsensus >= threshold ? "text-green-400" : "text-red-400"
              }
            >
              {totalConsensus >= threshold
                ? "Autonomous Action Approved"
                : "Human Escalation Required"}
            </span>
          </div>
        </div>

        {/* Agent Status Grid */}
        <div className="grid grid-cols-2 gap-4">
          {agents.map((agent) => (
            <div
              key={agent.name}
              className={`p-4 rounded-lg border-2 transition-all ${
                agent.status === "compromised"
                  ? "border-red-500 bg-red-500/10"
                  : agent.status === "active"
                  ? "border-green-500 bg-green-500/10"
                  : "border-gray-500 bg-gray-500/10"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold">{agent.name}</span>
                <div
                  className={`w-3 h-3 rounded-full ${getStatusColor(
                    agent.status
                  )}`}
                />
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Weight:</span>
                  <span className="font-mono">{agent.weight}</span>
                </div>
                <div className="flex justify-between">
                  <span>Confidence:</span>
                  <span
                    className={`font-mono ${
                      agent.status === "compromised"
                        ? "text-red-400"
                        : "text-green-400"
                    }`}
                  >
                    {(agent.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Contribution:</span>
                  <span
                    className={`font-mono ${
                      agent.status === "compromised"
                        ? "text-red-400"
                        : "text-blue-400"
                    }`}
                  >
                    {(agent.contribution * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {agent.status === "compromised" && (
                <div className="mt-2 text-xs text-red-400 bg-red-500/20 p-2 rounded">
                  ⚠️ Agent compromised - contribution discounted
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Fault Tolerance Explanation */}
        <div className="bg-blue-500/20 rounded-lg p-4">
          <h4 className="font-semibold text-blue-400 mb-2">
            Byzantine Fault Tolerance
          </h4>
          <div className="text-sm space-y-1">
            <p>• System can handle up to 33% compromised agents</p>
            <p>
              • Weighted consensus ensures critical agents (Diagnosis: 40%) have
              higher influence
            </p>
            <p>• Automatic detection and isolation of compromised agents</p>
            <p>• Graceful degradation maintains autonomous operation</p>
          </div>
        </div>

        {/* Success Metrics */}
        {phase === "success" && (
          <div className="bg-green-500/20 rounded-lg p-4">
            <h4 className="font-semibold text-green-400 mb-2">
              ✅ Fault Tolerance Proven
            </h4>
            <div className="text-sm space-y-1">
              <p>
                • Consensus maintained: {(totalConsensus * 100).toFixed(1)}%
                (above 70% threshold)
              </p>
              <p>• Compromised agent isolated and discounted</p>
              <p>• Autonomous resolution proceeding with high confidence</p>
              <p>• Zero human intervention required</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ByzantineConsensusDemo;
