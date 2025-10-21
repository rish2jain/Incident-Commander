"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { formatDuration } from "../lib/utils/time";
import {
  AlertTriangle,
  Clock,
  TrendingUp,
  Users,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Shield,
  Trophy,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { useIncidentStatus } from "../lib/hooks/useIncidentStatus";

interface Service {
  name: string;
  status: "operational" | "degraded" | "down";
  impact: string;
}

interface Metric {
  label: string;
  value: string;
  change: number;
  icon: React.ReactNode;
}

interface IncidentStatusPanelProps {
  incidentId?: string;
  title?: string;
  severity?: "critical" | "high" | "medium" | "low";
  startTime?: Date;
  affectedServices?: Service[];
  description?: string;
  useRealStatus?: boolean; // Whether to use real incident status from tracker
  showOverview?: boolean; // Whether to show the incident overview panel
  overviewData?: {
    activeIncidents: number;
    resolvedIncidents: number;
    totalIncidents: number;
    recentResolution?: {
      id: string;
      title: string;
      resolutionTime: number;
      timestamp: Date;
    } | null;
  };
}

const IncidentOverviewPanel = ({
  activeIncidents = 0,
  resolvedIncidents = 0,
  totalIncidents = 0,
  recentResolution,
  showRecentResolution = false,
}: {
  activeIncidents?: number;
  resolvedIncidents?: number;
  totalIncidents?: number;
  recentResolution?: {
    id: string;
    title: string;
    resolutionTime: number;
    timestamp: Date;
  } | null;
  showRecentResolution?: boolean;
}) => {
  const [showResolved, setShowResolved] = useState(showRecentResolution);

  // Auto-hide resolved status after 30 seconds (Requirements 2.5)
  useEffect(() => {
    if (showRecentResolution && recentResolution) {
      setShowResolved(true);
      const timer = setTimeout(() => {
        setShowResolved(false);
      }, 30000); // 30 seconds

      return () => clearTimeout(timer);
    }
  }, [showRecentResolution, recentResolution]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="mb-6"
    >
      <Card className="p-6 bg-card/50 backdrop-blur-sm border-border/50">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          Incident Overview
        </h3>

        {/* Recent Resolution Alert - Requirements 2.4, 2.5 */}
        <AnimatePresence>
          {showResolved && recentResolution && (
            <motion.div
              initial={{ opacity: 0, height: 0, y: -10 }}
              animate={{ opacity: 1, height: "auto", y: 0 }}
              exit={{ opacity: 0, height: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="mb-4 p-4 rounded-lg bg-green-500/10 border border-green-500/30"
            >
              <div className="flex items-center gap-3">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, ease: "easeInOut" }}
                >
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </motion.div>
                <div className="flex-1">
                  <div className="font-medium text-green-600 dark:text-green-400">
                    Incident Recently Resolved
                  </div>
                  <div className="text-sm text-green-700 dark:text-green-300">
                    {recentResolution.title} - Resolved in{" "}
                    {formatDuration(recentResolution.resolutionTime)}
                  </div>
                  <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                    {recentResolution.timestamp.toLocaleTimeString()}
                  </div>
                </div>
                <button
                  onClick={() => setShowResolved(false)}
                  className="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Incident Statistics Grid - Requirements 2.4 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Active Incidents */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="relative overflow-hidden rounded-xl p-4 bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {activeIncidents}
                </div>
                <div className="text-sm text-orange-700 dark:text-orange-300 font-medium">
                  Active Incidents
                </div>
              </div>
              <div className="p-2 rounded-lg bg-orange-500/20">
                <AlertTriangle className="w-6 h-6 text-orange-500" />
              </div>
            </div>
            {activeIncidents > 0 && (
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute top-2 right-2 w-2 h-2 bg-orange-500 rounded-full"
              />
            )}
          </motion.div>

          {/* Resolved Incidents */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="relative overflow-hidden rounded-xl p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {resolvedIncidents}
                </div>
                <div className="text-sm text-green-700 dark:text-green-300 font-medium">
                  Resolved Today
                </div>
              </div>
              <div className="p-2 rounded-lg bg-green-500/20">
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
            </div>
          </motion.div>

          {/* Total Incidents */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="relative overflow-hidden rounded-xl p-4 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {totalIncidents}
                </div>
                <div className="text-sm text-blue-700 dark:text-blue-300 font-medium">
                  Total Incidents
                </div>
              </div>
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Activity className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </motion.div>
        </div>

        {/* Resolution Rate */}
        {totalIncidents > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mt-4 p-4 rounded-lg bg-muted/50"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-muted-foreground">
                Resolution Rate
              </span>
              <span className="text-sm font-mono text-primary">
                {Math.round((resolvedIncidents / totalIncidents) * 100)}%
              </span>
            </div>
            <div className="relative h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${(resolvedIncidents / totalIncidents) * 100}%`,
                }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
              />
            </div>
          </motion.div>
        )}
      </Card>
    </motion.div>
  );
};

const ProgressIndicator = ({
  phaseProgress,
  currentPhase,
  isActive,
}: {
  phaseProgress: Record<string, number>;
  currentPhase: string | null;
  isActive: boolean;
}) => {
  const phases = [
    { key: "detection", label: "Detection", icon: AlertTriangle },
    { key: "diagnosis", label: "Diagnosis", icon: Activity },
    { key: "prediction", label: "Prediction", icon: TrendingUp },
    { key: "resolution", label: "Resolution", icon: Shield },
    { key: "communication", label: "Communication", icon: Users },
  ];

  if (!isActive) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="mb-6"
    >
      <Card className="p-6 bg-card/50 backdrop-blur-sm border-border/50">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          Incident Resolution Progress
        </h3>

        <div className="space-y-4">
          {phases.map((phase, index) => {
            const progress = phaseProgress[phase.key] || 0;
            const isCurrentPhase = currentPhase === phase.key;
            const isCompleted = progress === 100;
            const isActivePhase = progress > 0 && progress < 100;

            return (
              <motion.div
                key={phase.key}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                <div className="flex items-center gap-4">
                  {/* Phase Icon */}
                  <div
                    className={`relative flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-300 ${
                      isCompleted
                        ? "bg-green-500/20 border-green-500 text-green-600"
                        : isCurrentPhase
                        ? "bg-primary/20 border-primary text-primary animate-pulse"
                        : "bg-muted border-muted-foreground/30 text-muted-foreground"
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <phase.icon className="w-5 h-5" />
                    )}

                    {isCurrentPhase && (
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="absolute inset-0 rounded-full border-2 border-primary/50"
                      />
                    )}
                  </div>

                  {/* Phase Info */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span
                        className={`font-medium ${
                          isCompleted
                            ? "text-green-600 dark:text-green-400"
                            : isCurrentPhase
                            ? "text-primary"
                            : "text-muted-foreground"
                        }`}
                      >
                        {phase.label}
                      </span>
                      <span
                        className={`text-sm font-mono ${
                          isCompleted
                            ? "text-green-600 dark:text-green-400"
                            : isCurrentPhase
                            ? "text-primary"
                            : "text-muted-foreground"
                        }`}
                      >
                        {Math.round(progress)}%
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="relative h-2 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                        className={`h-full rounded-full ${
                          isCompleted
                            ? "bg-green-500"
                            : isCurrentPhase
                            ? "bg-primary"
                            : "bg-muted-foreground/50"
                        }`}
                      />

                      {isActivePhase && (
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
                  </div>
                </div>

                {/* Connection Line */}
                {index < phases.length - 1 && (
                  <div
                    className={`absolute left-5 top-10 w-0.5 h-6 transition-colors duration-300 ${
                      phaseProgress[phases[index + 1].key] > 0
                        ? "bg-green-500"
                        : "bg-muted-foreground/30"
                    }`}
                  />
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Overall Progress */}
        <div className="mt-6 pt-4 border-t border-border/50">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-foreground">
              Overall Progress
            </span>
            <span className="text-sm font-mono text-primary">
              {Math.round(
                Object.values(phaseProgress).reduce(
                  (sum, progress) => sum + progress,
                  0
                ) / 5
              )}
              %
            </span>
          </div>
          <div className="relative h-3 bg-muted rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{
                width: `${
                  Object.values(phaseProgress).reduce(
                    (sum, progress) => sum + progress,
                    0
                  ) / 5
                }%`,
              }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-primary to-green-500 rounded-full"
            />
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

const ResolutionStatusBanner = ({
  isResolved,
  resolutionTime,
  businessImpact,
}: {
  isResolved: boolean;
  resolutionTime: number | null;
  businessImpact?: any;
}) => {
  if (!isResolved) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: -20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 25,
        duration: 0.6,
      }}
      className="mb-6"
    >
      <div
        className="relative overflow-hidden rounded-2xl p-6
        bg-gradient-to-r from-green-500/10 via-green-400/10 to-emerald-500/10
        border-2 border-green-500/30 backdrop-blur-sm
        shadow-[0_0_30px_rgba(34,197,94,0.2)]"
      >
        {/* Animated background pattern */}
        <div className="absolute inset-0 opacity-20">
          <motion.div
            animate={{
              backgroundPosition: ["0% 0%", "100% 100%"],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "linear",
            }}
            className="w-full h-full bg-gradient-to-br from-green-400/20 via-transparent to-emerald-400/20"
            style={{
              backgroundSize: "200% 200%",
            }}
          />
        </div>

        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.div
              animate={{
                rotate: [0, 360],
                scale: [1, 1.1, 1],
              }}
              transition={{
                rotate: { duration: 2, ease: "easeInOut" },
                scale: { duration: 1, repeat: Infinity, ease: "easeInOut" },
              }}
              className="p-3 rounded-full bg-green-500/20 border border-green-500/40"
            >
              <CheckCircle className="w-8 h-8 text-green-500" />
            </motion.div>

            <div>
              <motion.h2
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="text-2xl font-bold text-green-600 dark:text-green-400 flex items-center gap-2"
              >
                <Trophy className="w-6 h-6" />
                INCIDENT RESOLVED
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="text-green-700 dark:text-green-300 font-medium"
              >
                System has been successfully restored to normal operation
              </motion.p>
            </div>
          </div>

          {resolutionTime && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
              className="text-right"
            >
              <div className="text-sm text-green-600 dark:text-green-400 font-medium mb-1">
                Total Resolution Time
              </div>
              <div className="text-3xl font-bold text-green-700 dark:text-green-300 font-mono">
                {formatDuration(resolutionTime)}
              </div>
              {businessImpact && (
                <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                  Cost Saved: $
                  {businessImpact.costSaved?.toLocaleString() || "N/A"}
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Success metrics */}
        {businessImpact && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-4 pt-4 border-t border-green-500/20"
          >
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  {businessImpact.affectedUsers?.toLocaleString() || "N/A"}
                </div>
                <div className="text-xs text-green-700 dark:text-green-300">
                  Users Protected
                </div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  {formatDuration(businessImpact.downtime || 0)}
                </div>
                <div className="text-xs text-green-700 dark:text-green-300">
                  Downtime Minimized
                </div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  100%
                </div>
                <div className="text-xs text-green-700 dark:text-green-300">
                  Service Restored
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

const SeverityBadge = ({ severity }: { severity: string }) => {
  const severityConfig = {
    critical: {
      bg: "bg-red-500/10 dark:bg-red-500/20",
      border: "border-red-500/50",
      text: "text-red-600 dark:text-red-400",
      glow: "shadow-[0_0_20px_rgba(239,68,68,0.3)]",
    },
    high: {
      bg: "bg-orange-500/10 dark:bg-orange-500/20",
      border: "border-orange-500/50",
      text: "text-orange-600 dark:text-orange-400",
      glow: "shadow-[0_0_20px_rgba(249,115,22,0.3)]",
    },
    medium: {
      bg: "bg-yellow-500/10 dark:bg-yellow-500/20",
      border: "border-yellow-500/50",
      text: "text-yellow-600 dark:text-yellow-400",
      glow: "shadow-[0_0_20px_rgba(234,179,8,0.3)]",
    },
    low: {
      bg: "bg-blue-500/10 dark:bg-blue-500/20",
      border: "border-blue-500/50",
      text: "text-blue-600 dark:text-blue-400",
      glow: "shadow-[0_0_20px_rgba(59,130,246,0.3)]",
    },
  };

  const config =
    severityConfig[severity as keyof typeof severityConfig] ||
    severityConfig.low;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
      }}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2
        ${config.bg} ${config.border} ${config.text} ${config.glow}
        backdrop-blur-sm font-semibold text-sm`}
    >
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [1, 0.7, 1],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <AlertTriangle className="w-4 h-4" />
      </motion.div>
      <span className="uppercase tracking-wide">{severity}</span>
    </motion.div>
  );
};

const Timer = ({ startTime }: { startTime: Date }) => {
  const [elapsed, setElapsed] = useState("");

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const diff = now.getTime() - startTime.getTime();
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setElapsed(
        `${hours.toString().padStart(2, "0")}:${minutes
          .toString()
          .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
      );
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  return (
    <div className="flex items-center gap-2 text-muted-foreground">
      <Clock className="w-4 h-4" />
      <span className="font-mono text-lg font-semibold">{elapsed}</span>
    </div>
  );
};

const ServiceStatusIcon = ({ status }: { status: string }) => {
  if (status === "operational")
    return <CheckCircle className="w-4 h-4 text-green-500" />;
  if (status === "degraded")
    return <AlertCircle className="w-4 h-4 text-yellow-500" />;
  if (status === "down") return <XCircle className="w-4 h-4 text-red-500" />;
  return <Activity className="w-4 h-4 text-muted-foreground" />;
};

const MetricCard = ({ metric }: { metric: Metric }) => {
  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="relative overflow-hidden rounded-xl p-4
        bg-gradient-to-br from-background/80 to-background/40
        backdrop-blur-md border border-border/50
        shadow-lg hover:shadow-xl transition-shadow"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
      <div className="relative flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs text-muted-foreground mb-1">{metric.label}</p>
          <p className="text-2xl font-bold text-foreground">{metric.value}</p>
          <div
            className={`flex items-center gap-1 mt-2 text-xs font-medium ${
              metric.change >= 0
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            <TrendingUp
              className={`w-3 h-3 ${metric.change < 0 ? "rotate-180" : ""}`}
            />
            <span>{Math.abs(metric.change)}%</span>
          </div>
        </div>
        <div className="p-2 rounded-lg bg-primary/10 text-primary">
          {metric.icon}
        </div>
      </div>
    </motion.div>
  );
};

const IncidentStatusPanel = ({
  incidentId = "INC-2024-001",
  title = "Database Performance Degradation",
  severity = "critical",
  startTime = new Date(Date.now() - 3600000),
  affectedServices = [
    { name: "API Gateway", status: "degraded", impact: "High latency" },
    { name: "Database Cluster", status: "down", impact: "Connection timeouts" },
    {
      name: "Authentication Service",
      status: "operational",
      impact: "No impact",
    },
    { name: "Email Service", status: "degraded", impact: "Delayed delivery" },
  ],
  description = "We are currently experiencing performance issues with our primary database cluster. Our team is actively investigating and working on a resolution.",
  useRealStatus = false,
  showOverview = false,
  overviewData = {
    activeIncidents: 1,
    resolvedIncidents: 5,
    totalIncidents: 6,
    recentResolution: null,
  },
}: IncidentStatusPanelProps) => {
  const [isLoading, setIsLoading] = useState(true);

  // Use real incident status if enabled
  const {
    currentIncident,
    isActive,
    isResolved,
    resolutionTime,
    currentPhase,
    phaseProgress,
    getBusinessImpact,
  } = useIncidentStatus();

  // Determine which data to use
  const actualIncident =
    useRealStatus && currentIncident ? currentIncident : null;
  const displayTitle = actualIncident?.title || title;
  const displaySeverity = actualIncident?.severity || severity;
  const displayStartTime = actualIncident?.startTime || startTime;
  const displayDescription = actualIncident?.description || description;
  const displayIncidentId = actualIncident?.id || incidentId;
  const businessImpact = useRealStatus ? getBusinessImpact() : null;

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const metrics: Metric[] = [
    {
      label: "Affected Users",
      value: "2,847",
      change: -12,
      icon: <Users className="w-5 h-5" />,
    },
    {
      label: "Error Rate",
      value: "23.4%",
      change: 156,
      icon: <Activity className="w-5 h-5" />,
    },
    {
      label: "Response Time",
      value: "4.2s",
      change: 340,
      icon: <Clock className="w-5 h-5" />,
    },
  ];

  if (isLoading) {
    return (
      <div className="w-full max-w-5xl mx-auto p-8">
        <Card className="relative overflow-hidden backdrop-blur-xl bg-background/95 border-border/50">
          <CardContent className="flex items-center justify-center h-96">
            <Loader2 className="w-12 h-12 animate-spin text-primary" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Incident Overview Panel - Requirements 2.4, 2.5 */}
        {showOverview && (
          <IncidentOverviewPanel
            activeIncidents={overviewData.activeIncidents}
            resolvedIncidents={overviewData.resolvedIncidents}
            totalIncidents={overviewData.totalIncidents}
            recentResolution={overviewData.recentResolution}
            showRecentResolution={useRealStatus && isResolved}
          />
        )}

        {/* Progress Indicator for Active Incidents - Requirements 2.3 */}
        {useRealStatus && isActive && (
          <ProgressIndicator
            phaseProgress={phaseProgress}
            currentPhase={currentPhase}
            isActive={isActive}
          />
        )}

        {/* Resolution Status Banner - Requirements 2.1, 2.2 */}
        {useRealStatus && isResolved && (
          <ResolutionStatusBanner
            isResolved={isResolved}
            resolutionTime={resolutionTime}
            businessImpact={businessImpact}
          />
        )}

        <Card
          className="relative overflow-hidden
          backdrop-blur-xl bg-background/95
          border-border/50 shadow-2xl"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-destructive/5 pointer-events-none" />

          <CardHeader className="relative space-y-4 pb-6">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <Badge className="font-mono text-xs border border-border text-foreground">
                    {displayIncidentId}
                  </Badge>
                  <SeverityBadge severity={displaySeverity} />
                  {useRealStatus && isResolved && (
                    <Badge className="bg-green-500/10 text-green-600 border-green-500/30">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      RESOLVED
                    </Badge>
                  )}
                </div>
                <CardTitle className="text-2xl md:text-3xl font-bold">
                  {displayTitle}
                </CardTitle>
                <p className="text-sm text-muted-foreground max-w-2xl">
                  {displayDescription}
                </p>
              </div>
              <div className="flex flex-col items-start md:items-end gap-2">
                <span className="text-xs text-muted-foreground">
                  {useRealStatus && isResolved ? "Resolution Time" : "Duration"}
                </span>
                <Timer startTime={displayStartTime} />
                {useRealStatus && isResolved && resolutionTime && (
                  <div className="text-sm text-green-600 dark:text-green-400 font-medium">
                    Resolved in {Math.floor(resolutionTime / 60)}m{" "}
                    {resolutionTime % 60}s
                  </div>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="relative space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {metrics.map((metric, index) => (
                <MetricCard key={index} metric={metric} />
              ))}
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" />
                Affected Services
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {affectedServices.map((service, index) => (
                  <motion.div
                    key={service.name}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 rounded-lg
                      bg-card/50 backdrop-blur-sm border border-border/50
                      hover:bg-card/80 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <ServiceStatusIcon status={service.status} />
                      <div>
                        <p className="font-medium text-sm">{service.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {service.impact}
                        </p>
                      </div>
                    </div>
                    <Badge
                      className={`text-xs capitalize ${
                        service.status === "operational"
                          ? "bg-primary text-primary-foreground"
                          : "bg-destructive text-destructive-foreground"
                      }`}
                    >
                      {service.status}
                    </Badge>
                  </motion.div>
                ))}
              </div>
            </div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="p-4 rounded-lg border border-primary/20
                bg-primary/5 backdrop-blur-sm"
            >
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-medium text-sm">Latest Update</p>
                  <p className="text-xs text-muted-foreground">
                    Our engineering team has identified the root cause and is
                    implementing a fix. We expect full service restoration
                    within the next 30 minutes.
                  </p>
                  <p className="text-xs text-muted-foreground/70 mt-2">
                    Last updated: {new Date().toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default IncidentStatusPanel;
