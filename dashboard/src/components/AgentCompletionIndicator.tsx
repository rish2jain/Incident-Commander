/**
 * Agent Completion Indicator Component
 * Visual feedback for agent task completion with animations
 * Requirements: 3.2 - Show completion animations and success indicators when agents finish tasks
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
  Trophy,
  Star,
  Target,
} from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import {
  AgentType,
  AGENT_CONFIGS,
  AgentCompletionEvent,
} from "../lib/agent-completion-manager";
import { useAgentCompletions } from "../lib/hooks/useAgentCompletions";

const AGENT_ICONS = {
  detection: AlertTriangle,
  diagnosis: Activity,
  prediction: TrendingUp,
  resolution: Shield,
  communication: Users,
};

interface AgentCompletionIndicatorProps {
  showRecentCompletions?: boolean;
  showStats?: boolean;
  maxRecentItems?: number;
  className?: string;
}

const SuccessAnimation = ({
  agentType,
  isVisible,
}: {
  agentType: AgentType;
  isVisible: boolean;
}) => {
  const config = AGENT_CONFIGS[agentType];
  const Icon = AGENT_ICONS[agentType];

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.5, y: 50 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: -20 }}
          transition={{
            type: "spring",
            stiffness: 400,
            damping: 25,
            duration: 0.6,
          }}
          className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50"
        >
          <div
            className={`
              relative p-8 rounded-2xl border-2 backdrop-blur-xl
              ${config.bgColor} ${config.borderColor}
              shadow-2xl shadow-current/20
            `}
          >
            {/* Background glow effect */}
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className={`absolute inset-0 rounded-2xl ${config.bgColor} blur-xl`}
            />

            {/* Main content */}
            <div className="relative flex flex-col items-center gap-4">
              {/* Agent icon with success animation */}
              <motion.div
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.2, 1],
                }}
                transition={{
                  rotate: { duration: 1, ease: "easeInOut" },
                  scale: { duration: 0.8, repeat: Infinity, ease: "easeInOut" },
                }}
                className={`
                  relative p-4 rounded-full border-2
                  ${config.bgColor} ${config.borderColor} ${config.color}
                `}
              >
                <Icon className="w-8 h-8" />

                {/* Success checkmark overlay */}
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ delay: 0.3, type: "spring", stiffness: 400 }}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
                >
                  <CheckCircle className="w-4 h-4 text-white" />
                </motion.div>
              </motion.div>

              {/* Success message */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-center"
              >
                <h3 className={`text-xl font-bold ${config.color} mb-1`}>
                  Task Complete!
                </h3>
                <p className="text-sm text-muted-foreground">
                  {config.name} finished successfully
                </p>
              </motion.div>

              {/* Celebration particles */}
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{
                    opacity: 0,
                    scale: 0,
                    x: 0,
                    y: 0,
                  }}
                  animate={{
                    opacity: [0, 1, 0],
                    scale: [0, 1, 0],
                    x: [0, (Math.random() - 0.5) * 200],
                    y: [0, (Math.random() - 0.5) * 200],
                  }}
                  transition={{
                    duration: 1.5,
                    delay: 0.5 + i * 0.1,
                    ease: "easeOut",
                  }}
                  className="absolute w-2 h-2 bg-yellow-400 rounded-full"
                />
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const CompletionItem = ({
  completion,
  index,
}: {
  completion: AgentCompletionEvent;
  index: number;
}) => {
  const config = AGENT_CONFIGS[completion.agentType];
  const Icon = AGENT_ICONS[completion.agentType];

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return "text-gray-500";
    if (confidence >= 0.9) return "text-green-600";
    if (confidence >= 0.75) return "text-blue-600";
    if (confidence >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      transition={{
        delay: index * 0.1,
        type: "spring",
        stiffness: 300,
        damping: 25,
      }}
      className={`
        relative p-4 rounded-lg border transition-all duration-300
        ${config.bgColor} ${config.borderColor}
        hover:shadow-lg hover:shadow-current/10
      `}
    >
      <div className="flex items-start gap-3">
        {/* Agent Icon */}
        <div
          className={`
            relative flex items-center justify-center w-10 h-10 rounded-full border-2
            ${config.bgColor} ${config.borderColor} ${config.color}
          `}
        >
          <Icon className="w-5 h-5" />

          {/* Success/Failure indicator */}
          <div
            className={`
              absolute -top-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center
              ${
                completion.success
                  ? "bg-green-500 text-white"
                  : "bg-red-500 text-white"
              }
            `}
          >
            {completion.success ? (
              <CheckCircle className="w-3 h-3" />
            ) : (
              <XCircle className="w-3 h-3" />
            )}
          </div>
        </div>

        {/* Completion Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className={`font-semibold text-sm ${config.color}`}>
              {config.name}
            </h4>
            <span className="text-xs text-muted-foreground">
              {completion.timestamp.toLocaleTimeString()}
            </span>
          </div>

          <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
            {completion.action.title}
          </p>

          <div className="flex items-center gap-3 text-xs">
            {/* Completion Time */}
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{formatTime(completion.completionTime)}</span>
            </div>

            {/* Confidence Level */}
            {completion.confidence && (
              <div className="flex items-center gap-1">
                <Target className="w-3 h-3" />
                <span className={getConfidenceColor(completion.confidence)}>
                  {Math.round(completion.confidence * 100)}%
                </span>
              </div>
            )}

            {/* Success Badge */}
            <Badge
              variant={completion.success ? "default" : "destructive"}
              className="text-xs"
            >
              {completion.success ? "Success" : "Failed"}
            </Badge>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const StatsPanel = ({
  stats,
}: {
  stats: {
    totalCompletions: number;
    successRate: number;
    averageCompletionTime: number;
    agentPerformance: Record<
      AgentType,
      { completions: number; successRate: number; avgTime: number }
    >;
  };
}) => {
  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6"
    >
      {/* Total Completions */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {stats.totalCompletions}
            </div>
            <div className="text-sm text-blue-700 dark:text-blue-300">
              Total Completions
            </div>
          </div>
          <Trophy className="w-6 h-6 text-blue-500" />
        </div>
      </div>

      {/* Success Rate */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {Math.round(stats.successRate * 100)}%
            </div>
            <div className="text-sm text-green-700 dark:text-green-300">
              Success Rate
            </div>
          </div>
          <Star className="w-6 h-6 text-green-500" />
        </div>
      </div>

      {/* Average Time */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {formatTime(stats.averageCompletionTime)}
            </div>
            <div className="text-sm text-purple-700 dark:text-purple-300">
              Avg. Time
            </div>
          </div>
          <Zap className="w-6 h-6 text-purple-500" />
        </div>
      </div>
    </motion.div>
  );
};

export default function AgentCompletionIndicator({
  showRecentCompletions = true,
  showStats = true,
  maxRecentItems = 5,
  className = "",
}: AgentCompletionIndicatorProps) {
  const {
    recentCompletions,
    completionStats,
    isShowingCompletion,
    lastCompletion,
  } = useAgentCompletions(undefined, maxRecentItems);

  return (
    <>
      {/* Success Animation Overlay */}
      {lastCompletion && (
        <SuccessAnimation
          agentType={lastCompletion.agentType}
          isVisible={isShowingCompletion}
        />
      )}

      {/* Main Component */}
      <Card className={`relative overflow-hidden ${className}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              Agent Completions
            </h3>

            {isShowingCompletion && lastCompletion && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-2"
              >
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-green-600 font-medium">
                  {AGENT_CONFIGS[lastCompletion.agentType].name} completed!
                </span>
              </motion.div>
            )}
          </div>

          {/* Statistics Panel */}
          {showStats && completionStats.totalCompletions > 0 && (
            <StatsPanel stats={completionStats} />
          )}

          {/* Recent Completions */}
          {showRecentCompletions && (
            <div>
              <h4 className="text-md font-semibold mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Recent Completions
              </h4>

              {recentCompletions.length > 0 ? (
                <div className="space-y-3">
                  {recentCompletions.map((completion, index) => (
                    <CompletionItem
                      key={`${completion.timestamp.getTime()}-${
                        completion.agentType
                      }`}
                      completion={completion}
                      index={index}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No agent completions yet</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
