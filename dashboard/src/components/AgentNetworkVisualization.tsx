/**
 * Agent Network Visualization
 *
 * Interactive network graph showing agents and their communications.
 * Uses SVG to create a force-directed graph visualization.
 *
 * Features:
 * - Agent nodes with status indicators
 * - Animated communication links
 * - Consensus formation visualization
 * - Real-time updates
 */

"use client";

import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Eye,
  Activity,
  TrendingUp,
  Wrench,
  MessageSquare,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared";

interface Agent {
  id: string;
  name: string;
  state: "idle" | "analyzing" | "reporting" | "consensus";
  position: { x: number; y: number };
  icon: React.ReactNode;
}

interface Communication {
  id: string;
  from: string;
  to: string;
  message: string;
  timestamp: number;
}

const AGENT_DEFINITIONS = [
  { id: "detection", name: "Detection", icon: Eye, color: "#3b82f6" },
  { id: "diagnosis", name: "Diagnosis", icon: Activity, color: "#8b5cf6" },
  { id: "prediction", name: "Prediction", icon: TrendingUp, color: "#06b6d4" },
  { id: "resolution", name: "Resolution", icon: Wrench, color: "#10b981" },
  { id: "communication", name: "Communication", icon: MessageSquare, color: "#f59e0b" },
];

