/**
 * Progress Timeline Component
 * Real-time progress timeline with estimated completion times
 * Requirements: 3.3 - Display Status_Timeline with real-time progress and estimated completion times
 */

"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Clock,
  TrendingUp,
  AlertTriangle,
  Activity,
  Shield,
  Users,
  CheckCircle,
  Timer,
  Target,
  Zap,
  Calendar,
  BarChart3,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import {
  TimelineEvent,
  TimelineMetrics,
  ProgressEstimate,
  ProgressTimelineManager,
} from "../lib/progress-timeline-manager";
import { IncidentPhase } from "../lib/phase-transition-manager";
import { useProgressTimeline } from "../lib/hooks/useProgressTimeline";

const PHASE_ICONS = {
  detection: AlertTriangle,
  diagnosis: Activity,
  prediction: TrendingUp,
  resolution: Shield,
  communication: Users,
  resolved: CheckCircle,
};

const PHASE_COLORS = {
  detection: "text-orange-600 dark:text-orange-400",
  diagnosis: "text-blue-600 dark:text-blue-400",
  prediction: "text-purple-600 dark:text-purple-400",
  resolution: "text-red-600 dark:text-red-400",
  communication: "text-indigo-600 dark:text-indigo-400",
  resolved: "text-green-600 dark:text-green-400",
};

interface ProgressTimelineProps {
  showEstimates?: boolean;
  showMetrics?: boolean;
  showEvents?: boolean;
  compact?: boolean;
  className?: string;
}

