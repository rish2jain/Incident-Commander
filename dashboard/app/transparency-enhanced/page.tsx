"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  DashboardLayout,
  DashboardSection,
  DashboardGrid,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress,
  SeverityIndicator,
} from "../../src/components/shared";
import ByzantineConsensusDemo from "../../src/components/ByzantineConsensusDemo";
import PredictivePreventionDemo from "../../src/components/PredictivePreventionDemo";

// Enhanced Components
import {
  InteractiveMetricCard,
  EnhancedConfidenceGauge,
  PerformanceTrends,
  ExportButton,
  Tooltip,
} from "../../src/components/enhanced/InteractiveMetrics";
import { DecisionTreeVisualization } from "../../src/components/enhanced/DecisionTreeVisualization";
import { CommunicationPanel } from "../../src/components/enhanced/CommunicationPanel";
import { ReasoningPanel } from "../../src/components/enhanced/ReasoningPanel";

/**
 * Enhanced AI Transparency Dashboard
 *
 * Implements all user feedback improvements:
 * - Enhanced readability with collapsible sections
 * - Interactive metrics with tooltips and explanations
 * - Decision tree visualization with expandable nodes
 * - Improved communication panel with message categorization
 * - Performance trends with sparklines
 * - Export functionality for reports
 * - Better accessibility and color contrast
 */

// Enhanced TypeScript interfaces
interface EnhancedAgentReasoning {
  id: string;
  timestamp: string;
  agent: string;
  step: string;
  message: string;
  confidence: number;
  reasoning: string;
  explanation?: string;
  evidence?: string[];
  alternatives?: Array<{
    option: string;
    probability: number;
    chosen: boolean;
    reasoning?: string;
  }>;
  riskAssessment?: number;
  processingTime?: number;
  keyInsights?: string[];
  nextSteps?: string[];
}

interface EnhancedDecisionNode {
  id: string;
  nodeType: "analysis" | "action" | "execution" | "condition";
  label: string;
  confidence: number;
  description?: string;
  evidence?: string[];
  alternatives?: Array<{
    option: string;
    probability: number;
    chosen: boolean;
    reasoning?: string;
  }>;
  children?: EnhancedDecisionNode[];
  metadata?: {
    executionTime?: number;
    riskLevel?: "low" | "medium" | "high";
    impact?: string;
  };
}

interface EnhancedAgentMessage {
  id: string;
  timestamp: string;
  from: string;
  to: string;
  message: string;
  messageType: string;
  confidence?: number;
  priority?: "low" | "medium" | "high" | "critical";
  metadata?: {
    correlationId?: string;
    retryCount?: number;
    processingTime?: number;
    payload?: any;
  };
}

interface Scenario {
  name: string;
  category: string;
  severity: string;
  description: string;
  detailedDescription: string;
  mttr: number;
}

const SCENARIOS: Record<string, Scenario> = {
  database_cascade: {
    name: "Database Cascade Failure",
    category: "Infrastructure",
    severity: "high",
    description: "Connection pool exhaustion causing cascading failures",
    detailedDescription:
      "Primary database connection pool saturated at 500/500, triggering circuit breakers and causing dependent services to fail in sequence",
    mttr: 147,
  },
  api_overload: {
    name: "API Rate Limit Breach",
    category: "Performance",
    severity: "medium",
    description: "Authentication service hitting rate limits under load",
    detailedDescription:
      "Sudden traffic spike overwhelms authentication endpoints, causing 429 responses and user login failures across multiple applications",
    mttr: 89,
  },
  memory_leak: {
    name: "Memory Leak Detection",
    category: "Resource",
    severity: "medium",
    description: "Gradual memory consumption increase in microservice",
    detailedDescription:
      "Memory usage climbing steadily in user session service, indicating potential memory leak that could lead to OOM crashes",
    mttr: 203,
  },
  security_breach: {
    name: "Security Anomaly Alert",
    category: "Security",
    severity: "critical",
    description: "Unusual access patterns detected in admin systems",
    detailedDescription:
      "Multiple failed authentication attempts followed by successful login from unusual geographic location with elevated privilege usage",
    mttr: 45,
  },
};