export function AgentNetworkVisualization({
  activeIncident = false,
}: {
  activeIncident?: boolean;
}) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [communications, setCommunications] = useState<Communication[]>([]);
  const [consensusForming, setConsensusForming] = useState(false);

  // Initialize agent positions in a pentagon
  useEffect(() => {
    const centerX = 400;
    const centerY = 200;
    const radius = 120;

    const initialAgents = AGENT_DEFINITIONS.map((def, index) => {
      const angle = (index / AGENT_DEFINITIONS.length) * 2 * Math.PI - Math.PI / 2;
      return {
        id: def.id,
        name: def.name,
        state: "idle" as const,
        position: {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        },
        icon: React.createElement(def.icon, { className: "w-5 h-5" }),
      };
    });

    setAgents(initialAgents);
  }, []);

  // Simulate agent activity when incident is active
  useEffect(() => {
    if (!activeIncident) {
      setAgents((prev) =>
        prev.map((agent) => ({ ...agent, state: "idle" as const }))
      );
      setCommunications([]);
      setConsensusForming(false);
      return;
    }

    // Activate agents in sequence
    const activationSequence = async () => {
      // Detection activates first
      await new Promise((resolve) => setTimeout(resolve, 500));
      setAgents((prev) =>
        prev.map((a) =>
          a.id === "detection" ? { ...a, state: "analyzing" as const } : a
        )
      );

      // Detection reports to others
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setCommunications([
        {
          id: "comm-1",
          from: "detection",
          to: "diagnosis",
          message: "Anomaly detected",
          timestamp: Date.now(),
        },
      ]);

      setAgents((prev) =>
        prev.map((a) =>
          a.id === "detection"
            ? { ...a, state: "reporting" as const }
            : a.id === "diagnosis"
            ? { ...a, state: "analyzing" as const }
            : a
        )
      );

      // Diagnosis and prediction analyze
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setCommunications((prev) => [
        ...prev,
        {
          id: "comm-2",
          from: "diagnosis",
          to: "prediction",
          message: "Root cause found",
          timestamp: Date.now(),
        },
      ]);

      setAgents((prev) =>
        prev.map((a) =>
          a.id === "prediction" ? { ...a, state: "analyzing" as const } : a
        )
      );

      // All agents converge for consensus
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setConsensusForming(true);
      setAgents((prev) =>
        prev.map((a) => ({ ...a, state: "consensus" as const }))
      );

      // Consensus reached
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setAgents((prev) =>
        prev.map((a) =>
          a.id === "resolution" ? { ...a, state: "analyzing" as const } : a
        )
      );
      setConsensusForming(false);

      // Resolution takes action
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setCommunications((prev) => [
        ...prev,
        {
          id: "comm-3",
          from: "resolution",
          to: "communication",
          message: "Fix deployed",
          timestamp: Date.now(),
        },
      ]);

      setAgents((prev) =>
        prev.map((a) =>
          a.id === "communication"
            ? { ...a, state: "reporting" as const }
            : a
        )
      );

      // Complete
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setAgents((prev) =>
        prev.map((a) => ({ ...a, state: "idle" as const }))
      );
      setCommunications([]);
    };

    activationSequence();
  }, [activeIncident]);

  // Calculate consensus ring center
  const centerX = 400;
  const centerY = 200;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Agent Network (Live)
        </CardTitle>
        <p className="text-xs text-slate-400 mt-1">
          Real-time visualization of agent communication and consensus
        </p>
      </CardHeader>
      <CardContent>
        <div className="relative bg-slate-900/50 rounded-lg p-4">
          <svg
            width="800"
            height="400"
            viewBox="0 0 800 400"
            className="w-full h-auto"
          >
            {/* Consensus ring */}
            <AnimatePresence>
              {consensusForming && (
                <motion.circle
                  key="consensus-ring"
                  cx={centerX}
                  cy={centerY}
                  r={150}
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2"
                  strokeDasharray="10 5"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{
                    opacity: [0.3, 0.6, 0.3],
                    scale: [0.95, 1.05, 0.95],
                    rotate: [0, 360],
                  }}
                  exit={{ opacity: 0 }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                />
              )}
            </AnimatePresence>

            {/* Communication lines */}
            <AnimatePresence>
              {communications.map((comm) => {
                const fromAgent = agents.find((a) => a.id === comm.from);
                const toAgent = agents.find((a) => a.id === comm.to);

                if (!fromAgent || !toAgent) return null;

                return (
                  <motion.g key={comm.id}>
                    <motion.line
                      x1={fromAgent.position.x}
                      y1={fromAgent.position.y}
                      x2={toAgent.position.x}
                      y2={toAgent.position.y}
                      stroke="#3b82f6"
                      strokeWidth="2"
                      initial={{ pathLength: 0, opacity: 0 }}
                      animate={{ pathLength: 1, opacity: 0.6 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.5 }}
                    />
                    <motion.circle
                      initial={{ opacity: 0 }}
                      animate={{
                        cx: [fromAgent.position.x, toAgent.position.x],
                        cy: [fromAgent.position.y, toAgent.position.y],
                        opacity: [0, 1, 0],
                      }}
                      r="4"
                      fill="#3b82f6"
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                    />
                  </motion.g>
                );
              })}
            </AnimatePresence>

            {/* Agent nodes */}
            {agents.map((agent) => {
              const agentDef = AGENT_DEFINITIONS.find((d) => d.id === agent.id);
              const color = agentDef?.color || "#64748b";

              return (
                <g key={agent.id}>
                  {/* Pulsing ring for active agents */}
                  {agent.state !== "idle" && (
                    <motion.circle
                      cx={agent.position.x}
                      cy={agent.position.y}
                      r={25}
                      fill="none"
                      stroke={color}
                      strokeWidth="2"
                      initial={{ opacity: 0, scale: 1 }}
                      animate={{
                        opacity: [0.3, 0, 0.3],
                        scale: [1, 1.5, 1],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut",
                      }}
                    />
                  )}

                  {/* Main node circle */}
                  <motion.circle
                    cx={agent.position.x}
                    cy={agent.position.y}
                    r={20}
                    fill={agent.state === "idle" ? "#1e293b" : color}
                    stroke={color}
                    strokeWidth="3"
                    initial={{ scale: 0 }}
                    animate={{
                      scale: 1,
                      fill:
                        agent.state === "consensus"
                          ? "#10b981"
                          : agent.state === "idle"
                          ? "#1e293b"
                          : color,
                    }}
                    transition={{ duration: 0.3 }}
                  />

                  {/* Agent label */}
                  <text
                    x={agent.position.x}
                    y={agent.position.y + 40}
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize="12"
                    fontWeight="600"
                  >
                    {agent.name}
                  </text>

                  {/* State indicator */}
                  {agent.state !== "idle" && (
                    <text
                      x={agent.position.x}
                      y={agent.position.y + 55}
                      textAnchor="middle"
                      fill={color}
                      fontSize="10"
                      fontStyle="italic"
                    >
                      {agent.state}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="mt-4 flex items-center justify-center gap-6 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-slate-800 border-2 border-slate-500" />
              <span className="text-slate-400">Idle</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500 border-2 border-blue-500" />
              <span className="text-slate-400">Active</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500 border-2 border-green-500" />
              <span className="text-slate-400">Consensus</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
