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

import React, { useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Users,
  Activity,
  Zap,
  Eye,
  Settings,
  BarChart3,
  Brain,
  MessageSquare,
} from "lucide-react";
import { RefinedDashboard } from "./RefinedDashboard";
import { AgentTransparencyModal } from "./AgentTransparencyModal";
import { ByzantineConsensusVisualization } from "./ByzantineConsensusVisualization";
import { TrustIndicatorsGroup } from "./TrustIndicators";
import {
  DashboardLayout,
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

// Enhanced Agent Card with animations and better visual hierarchy
interface EnhancedAgentCardProps {
  agent: {
    agent_name: string;
    agent_type: string;
    current_confidence: number;
    status: "idle" | "analyzing" | "complete" | "error";
  };
  onClick: () => void;
  isActive?: boolean;
}

function EnhancedAgentCard({
  agent,
  onClick,
  isActive = false,
}: EnhancedAgentCardProps) {
  const isClient = useClientSideTimestamp();

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

  const getStatusColor = (status: string, confidence: number) => {
    if (status === "error") return "border-red-500 bg-red-50";
    if (status === "analyzing") return "border-yellow-500 bg-yellow-50";
    if (confidence >= 0.9) return "border-green-500 bg-green-50";
    if (confidence >= 0.7) return "border-blue-500 bg-blue-50";
    return "border-orange-500 bg-orange-50";
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return "text-green-600";
    if (confidence >= 0.7) return "text-blue-600";
    return "text-orange-600";
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
              <motion.span
                className="text-2xl"
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
              </motion.span>
              <div>
                <CardTitle className="text-sm font-semibold">
                  {agent.agent_name}
                </CardTitle>
                <Badge
                  variant={
                    agent.status === "complete" ? "default" : "secondary"
                  }
                  className="text-xs mt-1"
                >
                  {agent.status}
                </Badge>
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
              <span className="text-xs text-muted-foreground">Confidence</span>
              <span
                className={`text-xl font-bold ${getConfidenceColor(
                  agent.current_confidence
                )}`}
              >
                {Math.round(agent.current_confidence * 100)}%
              </span>
            </div>
            <Progress value={agent.current_confidence * 100} className="h-2" />
            <div className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1">
              <Eye className="w-3 h-3" />
              View detailed reasoning
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Business Impact Scorecard
function BusinessImpactScorecard({
  metrics,
}: {
  metrics: BusinessImpactMetrics;
}) {
  return (
    <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-green-800">
          <TrendingUp className="w-5 h-5" />
          Business Impact Scorecard
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {metrics.mttrReduction.improvement}%
            </div>
            <div className="text-xs text-green-700">MTTR Reduction</div>
            <div className="text-xs text-muted-foreground">
              {metrics.mttrReduction.traditional}m →{" "}
              {metrics.mttrReduction.autonomous}m
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              ${(metrics.costSavings.amount / 1000000).toFixed(1)}M
            </div>
            <div className="text-xs text-green-700">Annual Savings</div>
            <div className="text-xs text-muted-foreground">
              {metrics.costSavings.percentage}% cost reduction
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              ${(metrics.revenueProtected / 1000000).toFixed(1)}M
            </div>
            <div className="text-xs text-green-700">Revenue Protected</div>
            <div className="text-xs text-muted-foreground">
              {metrics.uptime}% uptime maintained
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {metrics.incidentsPreventedToday}
            </div>
            <div className="text-xs text-green-700">Prevented Today</div>
            <div className="text-xs text-muted-foreground">
              85% prevention rate
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Incident Narrative Panel
function IncidentNarrativePanel({
  narrative,
}: {
  narrative: IncidentNarrative;
}) {
  const isClient = useClientSideTimestamp();

  const getPhaseIcon = (phase: string) => {
    const icons: Record<string, React.ReactNode> = {
      detection: <AlertTriangle className="w-4 h-4 text-orange-500" />,
      diagnosis: <Brain className="w-4 h-4 text-blue-500" />,
      prediction: <TrendingUp className="w-4 h-4 text-purple-500" />,
      resolution: <Settings className="w-4 h-4 text-green-500" />,
      communication: <MessageSquare className="w-4 h-4 text-indigo-500" />,
    };
    return icons[phase] || <Activity className="w-4 h-4" />;
  };

  return (
    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-blue-800">
          <MessageSquare className="w-5 h-5" />
          Incident Narrative
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            {getPhaseIcon(narrative.phase)}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className="text-xs">
                  {narrative.phase.toUpperCase()}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatTimeSafe(narrative.timestamp, isClient)}
                </span>
                <Badge
                  variant={
                    narrative.confidence >= 0.8 ? "default" : "secondary"
                  }
                  className="text-xs"
                >
                  {Math.round(narrative.confidence * 100)}% confidence
                </Badge>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">
                {narrative.summary}
              </p>
              {narrative.nextAction && (
                <div className="mt-2 p-2 bg-blue-100 rounded text-xs text-blue-800">
                  <strong>Next:</strong> {narrative.nextAction}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Predictive Forecasting Widget
function PredictiveForecastWidget({ alerts }: { alerts: PredictiveAlert[] }) {
  return (
    <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-purple-800">
          <Brain className="w-5 h-5" />
          Predictive Insights
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="flex items-start gap-3 p-3 bg-white rounded-lg border"
            >
              <div
                className={`w-2 h-2 rounded-full mt-2 ${
                  alert.type === "critical"
                    ? "bg-red-500"
                    : alert.type === "warning"
                    ? "bg-yellow-500"
                    : "bg-blue-500"
                }`}
              />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge
                    variant={
                      alert.type === "critical" ? "destructive" : "secondary"
                    }
                    className="text-xs"
                  >
                    {alert.probability}% probability
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {alert.timeframe}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{alert.message}</p>
                {alert.preventionAction && (
                  <div className="mt-1 text-xs text-purple-600">
                    <strong>Prevention:</strong> {alert.preventionAction}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Main Improved Dashboard Component
export function ImprovedOperationsDashboard() {
  const [viewMode, setViewMode] = useState<ViewMode["mode"]>("ops");
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeAgentType, setActiveAgentType] = useState<string | null>(null);

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
      "Diagnosis Agent identified database query plan regression causing connection pool exhaustion. Resolution Agent has initiated canary rollback with circuit breaker protection. Estimated completion in 3 minutes with full rollback capability.",
    timestamp: new Date(Date.now() - 4 * 60 * 1000), // 4 minutes ago
    confidence: 0.94,
    nextAction: "Monitor traffic restoration and validate performance metrics",
  };

  const predictiveAlerts: PredictiveAlert[] = [
    {
      id: "pred-001",
      type: "warning",
      message:
        "API layer showing early signs of cascade failure pattern. Similar to incident INC-4512.",
      probability: 74,
      timeframe: "Next 15-30 minutes",
      preventionAction:
        "Preemptively scale connection pools and enable circuit breakers",
    },
    {
      id: "pred-002",
      type: "info",
      message:
        "Memory usage trending toward threshold in session service after recent deployment.",
      probability: 62,
      timeframe: "Next 2-4 hours",
      preventionAction: "Schedule canary rollback during low-traffic window",
    },
  ];

  const sampleAgents = [
    {
      agent_name: "Detection Agent",
      agent_type: "detection",
      current_confidence: 0.93,
      status: "complete" as const,
    },
    {
      agent_name: "Diagnosis Agent",
      agent_type: "diagnosis",
      current_confidence: 0.97,
      status: "complete" as const,
    },
    {
      agent_name: "Prediction Agent",
      agent_type: "prediction",
      current_confidence: 0.73,
      status: "analyzing" as const,
    },
    {
      agent_name: "Resolution Agent",
      agent_type: "resolution",
      current_confidence: 0.95,
      status: "complete" as const,
    },
    {
      agent_name: "Communication Agent",
      agent_type: "communication",
      current_confidence: 0.88,
      status: "complete" as const,
    },
  ];

  const handleAgentClick = useCallback((agentType: string) => {
    setActiveAgentType(agentType);
    // Get sample agent data (you would replace this with real data)
    setSelectedAgent({
      agent_name: `${
        agentType.charAt(0).toUpperCase() + agentType.slice(1)
      } Agent`,
      agent_type: agentType,
      current_confidence: Math.random() * 0.3 + 0.7, // 0.7-1.0
      status: "complete",
      reasoning_summary: `Sample reasoning for ${agentType} agent...`,
    });
    setIsModalOpen(true);
  }, []);

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
      {/* View Mode Toggle */}
      <Card className="bg-gradient-to-r from-slate-50 to-gray-50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Autonomous Incident Commander
              </h1>
              <p className="text-sm text-muted-foreground">
                AI-Powered Multi-Agent Response System
              </p>
            </div>
            <div className="flex gap-2">
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

      {/* Business Impact Scorecard - Always visible but more prominent in executive mode */}
      <BusinessImpactScorecard metrics={businessMetrics} />

      {/* Incident Narrative - New addition */}
      <IncidentNarrativePanel narrative={incidentNarrative} />

      {/* Predictive Forecasting - New addition */}
      <PredictiveForecastWidget alerts={predictiveAlerts} />

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
              <Card className="bg-green-50 border-green-200">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                    <div>
                      <div className="text-2xl font-bold text-green-600">
                        AUTONOMOUS
                      </div>
                      <div className="text-sm text-green-700">
                        System Status
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Clock className="w-8 h-8 text-blue-600" />
                    <div>
                      <div className="text-2xl font-bold text-blue-600">
                        1.4 MIN
                      </div>
                      <div className="text-sm text-blue-700">Average MTTR</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-purple-50 border-purple-200">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Shield className="w-8 h-8 text-purple-600" />
                    <div>
                      <div className="text-2xl font-bold text-purple-600">
                        99.97%
                      </div>
                      <div className="text-sm text-purple-700">Uptime</div>
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
            {/* Trust Indicators Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Shield className="w-5 h-5 text-green-600" />
                    System Trust & Security
                  </CardTitle>
                  <Badge variant="default" className="bg-green-500">
                    All Systems Verified
                  </Badge>
                </div>
              </CardHeader>
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
              </CardContent>
            </Card>

            {/* Enhanced Agent Cards */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Brain className="w-5 h-5 text-blue-600" />
                  AI Agent Coordination
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Click any agent to view detailed reasoning and evidence
                </p>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {sampleAgents.map((agent) => (
                    <EnhancedAgentCard
                      key={agent.agent_type}
                      agent={agent}
                      onClick={() => handleAgentClick(agent.agent_type)}
                      isActive={activeAgentType === agent.agent_type}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Byzantine Consensus - Simplified */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-600" />
                  Consensus Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-2xl font-bold text-green-600">89%</div>
                    <div className="text-sm text-muted-foreground">
                      Weighted Consensus
                    </div>
                  </div>
                  <div>
                    <Badge variant="default" className="bg-green-500">
                      THRESHOLD ACHIEVED (85%)
                    </Badge>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  <strong>Decision:</strong> Autonomous action authorized
                  without human review
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
