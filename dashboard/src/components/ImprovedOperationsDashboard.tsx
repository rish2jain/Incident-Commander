/**
 * Improved Operations Dashboard
 *
 * Enhanced based on user feedback:
 * - Better visual hierarchy with stronger contrast
 * - Executive/Ops mode toggle
 * - Consolidated business impact scorecard
 * - Interactive agent cards with animations
 * - Incident narrative panel
 * - Predictive forecasting widget
 * - Improved consensus visualization
 */

"use client";

import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Zap,
  Eye,
  Settings,
  BarChart3,
  Brain,
  MessageSquare,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Play,
  Sparkles,
  Lock,
  Cpu,
} from "lucide-react";
import { AgentTransparencyModal } from "./AgentTransparencyModal";
import { TrustIndicatorsGroup } from "./TrustIndicators";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
  Progress,
} from "@/components/shared";
import {
  useClientSideTimestamp,
  formatTimeSafe,
} from "@/hooks/useClientSideTimestamp";

// Types
interface ViewMode {
  mode: "executive" | "ops";
  label: string;
  description: string;
}

interface BusinessImpactMetrics {
  mttrReduction: {
    traditional: number;
    autonomous: number;
    improvement: number;
  };
  costSavings: { amount: number; percentage: number };
  revenueProtected: number;
  uptime: number;
  incidentsPreventedToday: number;
  trend: "up" | "down" | "stable";
}

interface IncidentNarrative {
  phase:
    | "detection"
    | "diagnosis"
    | "prediction"
    | "resolution"
    | "communication";
  summary: string;
  timestamp: Date;
  confidence: number;
  nextAction?: string;
}

interface PredictiveAlert {
  id: string;
  type: "warning" | "info" | "critical";
  message: string;
  probability: number;
  timeframe: string;
  preventionAction?: string;
}

// Add severity type
type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

// Add collapsible section state type
interface CollapsibleState {
  security: boolean;
  byzantine: boolean;
  predictions: boolean;
  agents: boolean;
}

