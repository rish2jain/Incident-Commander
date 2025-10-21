/**
 * Phase Transition Indicator Component
 * Visual component for displaying smooth phase transitions
 * Requirements: 3.1 - Add visual transitions between incident phases
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
  Clock,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import {
  IncidentPhase,
  PHASE_CONFIGS,
  PHASE_ORDER,
  phaseTransitionVariants,
  phaseIndicatorVariants,
  phaseProgressVariants,
} from "../lib/phase-transition-manager";
import { usePhaseTransitions } from "../lib/hooks/usePhaseTransitions";

const PHASE_ICONS = {
  detection: AlertTriangle,
  diagnosis: Activity,
  prediction: TrendingUp,
  resolution: Shield,
  communication: Users,
  resolved: CheckCircle,
};

interface PhaseTransitionIndicatorProps {
  showProgress?: boolean;
  showTransitionHistory?: boolean;
  compact?: boolean;
  className?: string;
}

const PhaseIndicator = ({
  phase,
  isActive,
  isCompleted,
  progress,
  compact = false,
}: {
  phase: IncidentPhase;
  isActive: boolean;
  isCompleted: boolean;
  progress: number;
  compact?: boolean;
}) => {
  const config = PHASE_CONFIGS[phase];
  const Icon = PHASE_ICONS[phase];

  const getVariant = () => {
    if (isCompleted) return "completed";
    if (isActive) return "active";
    return "inactive";
  };

  return (
    <motion.div
      variants={phaseIndicatorVariants}
      animate={getVariant()}
      className="relative"
    >
      <div
        className={`
          relative flex items-center gap-3 p-4 rounded-xl border-2 transition-all duration-300
          ${config.bgColor} ${config.borderColor}
          ${isActive ? "shadow-lg shadow-current/20" : ""}
          ${isCompleted ? "bg-green-500/10 border-green-500/30" : ""}
        `}
      >
        {/* Phase Icon */}
        <div
          className={`
            relative flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-300
            ${
              isCompleted
                ? "bg-green-500/20 border-green-500 text-green-600"
                : isActive
                ? `${config.bgColor} ${config.borderColor} ${config.color}`
                : "bg-muted border-muted-foreground/30 text-muted-foreground"
            }
          `}
        >
          <Icon className="w-5 h-5" />

          {/* Active pulse animation */}
          {isActive && (
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
              className={`absolute inset-0 rounded-full border-2 ${config.borderColor}`}
            />
          )}
        </div>

        {/* Phase Info */}
        {!compact && (
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <span
                className={`font-semibold text-sm ${
                  isCompleted
                    ? "text-green-600 dark:text-green-400"
                    : isActive
                    ? config.color
                    : "text-muted-foreground"
                }`}
              >
                {config.label}
              </span>
              <span
                className={`text-xs font-mono ${
                  isCompleted
                    ? "text-green-600 dark:text-green-400"
                    : isActive
                    ? config.color
                    : "text-muted-foreground"
                }`}
              >
                {Math.round(progress)}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="relative h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                variants={phaseProgressVariants}
                animate="animate"
                custom={progress}
                className={`h-full rounded-full ${
                  isCompleted
                    ? "bg-green-500"
                    : isActive
                    ? "bg-current"
                    : "bg-muted-foreground/50"
                }`}
                style={{
                  color: isActive
                    ? config.color.split(" ")[0].replace("text-", "")
                    : undefined,
                }}
              />

              {/* Active shimmer effect */}
              {isActive && progress > 0 && progress < 100 && (
                <motion.div
                  animate={{ x: ["-100%", "100%"] }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="absolute top-0 left-0 h-full w-1/3 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                />
              )}
            </div>

            {/* Phase Description */}
            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
              {config.description}
            </p>
          </div>
        )}

        {/* Completion Checkmark */}
        {isCompleted && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 20 }}
            className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
          >
            <CheckCircle className="w-4 h-4 text-white" />
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