const MetricsPanel = ({ metrics }: { metrics: TimelineMetrics }) => {
  const formatDuration = (ms: number) =>
    ProgressTimelineManager.formatDuration(ms);
  const formatTime = (date: Date) => ProgressTimelineManager.formatTime(date);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6"
    >
      {/* Overall Progress */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Progress
            </span>
          </div>
          <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
            {Math.round(metrics.overallProgress)}%
          </span>
        </div>
        <Progress value={metrics.overallProgress} className="h-2" />
      </div>

      {/* Elapsed Time */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Timer className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium text-green-700 dark:text-green-300">
                Elapsed
              </span>
            </div>
            <div className="text-lg font-bold text-green-600 dark:text-green-400">
              {formatDuration(metrics.elapsedTime)}
            </div>
          </div>
        </div>
      </div>

      {/* Remaining Time */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-purple-500" />
              <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
                Remaining
              </span>
            </div>
            <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
              {formatDuration(metrics.remainingTime)}
            </div>
          </div>
        </div>
      </div>

      {/* ETA */}
      <div
        className={`p-4 rounded-lg border ${
          metrics.isOnTrack
            ? "bg-gradient-to-br from-emerald-500/10 to-emerald-600/10 border-emerald-500/20"
            : "bg-gradient-to-br from-red-500/10 to-red-600/10 border-red-500/20"
        }`}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="w-4 h-4" />
              <span className="text-sm font-medium">ETA</span>
            </div>
            <div className="text-sm font-bold">
              {formatTime(metrics.estimatedCompletion)}
            </div>
            {!metrics.isOnTrack && metrics.delayMinutes > 0 && (
              <div className="text-xs text-red-600 dark:text-red-400 mt-1">
                +{Math.round(metrics.delayMinutes)}m delay
              </div>
            )}
          </div>
          <div
            className={`p-2 rounded-lg ${
              metrics.isOnTrack
                ? "bg-emerald-500/20 text-emerald-500"
                : "bg-red-500/20 text-red-500"
            }`}
          >
            <Target className="w-4 h-4" />
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const EstimatesPanel = ({ estimates }: { estimates: ProgressEstimate[] }) => {
  const formatTime = (date: Date) => ProgressTimelineManager.formatTime(date);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="mb-6"
    >
      <h4 className="text-md font-semibold mb-3 flex items-center gap-2">
        <TrendingUp className="w-4 h-4" />
        Phase Estimates
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {estimates.map((estimate, index) => {
          const Icon = PHASE_ICONS[estimate.phase];
          const colorClass = PHASE_COLORS[estimate.phase];

          return (
            <motion.div
              key={estimate.phase}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="p-3 rounded-lg border bg-card/50 backdrop-blur-sm"
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-muted ${colorClass}`}>
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className={`font-medium text-sm capitalize ${colorClass}`}
                    >
                      {estimate.phase}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {Math.round(estimate.confidence * 100)}%
                    </Badge>
                  </div>

                  <div className="text-xs text-muted-foreground">
                    ETA: {formatTime(estimate.estimatedCompletion)}
                  </div>

                  {estimate.basedOnHistoricalData && (
                    <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                      Based on history
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

const EventsTimeline = ({ events }: { events: TimelineEvent[] }) => {
  const formatTime = (date: Date) => ProgressTimelineManager.formatTime(date);

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No timeline events yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {events.map((event, index) => {
        const Icon = PHASE_ICONS[event.phase];
        const colorClass = PHASE_COLORS[event.phase];

        const getStatusIcon = () => {
          switch (event.status) {
            case "completed":
              return <CheckCircle className="w-4 h-4 text-green-500" />;
            case "failed":
              return <AlertTriangle className="w-4 h-4 text-red-500" />;
            case "in_progress":
              return <Zap className="w-4 h-4 text-blue-500 animate-pulse" />;
            default:
              return <Clock className="w-4 h-4 text-gray-500" />;
          }
        };

        const getStatusColor = () => {
          switch (event.status) {
            case "completed":
              return "border-green-500/30 bg-green-500/10";
            case "failed":
              return "border-red-500/30 bg-red-500/10";
            case "in_progress":
              return "border-blue-500/30 bg-blue-500/10";
            default:
              return "border-gray-500/30 bg-gray-500/10";
          }
        };

        return (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`relative p-4 rounded-lg border ${getStatusColor()}`}
          >
            <div className="flex items-start gap-4">
              {/* Timeline connector */}
              <div className="relative flex flex-col items-center">
                <div
                  className={`p-2 rounded-full border-2 bg-background ${colorClass}`}
                >
                  <Icon className="w-4 h-4" />
                </div>

                {index < events.length - 1 && (
                  <div className="w-0.5 h-8 bg-border mt-2" />
                )}
              </div>

              {/* Event content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <h5 className={`font-semibold text-sm ${colorClass}`}>
                    {event.title}
                  </h5>

                  <div className="flex items-center gap-2">
                    {getStatusIcon()}
                    <span className="text-xs text-muted-foreground">
                      {formatTime(event.timestamp)}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground mb-3">
                  {event.description}
                </p>

                <div className="flex items-center gap-4">
                  {/* Progress bar */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-muted-foreground">
                        Progress
                      </span>
                      <span className="text-xs font-mono">
                        {Math.round(event.progress)}%
                      </span>
                    </div>
                    <Progress value={event.progress} className="h-1.5" />
                  </div>

                  {/* Duration */}
                  {event.actualDuration && (
                    <div className="text-xs text-muted-foreground">
                      {ProgressTimelineManager.formatDuration(
                        event.actualDuration
                      )}
                    </div>
                  )}

                  {/* Confidence */}
                  {event.confidence && (
                    <Badge variant="outline" className="text-xs">
                      {Math.round(event.confidence * 100)}%
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};

export default function ProgressTimeline({
  showEstimates = true,
  showMetrics = true,
  showEvents = true,
  compact = false,
  className = "",
}: ProgressTimelineProps) {
  const { metrics, events, estimates, isActive } = useProgressTimeline();

  if (!isActive && !compact) {
    return (
      <Card className={`relative overflow-hidden ${className}`}>
        <CardContent className="p-6">
          <div className="text-center py-8 text-muted-foreground">
            <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-semibold mb-2">No Active Incident</h3>
            <p className="text-sm">
              Timeline will appear when an incident is detected
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`relative overflow-hidden ${className}`}>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          Progress Timeline
          {isActive && (
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="ml-auto flex items-center gap-2"
            >
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm text-green-600 font-medium">Live</span>
            </motion.div>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Metrics Panel */}
        {showMetrics && isActive && <MetricsPanel metrics={metrics} />}

        {/* Estimates Panel */}
        {showEstimates && estimates.length > 0 && (
          <EstimatesPanel estimates={estimates} />
        )}

        {/* Events Timeline */}
        {showEvents && (
          <div>
            <h4 className="text-md font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Timeline Events
            </h4>
            <EventsTimeline events={events} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