// Enhanced Agent Card with status badges instead of progress bars
function EnhancedAgentCard({
  agent,
  onClick,
  isActive = false,
}: EnhancedAgentCardProps) {
  const getAgentIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      detection: <AlertCircle className="w-5 h-5" />,
      diagnosis: <Brain className="w-5 h-5" />,
      prediction: <Sparkles className="w-5 h-5" />,
      resolution: <Settings className="w-5 h-5" />,
      communication: <MessageSquare className="w-5 h-5" />,
    };
    return icons[type.toLowerCase()] || <Cpu className="w-5 h-5" />;
  };

  const getStatusBadge = (status: string) => {
    if (status === "complete")
      return (
        <Badge variant="default" className="bg-green-600">
          ✓ Complete
        </Badge>
      );
    if (status === "analyzing")
      return (
        <Badge variant="secondary" className="bg-yellow-500 text-white">
          ⏳ Analyzing
        </Badge>
      );
    if (status === "error") return <Badge variant="destructive">✗ Error</Badge>;
    return <Badge variant="outline">Idle</Badge>;
  };

  const getStatusColor = (status: string, confidence: number) => {
    if (status === "error") return "border-red-500 bg-red-900/20";
    if (status === "analyzing") return "border-yellow-500 bg-yellow-900/20";
    if (confidence >= 0.9) return "border-green-500 bg-green-900/20";
    if (confidence >= 0.7) return "border-blue-500 bg-blue-900/20";
    return "border-orange-500 bg-orange-900/20";
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return "text-green-400";
    if (confidence >= 0.7) return "text-blue-400";
    return "text-orange-400";
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${getStatusColor(
          agent.status,
          agent.current_confidence
        )} ${isActive ? "ring-2 ring-blue-500" : ""}`}
        onClick={onClick}
      >
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <motion.div
                className="text-blue-600"
                animate={
                  agent.status === "analyzing"
                    ? { rotate: [0, 10, -10, 0] }
                    : {}
                }
                transition={{
                  duration: 2,
                  repeat: agent.status === "analyzing" ? Infinity : 0,
                }}
              >
                {getAgentIcon(agent.agent_type)}
              </motion.div>
              <div>
                <CardTitle className="text-sm font-semibold">
                  {agent.agent_name}
                </CardTitle>
                <div className="mt-1">{getStatusBadge(agent.status)}</div>
              </div>
            </div>
            {agent.status === "analyzing" && (
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-2 h-2 bg-blue-500 rounded-full"
              />
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground font-medium">
                Confidence
              </span>
              <span
                className={`text-2xl font-bold ${getConfidenceColor(
                  agent.current_confidence
                )}`}
              >
                {Math.round(agent.current_confidence * 100)}%
              </span>
            </div>
            {agent.summary && (
              <div className="text-xs text-slate-300 leading-snug line-clamp-2">
                {agent.summary}
              </div>
            )}
            <div className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1 font-semibold mt-2">
              <Eye className="w-3 h-3" />
              View detailed reasoning →
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Enhanced Agent Card with animations and better visual hierarchy
interface EnhancedAgentCardProps {
  agent: {
    agent_name: string;
    agent_type: string;
    current_confidence: number;
    status: "idle" | "analyzing" | "complete" | "error";
    summary?: string;
    reasoning_summary?: string;
  };
  onClick: () => void;
  isActive?: boolean;
}

// Business Impact Scorecard - Enhanced with better visual hierarchy
function BusinessImpactScorecard({
  metrics,
}: {
  metrics: BusinessImpactMetrics;
}) {
  return (
    <Card className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 border-green-500/30 shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-3 text-green-100 text-xl">
          <TrendingUp className="w-6 h-6 text-green-400" />
          Business Impact Dashboard
        </CardTitle>
        <p className="text-sm text-green-200 font-medium">
          Real-time operational metrics showing autonomous incident response
          value
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center space-y-2">
            <div className="text-4xl font-bold text-green-400">
              {metrics.mttrReduction.improvement}%
            </div>
            <div className="text-sm font-bold text-green-200">
              MTTR Improvement
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <div>
                <strong>Before:</strong> {metrics.mttrReduction.traditional} min
              </div>
              <div>
                <strong>After:</strong> {metrics.mttrReduction.autonomous} min
              </div>
              <div className="text-green-300 font-semibold">
                {metrics.mttrReduction.improvement}% faster resolution
              </div>
            </div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-4xl font-bold text-green-400">
              ${(metrics.costSavings.amount / 1000000).toFixed(1)}M
            </div>
            <div className="text-sm font-bold text-green-200">
              Annual Cost Savings
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <div>
                <strong>Traditional:</strong> $5.6M
              </div>
              <div>
                <strong>Autonomous:</strong> $275K
              </div>
              <div className="text-green-300 font-semibold">
                {metrics.costSavings.percentage}% cost reduction
              </div>
            </div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-4xl font-bold text-green-400">
              ${(metrics.revenueProtected / 1000000).toFixed(1)}M
            </div>
            <div className="text-sm font-bold text-green-200">
              Revenue Protected
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <div>Business continuity maintained</div>
              <div className="text-green-300 font-semibold">
                ${(metrics.revenueProtected / 1000000).toFixed(1)}M exposure
                avoided
              </div>
            </div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-4xl font-bold text-green-400">
              {metrics.incidentsPreventedToday}
            </div>
            <div className="text-sm font-bold text-green-200">
              Incidents Prevented Today
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <div>
                <strong>Uptime:</strong> {metrics.uptime}%
              </div>
              <div className="text-green-300 font-semibold">
                85% prevention success rate
              </div>
            </div>
          </div>
        </div>
        <div className="mt-6 pt-4 border-t border-green-500/30">
          <div className="text-sm text-green-200 font-semibold text-center">
            Continuous monitoring, autonomous triage, and closed-loop resolution
            deliver measurable operational resilience.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Incident Narrative Panel - Enhanced with better metadata layout and prominent CTA
function IncidentNarrativePanel({
  narrative,
}: {
  narrative: IncidentNarrative;
}) {
  const isClient = useClientSideTimestamp();

  const getPhaseIcon = (phase: string) => {
    const icons: Record<string, React.ReactNode> = {
      detection: <AlertTriangle className="w-5 h-5 text-orange-600" />,
      diagnosis: <Brain className="w-5 h-5 text-blue-600" />,
      prediction: <TrendingUp className="w-5 h-5 text-purple-600" />,
      resolution: <Settings className="w-5 h-5 text-green-600" />,
      communication: <MessageSquare className="w-5 h-5 text-indigo-600" />,
    };
    return icons[phase] || <Activity className="w-5 h-5" />;
  };

  return (
    <Card className="bg-gradient-to-r from-blue-900/20 to-indigo-900/20 border-blue-500/30 shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-3 text-blue-100 text-xl">
          <AlertCircle className="w-6 h-6 text-blue-400" />
          Live Incident Status
        </CardTitle>
        <p className="text-sm text-blue-200 font-medium">
          Real-time incident progression and autonomous response coordination
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="mt-1">{getPhaseIcon(narrative.phase)}</div>
            <div className="flex-1 space-y-3">
              {/* Vertical metadata layout */}
              <div className="flex items-center gap-3 flex-wrap">
                <Badge
                  variant="outline"
                  className="text-sm font-semibold px-3 py-1"
                >
                  {narrative.phase.toUpperCase()}
                </Badge>
                <span className="text-sm text-slate-400 font-medium">
                  {isClient
                    ? formatTimeSafe(narrative.timestamp, isClient)
                    : "Loading..."}
                </span>
              </div>

              {/* Confidence score - prominent */}
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <Progress
                    value={narrative.confidence * 100}
                    className="h-3"
                  />
                </div>
                <Badge
                  variant={
                    narrative.confidence >= 0.8 ? "default" : "secondary"
                  }
                  className="text-base font-bold px-3 py-1"
                >
                  {Math.round(narrative.confidence * 100)}% Confidence
                </Badge>
              </div>

              {/* Summary */}
              <div className="bg-slate-800 p-4 rounded-lg border border-blue-500/30">
                <div className="text-xs text-slate-400 font-semibold mb-2">
                  SITUATION SUMMARY
                </div>
                <p className="text-sm text-slate-200 leading-relaxed font-medium">
                  {narrative.summary}
                </p>
              </div>

              {/* Prominent Next Action Button */}
              {narrative.nextAction && (
                <Button
                  variant="default"
                  size="lg"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-md"
                >
                  <Play className="w-5 h-5 mr-2" />
                  {narrative.nextAction}
                </Button>
              )}

              {/* Additional context */}
              <div className="bg-blue-900/30 p-3 rounded-lg">
                <div className="text-xs text-blue-200 font-medium">
                  <strong>Active Coordination:</strong> Agents monitoring
                  rollback progress, service latency metrics, and
                  post-remediation stability verification.
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Predictive Forecasting Widget - Enhanced with severity badges
function PredictiveForecastWidget({ alerts }: { alerts: PredictiveAlert[] }) {
  const getSeverityConfig = (type: string) => {
    const configs = {
      critical: {
        color: "bg-red-500",
        textColor: "text-red-100",
        borderColor: "border-red-500/30",
      },
      warning: {
        color: "bg-yellow-500",
        textColor: "text-yellow-100",
        borderColor: "border-yellow-500/30",
      },
      info: {
        color: "bg-blue-500",
        textColor: "text-blue-100",
        borderColor: "border-blue-500/30",
      },
    };
    return configs[type as keyof typeof configs] || configs.info;
  };

  return (
    <Card className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 border-purple-500/30 shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-3 text-purple-100 text-xl">
          <Sparkles className="w-6 h-6 text-purple-400" />
          AI Predictive Intelligence
        </CardTitle>
        <p className="text-sm text-purple-200 font-medium">
          Machine learning models synthesize telemetry patterns, historical
          data, and system correlations to forecast emerging risks
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {alerts.map((alert) => {
            const config = getSeverityConfig(alert.type);
            return (
              <div
                key={alert.id}
                className={`p-4 bg-slate-800 rounded-lg border-2 ${config.borderColor} shadow-sm`}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`w-3 h-3 rounded-full mt-2 ${config.color}`}
                  />
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        variant={
                          alert.type === "critical"
                            ? "destructive"
                            : "secondary"
                        }
                        className="text-sm font-bold px-3 py-1"
                      >
                        {alert.type.toUpperCase()}
                      </Badge>
                      <Badge
                        variant="outline"
                        className="text-sm font-semibold"
                      >
                        {alert.probability}% Probability
                      </Badge>
                      <span className="text-xs text-slate-400 font-medium">
                        {alert.timeframe}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="text-xs text-slate-400 font-semibold">
                        DETECTED PATTERN
                      </div>
                      <p className="text-sm text-slate-100 font-medium leading-relaxed">
                        {alert.message}
                      </p>
                    </div>

                    {alert.preventionAction && (
                      <div className="bg-purple-900/30 p-3 rounded-lg">
                        <div className="text-xs text-purple-200 font-semibold">
                          <strong>RECOMMENDED ACTION:</strong>{" "}
                          {alert.preventionAction}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// Main Improved Dashboard Component
export function ImprovedOperationsDashboard() {
  const [viewMode, setViewMode] = useState<ViewMode["mode"]>("ops");
  const [selectedAgent, setSelectedAgent] = useState<
    EnhancedAgentCardProps["agent"] | null
  >(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeAgentType, setActiveAgentType] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState<Date | null>(null);

  // Add collapsible sections state
  const [expandedSections, setExpandedSections] = useState<CollapsibleState>({
    security: false,
    byzantine: false,
    predictions: true,
    agents: true,
  });

  // Add Quick View mode state
  const [quickViewMode, setQuickViewMode] = useState(false);

  // Add show all agents state
  const [showAllAgents, setShowAllAgents] = useState(true);

  // Toggle section expansion
  const toggleSection = (section: keyof CollapsibleState) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  // Fix hydration by setting timestamp on client side only
  useEffect(() => {
    setCurrentTime(new Date(Date.now() - 4 * 60 * 1000));
  }, []);

  // Sample data
  const businessMetrics: BusinessImpactMetrics = {
    mttrReduction: { traditional: 42, autonomous: 6, improvement: 85.7 },
    costSavings: { amount: 2847500, percentage: 95.1 },
    revenueProtected: 2800000,
    uptime: 99.97,
    incidentsPreventedToday: 18,
    trend: "up",
  };

  const incidentNarrative: IncidentNarrative = {
    phase: "resolution",
    summary:
      "Database query regression detected and isolated. Canary rollback executing with circuit-breaker protection. Resolution completing within 2 minutes — rollback ready if validation fails.",
    timestamp: currentTime || new Date(), // Use client-side timestamp to prevent hydration mismatch
    confidence: 0.94,
    nextAction:
      "Validate traffic restoration and confirm performance recovery.",
  };

  const predictiveAlerts: PredictiveAlert[] = [
    {
      id: "pred-001",
      type: "warning",
      message: "API cascade detected | Matches historical incident INC-4512",
      probability: 74,
      timeframe: "Within 15–30 Minutes",
      preventionAction: "Scale connection pools and enable circuit breakers.",
    },
    {
      id: "pred-002",
      type: "info",
      message:
        "Session-service memory trending toward threshold post-deployment.",
      probability: 62,
      timeframe: "Within 2–4 Hours",
      preventionAction: "Schedule canary rollback during low-traffic window.",
    },
  ];

  const sampleAgents = [
    {
      agent_name: "Detection",
      agent_type: "detection",
      current_confidence: 0.93,
      status: "complete" as const,
      summary:
        "Anomaly correlation across 143 telemetry signals. Baseline drift 0.6% — within guardrails.",
    },
    {
      agent_name: "Diagnosis",
      agent_type: "diagnosis",
      current_confidence: 0.97,
      status: "complete" as const,
      summary:
        "Query plan regression isolated; lock-wait accumulation detected and mitigated.",
    },
    {
      agent_name: "Prediction",
      agent_type: "prediction",
      current_confidence: 0.73,
      status: "analyzing" as const,
      summary:
        "API cascade pattern under evaluation. Awaiting customer-impact confirmation.",
    },
    {
      agent_name: "Resolution",
      agent_type: "resolution",
      current_confidence: 0.95,
      status: "complete" as const,
      summary:
        "Canary rollback validated; full restoration pending verification.",
    },
    {
      agent_name: "Communication",
      agent_type: "communication",
      current_confidence: 0.88,
      status: "complete" as const,
      summary:
        "Stakeholder updates synchronized across Slack & email; awaiting executive acknowledgment.",
    },
  ];

  const handleAgentClick = useCallback(
    (agent: EnhancedAgentCardProps["agent"]) => {
      setActiveAgentType(agent.agent_type);
      setSelectedAgent({
        agent_name: agent.agent_name,
        agent_type: agent.agent_type,
        current_confidence: agent.current_confidence,
        status: agent.status,
        reasoning_summary:
          agent.reasoning_summary ||
          `Sample reasoning for ${agent.agent_name}...`,
      });
      setIsModalOpen(true);
    },
    []
  );

  const viewModes: ViewMode[] = [
    {
      mode: "executive",
      label: "Executive View",
      description: "High-level metrics and business impact",
    },
    {
      mode: "ops",
      label: "Operations View",
      description: "Detailed technical insights and agent reasoning",
    },
  ];

  return (
    <div className="space-y-6">
      {/* View Mode Toggle - MOVED TO TOP */}
      <Card className="bg-gradient-to-r from-slate-800 to-slate-700 border-slate-600 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-100">
                Autonomous Incident Commander
              </h1>
              <p className="text-sm text-slate-400 font-medium mt-1">
                Production Operations Dashboard — Real-time AI-Driven Incident
                Response
              </p>
            </div>
            <div className="flex gap-2 items-center">
              {/* Quick View Toggle */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setQuickViewMode(!quickViewMode)}
                className="flex items-center gap-2"
              >
                {quickViewMode ? (
                  <>
                    <ChevronDown className="w-4 h-4" />
                    Full View
                  </>
                ) : (
                  <>
                    <ChevronUp className="w-4 h-4" />
                    Quick View
                  </>
                )}
              </Button>

              {/* Executive/Ops View Toggle */}
              {viewModes.map((mode) => (
                <Button
                  key={mode.mode}
                  variant={viewMode === mode.mode ? "default" : "outline"}
                  size="sm"
                  onClick={() => setViewMode(mode.mode)}
                  className="flex items-center gap-2"
                >
                  {mode.mode === "executive" ? (
                    <BarChart3 className="w-4 h-4" />
                  ) : (
                    <Settings className="w-4 h-4" />
                  )}
                  {mode.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary - Enhanced */}
      <Card className="bg-gradient-to-br from-blue-900/20 to-indigo-900/30 border-blue-500/30 shadow-md">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <CheckCircle className="w-8 h-8 text-blue-400 flex-shrink-0" />
            <div>
              <div className="text-lg font-bold text-blue-100 mb-2">
                System Status: Operational — Autonomous Response Active
              </div>
              <div className="text-sm text-slate-200 leading-relaxed font-medium">
                <strong>89% agent consensus achieved.</strong> AI agents
                coordinating in real-time to deliver 95% faster incident
                resolution, $2.8M annual cost savings, and 99.97% system uptime.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Business Impact Scorecard - Always visible */}
      <BusinessImpactScorecard metrics={businessMetrics} />

      {/* Incident Narrative */}
      <IncidentNarrativePanel narrative={incidentNarrative} />

      {/* Predictive Forecasting - Collapsible in Quick View */}
      {(!quickViewMode || expandedSections.predictions) && (
        <PredictiveForecastWidget alerts={predictiveAlerts} />
      )}

      <AnimatePresence mode="wait">
        {viewMode === "executive" ? (
          <motion.div
            key="executive"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            {/* Executive Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-green-900/20 border-green-500/30 shadow-sm">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-10 h-10 text-green-400" />
                    <div>
                      <div className="text-3xl font-bold text-green-400">
                        OPERATIONAL
                      </div>
                      <div className="text-sm text-green-200 font-semibold">
                        System Health Status
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-blue-900/20 border-blue-500/30 shadow-sm">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Clock className="w-10 h-10 text-blue-400" />
                    <div>
                      <div className="text-3xl font-bold text-blue-400">
                        1.4 MIN
                      </div>
                      <div className="text-sm text-blue-200 font-semibold">
                        Average Resolution Time
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-purple-900/20 border-purple-500/30 shadow-sm">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Shield className="w-10 h-10 text-purple-400" />
                    <div>
                      <div className="text-3xl font-bold text-purple-400">
                        99.97%
                      </div>
                      <div className="text-sm text-purple-200 font-semibold">
                        Platform Uptime
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="ops"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            {/* Trust Indicators Section - Collapsible */}
            {(!quickViewMode || expandedSections.security) && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Lock className="w-5 h-5 text-green-600" />
                      Security & Compliance Status
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="default"
                        className="bg-green-600 font-semibold"
                      >
                        ✓ VERIFIED SECURE
                      </Badge>
                      {quickViewMode && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleSection("security")}
                        >
                          {expandedSections.security ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                {expandedSections.security && (
                  <CardContent>
                    <TrustIndicatorsGroup
                      guardrails={[
                        {
                          name: "Safety Verification",
                          status: "passed",
                          details: "All operations within safety bounds",
                        },
                        {
                          name: "Rate Limits",
                          status: "passed",
                          details: "API usage within limits",
                        },
                      ]}
                      pii={["IP addresses", "User IDs", "Email addresses"]}
                      circuitBreaker={{ status: "closed" }}
                      rollback={{ available: true, steps: 5 }}
                      rag={{ sourcesCount: 3, avgSimilarity: 0.89 }}
                    />
                    <div className="text-xs text-green-300 font-medium text-center mt-4">
                      All systems and guardrails verified within compliance
                      parameters. Rollback paths continuously tested and ready.
                    </div>
                  </CardContent>
                )}
              </Card>
            )}

            {/* Enhanced Agent Cards - Show/Hide All Toggle */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-xl flex items-center gap-3">
                      <Brain className="w-6 h-6 text-blue-400" />
                      AI Agent Intelligence
                    </CardTitle>
                    <p className="text-sm text-slate-400 font-medium mt-1">
                      Multi-agent coordination with federated decision-making
                    </p>
                  </div>
                  {!quickViewMode && sampleAgents.length > 2 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAllAgents(!showAllAgents)}
                    >
                      {showAllAgents
                        ? "Show Less"
                        : `Show All (${sampleAgents.length})`}
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {(showAllAgents
                    ? sampleAgents
                    : sampleAgents.slice(0, 2)
                  ).map((agent) => (
                    <EnhancedAgentCard
                      key={agent.agent_type}
                      agent={agent}
                      onClick={() => handleAgentClick(agent)}
                      isActive={activeAgentType === agent.agent_type}
                    />
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <div className="text-xs text-slate-300 font-medium text-center">
                    Click any agent card to view detailed reasoning, confidence
                    calculations, and supporting evidence.
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Byzantine Consensus - SIMPLIFIED & BUSINESS-FRIENDLY */}
            {(!quickViewMode || expandedSections.byzantine) && (
              <Card className="bg-gradient-to-r from-emerald-900/20 to-green-900/20 border-green-500/30 shadow-md">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-xl flex items-center gap-3">
                        <Zap className="w-6 h-6 text-green-400" />
                        Agent Alignment Status
                      </CardTitle>
                      <p className="text-sm text-slate-400 font-medium mt-1">
                        Distributed consensus validation for autonomous
                        execution approval
                      </p>
                    </div>
                    {quickViewMode && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleSection("byzantine")}
                      >
                        {expandedSections.byzantine ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-center space-y-4">
                    {/* Large consensus percentage - Visual focal point */}
                    <div>
                      <div className="text-6xl font-bold text-green-400">
                        89%
                      </div>
                      <div className="text-lg font-semibold text-slate-300 mt-2">
                        Multi-Agent Consensus Achieved
                      </div>
                    </div>

                    {/* Status badge */}
                    <Badge
                      variant="default"
                      className="bg-green-600 text-white font-bold text-base px-6 py-2"
                    >
                      ✓ Autonomous Execution Approved
                    </Badge>

                    {/* Progress bar visualization */}
                    <div className="max-w-md mx-auto">
                      <Progress value={89} className="h-4" />
                      <div className="text-xs text-slate-400 mt-2 font-medium">
                        Consensus threshold: 85% | Current: 89% | Status:{" "}
                        <strong className="text-green-400">Exceeded</strong>
                      </div>
                    </div>

                    {/* Expandable technical details */}
                    {!quickViewMode && (
                      <details className="text-left mt-4">
                        <summary className="text-sm font-semibold text-slate-300 cursor-pointer hover:text-blue-400">
                          <Info className="w-4 h-4 inline mr-2" />
                          View Weighted Contribution Details
                        </summary>
                        <div className="mt-3 p-4 bg-slate-800 rounded-lg border border-green-500/30">
                          <div className="text-sm font-semibold text-slate-300 mb-2">
                            Agent Contribution Weights:
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                            <div className="space-y-1">
                              <div className="font-medium text-slate-400">
                                Detection
                              </div>
                              <div className="text-blue-400 font-semibold">
                                18.6% (20%)
                              </div>
                            </div>
                            <div className="space-y-1">
                              <div className="font-medium text-slate-400">
                                Diagnosis
                              </div>
                              <div className="text-blue-400 font-semibold">
                                38.8% (40%)
                              </div>
                            </div>
                            <div className="space-y-1">
                              <div className="font-medium text-slate-400">
                                Prediction
                              </div>
                              <div className="text-blue-400 font-semibold">
                                21.9% (30%)
                              </div>
                            </div>
                            <div className="space-y-1">
                              <div className="font-medium text-slate-400">
                                Resolution
                              </div>
                              <div className="text-blue-400 font-semibold">
                                9.5% (10%)
                              </div>
                            </div>
                            <div className="space-y-1">
                              <div className="font-medium text-slate-400">
                                Communication
                              </div>
                              <div className="text-slate-500 font-semibold">
                                0.0% (0%)
                              </div>
                            </div>
                          </div>
                          <div className="text-xs text-slate-400 mt-3 italic">
                            Weighted scores reflect confidence × assigned weight
                            for each agent type.
                          </div>
                        </div>
                      </details>
                    )}

                    <div className="text-sm text-slate-300 font-medium">
                      Federated multi-agent coordination validates unified
                      confidence for safe autonomous execution without human
                      approval.
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* System Controls - REORGANIZED */}
            <Card className="bg-gradient-to-r from-slate-800 to-slate-700 border-slate-600">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Settings className="w-5 h-5 text-slate-400" />
                  System Configuration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm flex-wrap">
                    <span className="font-semibold text-slate-300">
                      Active View:
                    </span>
                    <Badge variant="outline">
                      {viewMode === "executive"
                        ? "Executive Summary"
                        : "Operations Detail"}
                    </Badge>
                  </div>

                  {/* Demo Scenarios - Separate collapsible section */}
                  <details className="mt-4">
                    <summary className="text-sm font-bold text-slate-300 cursor-pointer hover:text-blue-400 flex items-center gap-2">
                      <Badge variant="secondary">DEBUG MODE</Badge>
                      Demo Scenario Testing
                    </summary>
                    <div className="mt-3 p-4 bg-yellow-900/20 rounded-lg border border-yellow-500/30">
                      <div className="text-xs text-yellow-200 font-medium mb-3">
                        ⚠️ Demo scenarios simulate incident conditions for
                        testing and demonstration purposes
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" className="text-xs">
                          <AlertTriangle className="w-3 h-3 mr-1" />
                          Database Failure
                        </Button>
                        <Button variant="outline" size="sm" className="text-xs">
                          <Activity className="w-3 h-3 mr-1" />
                          API Cascade
                        </Button>
                        <Button variant="outline" size="sm" className="text-xs">
                          <Brain className="w-3 h-3 mr-1" />
                          Memory Leak
                        </Button>
                        <Button variant="outline" size="sm" className="text-xs">
                          <Zap className="w-3 h-3 mr-1" />
                          Network Issue
                        </Button>
                        <Button variant="outline" size="sm" className="text-xs">
                          <Shield className="w-3 h-3 mr-1" />
                          Security Event
                        </Button>
                      </div>
                    </div>
                  </details>
                </div>
              </CardContent>
            </Card>

            {/* Attribution - Enhanced */}
            <Card className="bg-gradient-to-r from-indigo-900/20 to-blue-900/20 border-indigo-500/30">
              <CardContent className="pt-6">
                <div className="text-center space-y-3">
                  <div className="text-lg font-bold text-indigo-200 flex items-center justify-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Built for AWS Hackathon 2024
                  </div>
                  <div className="text-sm text-slate-300 font-medium">
                    Autonomous Incident Commander — Multi-Agent AI Orchestration
                    Platform
                  </div>
                  <div className="text-xs text-slate-400 space-y-1">
                    <div>
                      <strong>Powered by:</strong> AWS Bedrock • Amazon Nova •
                      Amazon Q Developer • Agents with Memory SDK
                    </div>
                    <div>
                      <strong>AI Models:</strong> Claude 3.5 Sonnet (Multi-Agent
                      Reasoning) • Nova Micro & Lite (Speed) • Nova Pro
                      (Accuracy)
                    </div>
                    <div>
                      <strong>Architecture:</strong> Federated Multi-Agent
                      System • Byzantine Fault Tolerant Consensus • Autonomous
                      Response
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 pt-2 border-t border-indigo-500/30">
                    © 2025 Autonomous Incident Commander. All Rights Reserved.
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Agent Transparency Modal */}
      <AgentTransparencyModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        agentData={selectedAgent}
      />
    </div>
  );
}