export default function EnhancedTransparencyDashboard() {
  const [incidentActive, setIncidentActive] = useState(false);
  const [mttrSeconds, setMttrSeconds] = useState(0);
  const [currentPhase, setCurrentPhase] = useState("idle");
  const [selectedScenario, setSelectedScenario] = useState("database_cascade");
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customScenario, setCustomScenario] = useState("");

  // Enhanced state with better data structures
  const [agentReasonings, setAgentReasonings] = useState<
    EnhancedAgentReasoning[]
  >([]);
  const [decisionTree, setDecisionTree] = useState<{
    rootNode: EnhancedDecisionNode;
  } | null>(null);
  const [confidenceScores, setConfidenceScores] = useState<
    Record<string, number>
  >({});
  const [agentCommunications, setAgentCommunications] = useState<
    EnhancedAgentMessage[]
  >([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);

  // Enhanced helper functions
  const generateEnhancedAlternatives = (step: string) => {
    const alternatives: Record<
      string,
      Array<{
        option: string;
        probability: number;
        chosen: boolean;
        reasoning?: string;
      }>
    > = {
      "Analyzing symptoms": [
        {
          option: "Database connection issue",
          probability: 0.87,
          chosen: true,
          reasoning:
            "High correlation with connection pool metrics and error patterns",
        },
        {
          option: "Network partition",
          probability: 0.23,
          chosen: false,
          reasoning: "Network latency within normal bounds, unlikely cause",
        },
        {
          option: "Memory exhaustion",
          probability: 0.15,
          chosen: false,
          reasoning: "Memory usage stable, not consistent with symptoms",
        },
      ],
      "Identifying root cause": [
        {
          option: "Slow query cascade",
          probability: 0.94,
          chosen: true,
          reasoning:
            "Query execution times exceed thresholds, blocking other operations",
        },
        {
          option: "Connection pool leak",
          probability: 0.31,
          chosen: false,
          reasoning: "Pool size stable over time, leak pattern not detected",
        },
        {
          option: "Lock contention",
          probability: 0.18,
          chosen: false,
          reasoning: "Lock wait times within acceptable range",
        },
      ],
      "Planning remediation": [
        {
          option: "Kill query + Scale pool",
          probability: 0.96,
          chosen: true,
          reasoning:
            "Immediate relief with minimal risk, proven effective approach",
        },
        {
          option: "Restart database",
          probability: 0.12,
          chosen: false,
          reasoning:
            "High impact solution, unnecessary given targeted fix available",
        },
        {
          option: "Scale horizontally",
          probability: 0.45,
          chosen: false,
          reasoning: "Long-term solution, doesn't address immediate issue",
        },
      ],
    };
    return alternatives[step] || [];
  };

  const simulateEnhancedAgentReasoning = useCallback(
    (agent: string, step: string, evidence: string[], confidence: number) => {
      const reasoning: EnhancedAgentReasoning = {
        id: `${agent}-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        agent,
        step,
        message: `${step} - Confidence: ${(confidence * 100).toFixed(1)}%`,
        confidence,
        reasoning: `Analyzing ${step.toLowerCase()} with ${(
          confidence * 100
        ).toFixed(1)}% confidence based on comprehensive evidence analysis`,
        explanation: `${agent} agent processing ${step} using advanced ML models and historical pattern matching`,
        evidence,
        alternatives: generateEnhancedAlternatives(step),
        riskAssessment: 1 - confidence,
        processingTime: Math.floor(Math.random() * 500) + 100,
        keyInsights: [
          `Pattern matches ${Math.floor(
            confidence * 100
          )}% of historical incidents`,
          `Risk mitigation strategies identified and prioritized`,
          `Confidence level sufficient for autonomous action`,
        ],
        nextSteps: [
          "Continue monitoring system metrics",
          "Prepare fallback strategies if needed",
          "Coordinate with other agents for consensus",
        ],
      };

      setAgentReasonings((prev) => [reasoning, ...prev]);
      setConfidenceScores((prev) => ({ ...prev, [agent]: confidence }));
    },
    []
  );

  const simulateEnhancedAgentCommunication = (
    from: string,
    to: string,
    messageType: string,
    priority: "low" | "medium" | "high" | "critical" = "medium"
  ) => {
    const communication: EnhancedAgentMessage = {
      id: `${from}-${to}-${Date.now()}`,
      timestamp: new Date().toISOString(),
      from,
      to,
      message: `${messageType.replace(
        "_",
        " "
      )} - coordinating response strategy`,
      messageType,
      confidence: Math.random() * 0.3 + 0.7,
      priority,
      metadata: {
        correlationId: `corr-${Math.random().toString(36).substr(2, 9)}`,
        retryCount: 0,
        processingTime: Math.floor(Math.random() * 100) + 20,
        payload: {
          action: messageType,
          timestamp: Date.now(),
          agentVersion: "2.1.0",
        },
      },
    };

    setAgentCommunications((prev) => [communication, ...prev]);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getPhaseProgress = () => {
    const phases = [
      "idle",
      "detection",
      "diagnosis",
      "consensus",
      "resolution",
      "verification",
    ];
    const currentIndex = phases.indexOf(currentPhase);
    return (currentIndex / (phases.length - 1)) * 100;
  };

  // Enhanced incident trigger with better simulation
  const triggerIncident = useCallback(async () => {
    if (incidentActive) return;

    setIncidentActive(true);
    setMttrSeconds(0);
    setCurrentPhase("detection");
    setAgentReasonings([]);
    setAgentCommunications([]);
    setConfidenceScores({});

    // Phase 1: Enhanced Detection
    simulateEnhancedAgentReasoning(
      "Detection",
      "Analyzing symptoms",
      [
        "Connection pool: 500/500 (100% utilization)",
        "Error rate: 47% (baseline: 0.1%)",
        "Response time: 8.5s (baseline: 120ms)",
        "Queue depth: 245 pending requests",
        "CPU utilization: 89% (threshold: 80%)",
      ],
      0.92
    );

    await new Promise((resolve) => setTimeout(resolve, 2000));
    simulateEnhancedAgentCommunication(
      "Detection",
      "Diagnosis",
      "evidence_sharing",
      "high"
    );

    // Phase 2: Enhanced Diagnosis
    setTimeout(() => {
      setCurrentPhase("diagnosis");
      simulateEnhancedAgentReasoning(
        "Diagnosis",
        "Identifying root cause",
        [
          "Query analytics_rollup running 47s (timeout: 30s)",
          "12 queries blocked in queue",
          "Lock wait timeout exceeded on user_sessions table",
          "Connection pool exhaustion pattern detected",
          "Similar incident resolved 3 days ago with same pattern",
        ],
        0.94
      );

      // Enhanced decision tree
      const tree = {
        rootNode: {
          id: "root",
          nodeType: "analysis" as const,
          label: "N+1 query pattern in authentication service",
          confidence: 0.88,
          description: "Inefficient query pattern causing database overload",
          evidence: [
            "Multiple single-row queries instead of batch operation",
            "Query count scales linearly with user sessions",
            "Database connection pool exhaustion",
          ],
          metadata: {
            executionTime: 45,
            riskLevel: "high" as const,
            impact: "Service degradation affecting 15,000+ users",
          },
          children: [
            {
              id: "immediate",
              nodeType: "action" as const,
              label: "Immediate Response",
              confidence: 0.95,
              description: "Quick mitigation to restore service",
              metadata: {
                executionTime: 30,
                riskLevel: "low" as const,
                impact: "Temporary relief, 90% service restoration",
              },
              children: [
                {
                  id: "scale",
                  nodeType: "execution" as const,
                  label: "Scale Connection Pool",
                  confidence: 0.92,
                  description:
                    "Increase pool size from 500 to 1000 connections",
                  metadata: {
                    executionTime: 15,
                    riskLevel: "low" as const,
                    impact: "Immediate capacity increase",
                  },
                },
              ],
            },
            {
              id: "longterm",
              nodeType: "action" as const,
              label: "Long-term Fix",
              confidence: 0.87,
              description: "Permanent solution to prevent recurrence",
              metadata: {
                executionTime: 300,
                riskLevel: "medium" as const,
                impact: "Permanent fix, prevents future incidents",
              },
              children: [
                {
                  id: "optimize",
                  nodeType: "execution" as const,
                  label: "Optimize Query Patterns",
                  confidence: 0.91,
                  description: "Implement batch queries and connection pooling",
                  metadata: {
                    executionTime: 180,
                    riskLevel: "medium" as const,
                    impact: "50% reduction in database load",
                  },
                },
              ],
            },
          ],
        },
      };

      setDecisionTree(tree);
      simulateEnhancedAgentCommunication(
        "Diagnosis",
        "Resolution",
        "consensus_building",
        "high"
      );
    }, 3000);

    // Phase 3: Enhanced Consensus
    setTimeout(() => {
      setCurrentPhase("consensus");
      simulateEnhancedAgentReasoning(
        "Prediction",
        "Forecasting impact",
        [
          "Dual approach success rate: 96% based on historical data",
          "Expected MTTR: 45-60 seconds with immediate action",
          "Risk of cascade failure: 12% without intervention",
          "User impact: 15,000 affected users, $2,400/minute revenue loss",
        ],
        0.96
      );
    }, 5000);

    // Phase 4: Enhanced Resolution
    setTimeout(() => {
      setCurrentPhase("resolution");
      simulateEnhancedAgentReasoning(
        "Resolution",
        "Executing remediation",
        [
          "Long-running query terminated successfully",
          "Connection pool scaling initiated (500→1000)",
          "Circuit breakers reset, traffic flow restored",
          "Monitoring alerts cleared, system stabilizing",
        ],
        0.98
      );

      const metrics = {
        mttr: 147,
        detectionTime: 15,
        resolutionTime: 45,
        agentEfficiency: 0.92,
        accuracy: 0.95,
        confidenceCalibration: 0.88,
        trends: {
          mttr: [180, 165, 150, 147, 140],
          accuracy: [0.89, 0.91, 0.93, 0.95, 0.95],
          detectionTime: [25, 22, 18, 15, 15],
        },
      };
      setPerformanceMetrics(metrics);
    }, 7000);

    // Phase 5: Complete
    setTimeout(() => {
      setCurrentPhase("complete");
      setIncidentActive(false);
      simulateEnhancedAgentCommunication(
        "Resolution",
        "Communication",
        "status_update",
        "low"
      );
    }, 9000);
  }, [incidentActive, simulateEnhancedAgentReasoning]);

  // MTTR timer
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (incidentActive) {
      interval = setInterval(() => {
        setMttrSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [incidentActive]);

  // Auto-demo effect
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("auto-demo") === "true" && !incidentActive) {
      const timer = setTimeout(() => {
        triggerIncident();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [incidentActive, triggerIncident]);

  // Export functionality
  const handleExport = (format: "pdf" | "csv" | "json") => {
    const data = {
      timestamp: new Date().toISOString(),
      incident: selectedScenario,
      reasoning: agentReasonings,
      communications: agentCommunications,
      decisionTree,
      metrics: performanceMetrics,
      confidenceScores,
    };

    const filename = `incident-analysis-${Date.now()}`;

    switch (format) {
      case "json":
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${filename}.json`;
        a.click();
        URL.revokeObjectURL(url);
        break;
      case "csv":
        // Simplified CSV export for reasoning steps
        const csvData = agentReasonings
          .map(
            (r) =>
              `"${r.timestamp}","${r.agent}","${r.step}","${
                r.confidence
              }","${r.reasoning.replace(/"/g, '""')}"`
          )
          .join("\n");
        const csvBlob = new Blob(
          [`Timestamp,Agent,Step,Confidence,Reasoning\n${csvData}`],
          { type: "text/csv" }
        );
        const csvUrl = URL.createObjectURL(csvBlob);
        const csvA = document.createElement("a");
        csvA.href = csvUrl;
        csvA.download = `${filename}.csv`;
        csvA.click();
        URL.revokeObjectURL(csvUrl);
        break;
      case "pdf":
        alert(
          "PDF export would integrate with a PDF generation library in production"
        );
        break;
    }
  };

  return (
    <DashboardLayout
      title="Enhanced AI Transparency Dashboard"
      subtitle="Complete AI explainability with improved UX and interactive features"
      icon="🧠"
      headerActions={<ExportButton onExport={handleExport} />}
    >

      {/* Enhanced Status Bar */}
      <DashboardSection variant="glass" className="mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Badge variant={incidentActive ? "destructive" : "default"}>
              {incidentActive ? `Phase: ${currentPhase}` : "System Ready"}
            </Badge>
            <div className="text-sm text-status-neutral">
              MTTR:{" "}
              <span className="text-green-400 font-mono">
                {formatTime(mttrSeconds)}
              </span>
            </div>
            <Tooltip content="Current incident resolution progress">
              <div className="flex-1 mx-6">
                <Progress value={getPhaseProgress()} className="h-2" />
              </div>
            </Tooltip>
          </div>
          <Button
            onClick={triggerIncident}
            disabled={incidentActive}
            className="bg-red-600 hover:bg-red-700 focus-ring-primary"
          >
            {incidentActive ? "Analyzing..." : "🚨 Trigger Enhanced Demo"}
          </Button>
        </div>
      </DashboardSection>

      {/* Enhanced Scenario Selection */}
      <DashboardSection
        title="Select Incident Scenario"
        variant="glass"
        className="mb-4"
      >
        <DashboardGrid columns={4} className="mb-3">
          {Object.entries(SCENARIOS).map(([key, scenario]) => (
            <div
              key={key}
              onClick={() => {
                setSelectedScenario(key);
                setShowCustomInput(false);
              }}
              className={`interactive-card p-3 rounded-lg border-2 transition-all ${
                selectedScenario === key && !showCustomInput
                  ? "border-blue-500 bg-blue-500/10"
                  : "border-slate-600 hover:border-blue-500/50"
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <h3 className="font-semibold text-sm">{scenario.name}</h3>
                <SeverityIndicator
                  severity={
                    scenario.severity as "critical" | "high" | "medium" | "low"
                  }
                />
              </div>
              <p className="text-xs text-status-neutral">
                {scenario.description}
              </p>
              <div className="text-xs text-slate-400 mt-1">
                MTTR: {scenario.mttr}s
              </div>
            </div>
          ))}
        </DashboardGrid>

        {/* Custom Scenario with Template */}
        <div
          onClick={() => setShowCustomInput(true)}
          className={`p-3 rounded-lg border-2 border-dashed cursor-pointer interactive-element transition-all ${
            showCustomInput
              ? "border-purple-500 bg-purple-500/10"
              : "border-slate-600 hover:border-purple-500/50"
          }`}
        >
          <div className="text-center">
            <div className="text-xl mb-1">🧪</div>
            <h3 className="font-semibold text-sm">Custom Scenario</h3>
            <p className="text-xs text-status-neutral">
              Describe your own incident with guided prompts
            </p>
          </div>
        </div>

        {showCustomInput && (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-3 gap-3 text-xs">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setCustomScenario(
                    "Service: Authentication API\nSymptoms: High latency, timeout errors\nImpact: User login failures"
                  )
                }
              >
                📝 API Issues Template
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setCustomScenario(
                    "Service: Database cluster\nSymptoms: Connection pool exhaustion\nImpact: Application errors"
                  )
                }
              >
                📝 Database Template
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setCustomScenario(
                    "Service: Load balancer\nSymptoms: Uneven traffic distribution\nImpact: Server overload"
                  )
                }
              >
                📝 Infrastructure Template
              </Button>
            </div>
            <textarea
              value={customScenario}
              onChange={(e) => setCustomScenario(e.target.value)}
              placeholder="Describe your incident scenario with:\n- Affected service/component\n- Observed symptoms\n- Business impact\n- Any relevant context"
              className="w-full mt-4 p-3 bg-slate-700 border border-slate-600 rounded-lg text-sm"
              rows={4}
            />
          </div>
        )}
      </DashboardSection>

      {/* Enhanced Visual Proof Components */}
      <DashboardSection variant="glass" className="mb-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PredictivePreventionDemo
            className="w-full"
            onPreventionComplete={() => console.log("Prevention demo complete")}
          />
          <ByzantineConsensusDemo className="w-full" />
        </div>
      </DashboardSection>

      {/* Enhanced Transparency Tabs */}
      <Tabs defaultValue="reasoning" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 card-glass">
          <TabsTrigger value="reasoning" data-testid="tab-reasoning">
            🧠 Reasoning
          </TabsTrigger>
          <TabsTrigger value="decisions" data-testid="tab-decisions">
            🌳 Decisions
          </TabsTrigger>
          <TabsTrigger value="confidence" data-testid="tab-confidence">
            📈 Confidence
          </TabsTrigger>
          <TabsTrigger value="communication" data-testid="tab-communication">
            💬 Communication
          </TabsTrigger>
          <TabsTrigger value="analytics" data-testid="tab-analytics">
            📊 Analytics
          </TabsTrigger>
        </TabsList>

        {/* Enhanced Reasoning Tab */}
        <TabsContent value="reasoning" data-testid="panel-reasoning">
          <ReasoningPanel
            reasoningSteps={agentReasonings}
            onStepClick={(step) => console.log("Reasoning step clicked:", step)}
          />
        </TabsContent>

        {/* Enhanced Decision Tree Tab */}
        <TabsContent value="decisions" data-testid="panel-decisions">
          {!decisionTree ? (
            <Card className="card-glass">
              <CardContent className="text-center text-status-neutral py-12">
                <div className="text-4xl mb-3">🌳</div>
                <h3 className="text-lg font-medium mb-2">
                  Decision Tree Analysis
                </h3>
                <p className="text-sm">
                  Interactive decision tree will appear during incident analysis
                </p>
                <p className="text-xs mt-2 text-slate-500">
                  Click nodes to explore decision paths and alternatives
                </p>
              </CardContent>
            </Card>
          ) : (
            <DecisionTreeVisualization
              rootNode={decisionTree.rootNode}
              onNodeClick={(node) =>
                console.log("Decision node clicked:", node)
              }
            />
          )}
        </TabsContent>

        {/* Enhanced Confidence Tab */}
        <TabsContent value="confidence" data-testid="panel-confidence">
          <Card className="card-glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                📈 Enhanced Confidence & Uncertainty Analysis
                <Tooltip content="Confidence scores with uncertainty ranges and calculation details">
                  <span className="text-sm text-slate-400 cursor-help">ℹ️</span>
                </Tooltip>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(confidenceScores).map(([agent, confidence]) => (
                  <EnhancedConfidenceGauge
                    key={agent}
                    agent={agent}
                    confidence={confidence}
                    uncertainty={0.02}
                    calculation={`Confidence derived from model accuracy (${(
                      confidence * 100
                    ).toFixed(1)}%) across ${
                      Math.floor(Math.random() * 1000) + 500
                    } historical incidents`}
                  />
                ))}

                {Object.keys(confidenceScores).length === 0 && (
                  <div className="text-center text-slate-400 py-8">
                    <div className="text-3xl mb-2">📈</div>
                    <p>
                      Confidence analysis will appear during incident processing
                    </p>
                    <p className="text-xs mt-2">
                      Enhanced gauges with uncertainty ranges and calculation
                      details
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Enhanced Communication Tab */}
        <TabsContent value="communication" data-testid="panel-communication">
          <CommunicationPanel
            messages={agentCommunications}
            onMessageClick={(message) =>
              console.log("Message clicked:", message)
            }
          />
        </TabsContent>

        {/* Enhanced Analytics Tab */}
        <TabsContent value="analytics" data-testid="panel-analytics">
          {!performanceMetrics ? (
            <Card className="card-glass">
              <CardContent className="text-center text-status-neutral py-12">
                <div className="text-4xl mb-3">📊</div>
                <h3 className="text-lg font-medium mb-2">
                  Performance Analytics
                </h3>
                <p className="text-sm">
                  Enhanced metrics with trends and comparisons will appear
                  during resolution
                </p>
                <p className="text-xs mt-2 text-slate-500">
                  Includes sparklines, baselines, and interactive drill-downs
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              <PerformanceTrends
                metrics={[
                  {
                    name: "Mean Time To Resolution (MTTR)",
                    current: performanceMetrics.mttr,
                    baseline: 300,
                    unit: "s",
                    trend: performanceMetrics.trends?.mttr || [
                      300, 250, 200, 180, 147,
                    ],
                    target: 120,
                  },
                  {
                    name: "Detection Accuracy",
                    current: performanceMetrics.accuracy * 100,
                    baseline: 85,
                    unit: "%",
                    trend: performanceMetrics.trends?.accuracy?.map(
                      (v) => v * 100
                    ) || [85, 88, 91, 94, 95],
                    target: 95,
                  },
                  {
                    name: "Detection Time",
                    current: performanceMetrics.detectionTime,
                    baseline: 45,
                    unit: "s",
                    trend: performanceMetrics.trends?.detectionTime || [
                      45, 35, 25, 20, 15,
                    ],
                    target: 10,
                  },
                ]}
              />

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <InteractiveMetricCard
                  title="Agent Efficiency"
                  value={`${(performanceMetrics.agentEfficiency * 100).toFixed(
                    1
                  )}%`}
                  icon="⚡"
                  trend="up"
                  trendValue="+5.2%"
                  details={[
                    {
                      label: "Task Completion",
                      value: "98.5%",
                      description: "Successfully completed tasks",
                    },
                    {
                      label: "Response Time",
                      value: "1.2s",
                      description: "Average agent response time",
                    },
                    {
                      label: "Resource Usage",
                      value: "67%",
                      description: "CPU and memory utilization",
                    },
                  ]}
                />

                <InteractiveMetricCard
                  title="Confidence Calibration"
                  value={`${(
                    performanceMetrics.confidenceCalibration * 100
                  ).toFixed(1)}%`}
                  icon="🎯"
                  trend="up"
                  trendValue="+2.1%"
                  details={[
                    {
                      label: "Prediction Accuracy",
                      value: "94.2%",
                      description: "Confidence vs actual outcomes",
                    },
                    {
                      label: "Calibration Error",
                      value: "0.08",
                      description: "Mean calibration error",
                    },
                    {
                      label: "Reliability",
                      value: "High",
                      description: "Confidence score reliability",
                    },
                  ]}
                />

                <InteractiveMetricCard
                  title="Business Impact"
                  value="$2.8M"
                  icon="💰"
                  trend="up"
                  trendValue="458% ROI"
                  details={[
                    {
                      label: "Annual Savings",
                      value: "$2,847,500",
                      description: "Total cost savings per year",
                    },
                    {
                      label: "Incident Cost",
                      value: "$47",
                      description: "Average cost per incident",
                    },
                    {
                      label: "Payback Period",
                      value: "6.2 months",
                      description: "Time to recover investment",
                    },
                  ]}
                />

                <InteractiveMetricCard
                  title="System Health"
                  value="99.9%"
                  icon="💚"
                  trend="stable"
                  trendValue="Stable"
                  details={[
                    {
                      label: "Uptime",
                      value: "99.95%",
                      description: "System availability",
                    },
                    {
                      label: "Error Rate",
                      value: "0.01%",
                      description: "System error rate",
                    },
                    {
                      label: "Performance",
                      value: "Optimal",
                      description: "Overall system performance",
                    },
                  ]}
                />
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  );
}