const TransitionHistory = ({
  transitions,
}: {
  transitions: Array<{
    from: IncidentPhase | null;
    to: IncidentPhase;
    timestamp: Date;
    duration: number;
  }>;
}) => {
  const recentTransitions = transitions.slice(-3); // Show last 3 transitions

  if (recentTransitions.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 p-4 rounded-lg bg-muted/50 border border-border/50"
    >
      <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
        <Clock className="w-4 h-4" />
        Recent Transitions
      </h4>

      <div className="space-y-2">
        {recentTransitions.map((transition, index) => (
          <motion.div
            key={`${transition.timestamp.getTime()}-${index}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-center gap-3 text-xs"
          >
            <div className="flex items-center gap-2">
              {transition.from && (
                <>
                  <Badge variant="outline" className="text-xs">
                    {PHASE_CONFIGS[transition.from].label}
                  </Badge>
                  <ArrowRight className="w-3 h-3 text-muted-foreground" />
                </>
              )}
              <Badge className="text-xs">
                {PHASE_CONFIGS[transition.to].label}
              </Badge>
            </div>

            <span className="text-muted-foreground ml-auto">
              {transition.timestamp.toLocaleTimeString()}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default function PhaseTransitionIndicator({
  showProgress = true,
  showTransitionHistory = false,
  compact = false,
  className = "",
}: PhaseTransitionIndicatorProps) {
  const {
    currentPhase,
    transitionHistory,
    getPhaseProgress,
    isPhaseActive,
    isPhaseCompleted,
    isTransitioning,
    lastTransition,
  } = usePhaseTransitions();

  return (
    <Card className={`relative overflow-hidden ${className}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            Incident Phase Progress
          </h3>

          {isTransitioning && lastTransition && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="flex items-center gap-2"
            >
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              <span className="text-sm text-primary font-medium">
                Transitioning to {PHASE_CONFIGS[lastTransition.to].label}
              </span>
            </motion.div>
          )}
        </div>

        {/* Phase Indicators */}
        <div className={`space-y-4 ${compact ? "space-y-2" : ""}`}>
          <AnimatePresence mode="wait">
            {PHASE_ORDER.map((phase, index) => {
              const progress = getPhaseProgress(phase);
              const isActive = isPhaseActive(phase);
              const isCompleted = isPhaseCompleted(phase);

              return (
                <motion.div
                  key={phase}
                  variants={phaseTransitionVariants}
                  initial="initial"
                  animate="enter"
                  exit="exit"
                  transition={{ delay: index * 0.1 }}
                  className="relative"
                >
                  <PhaseIndicator
                    phase={phase}
                    isActive={isActive}
                    isCompleted={isCompleted}
                    progress={progress}
                    compact={compact}
                  />

                  {/* Connection Line */}
                  {index < PHASE_ORDER.length - 1 && !compact && (
                    <div className="flex justify-center py-2">
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{
                          height: 20,
                          opacity:
                            isCompleted ||
                            index <
                              PHASE_ORDER.findIndex((p) => isPhaseActive(p))
                              ? 1
                              : 0.3,
                        }}
                        transition={{ delay: (index + 1) * 0.1 }}
                        className={`w-0.5 rounded-full transition-colors duration-300 ${
                          isCompleted ||
                          index < PHASE_ORDER.findIndex((p) => isPhaseActive(p))
                            ? "bg-green-500"
                            : "bg-muted-foreground/30"
                        }`}
                      />
                    </div>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* Overall Progress */}
        {showProgress && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mt-6 pt-4 border-t border-border/50"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-foreground">
                Overall Progress
              </span>
              <span className="text-sm font-mono text-primary">
                {Math.round(
                  PHASE_ORDER.reduce(
                    (sum, phase) => sum + getPhaseProgress(phase),
                    0
                  ) / PHASE_ORDER.length
                )}
                %
              </span>
            </div>

            <div className="relative h-3 bg-muted rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${
                    PHASE_ORDER.reduce(
                      (sum, phase) => sum + getPhaseProgress(phase),
                      0
                    ) / PHASE_ORDER.length
                  }%`,
                }}
                transition={{ duration: 1.2, ease: "easeOut" }}
                className="h-full bg-gradient-to-r from-primary to-green-500 rounded-full"
              />
            </div>
          </motion.div>
        )}

        {/* Transition History */}
        {showTransitionHistory && (
          <TransitionHistory transitions={transitionHistory} />
        )}
      </CardContent>
    </Card>
  );
}
