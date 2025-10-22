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
  ConfidenceScore,
  SeverityIndicator,
} from "../../src/components/shared";
import ByzantineConsensusDemo from "../../src/components/ByzantineConsensusDemo";
import PredictivePreventionDemo from "../../src/components/PredictivePreventionDemo";
import { ReasoningPanel } from "../../src/components/enhanced/ReasoningPanel";
import { CommunicationPanel } from "../../src/components/enhanced/CommunicationPanel";
import { DecisionTreeVisualization } from "../../src/components/enhanced/DecisionTreeVisualization";

/**
 * Consolidated Transparency Dashboard
 *
 * Merges best features from insights-demo and enhanced-insights-demo.
 * Designed for technical demonstrations and AI explainability showcase.
 *
 * Features:
 * - 5 transparency tabs (Reasoning, Decisions, Confidence, Communication, Analytics)
 * - 4 predefined scenarios + custom input
 * - Clean shadcn/ui design
 * - Keyboard shortcuts (1-5 for tabs, Enter to trigger)
 *
 * Use for:
 * - Hackathon judging (technical track)
 * - AI transparency demonstrations
 * - Extended technical presentations
 */

// TypeScript interfaces
interface AgentReasoning {
  id: string;
  timestamp: string;
  agent: string;
  message: string;
  confidence: number;
  reasoning: string;
  step?: string;
  explanation?: string;
  evidence?: string[];
  alternatives?: Array<{
    option: string;
    probability: number;
    chosen: boolean;
  }>;
  riskAssessment?: number;
}

interface DecisionTreeNode {
  id: string;
  nodeType: string;
  label: string;
  confidence: number;
  children?: DecisionTreeNode[];
}

interface DecisionTree {
  rootNode: DecisionTreeNode;
  totalNodes: number;
  maxDepth: number;
}

interface AgentCommunication {
  id: string;
  timestamp: string;
  from: string;
  to: string;
  message: string;
  messageType: string;
  confidence?: number;
}

interface PerformanceMetrics {
  mttr: number;
  detectionTime: number;
  resolutionTime: number;
  agentEfficiency: number;
  accuracy?: number;
  confidenceCalibration?: number;
}

interface Scenario {
  name: string;
  category: string;
  severity: string;
  description: string;
  detailedDescription: string;
  mttr: number;
}

// Scenario metadata loaded from cached AWS-generated scenarios
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

export default function TransparencyDashboardPage() {
  const [incidentActive, setIncidentActive] = useState(false);
  const [mttrSeconds, setMttrSeconds] = useState(0);
  const [currentPhase, setCurrentPhase] = useState("idle");
  const [cachedScenario, setCachedScenario] = useState<any>(null);
  const [scenarioMetadata, setScenarioMetadata] = useState<any>(null);
  const [agentReasonings, setAgentReasonings] = useState<AgentReasoning[]>([
    // Initial sample reasoning for demo purposes
    {
      id: "sample-detection-1",
      timestamp: "Ready",
      agent: "Detection",
      message: "System monitoring active - Confidence: 92.0%",
      confidence: 0.92,
      reasoning:
        "Monitoring 47 metrics across 12 services with high confidence",
      step: "Continuous monitoring",
      explanation:
        "Detection agent actively monitoring system health and performance metrics",
      evidence: [
        "Response time: 120ms (baseline)",
        "Error rate: 0.1% (normal)",
        "Connection pool: 245/500 (healthy)",
      ],
      alternatives: [
        { option: "Active monitoring", probability: 0.92, chosen: true },
        { option: "Passive monitoring", probability: 0.15, chosen: false },
      ],
      riskAssessment: 0.08,
    },
    {
      id: "sample-diagnosis-1",
      timestamp: "Ready",
      agent: "Diagnosis",
      message: "Analysis capabilities ready - Confidence: 88.0%",
      confidence: 0.88,
      reasoning: "Ready to analyze patterns and identify root causes",
      step: "Standby analysis",
      explanation:
        "Diagnosis agent prepared with ML models and historical pattern analysis",
      evidence: [
        "Pattern database: 15,000+ incidents",
        "ML models: 94% accuracy rate",
        "Analysis time: <30s average",
      ],
      alternatives: [
        { option: "ML-based analysis", probability: 0.88, chosen: true },
        { option: "Rule-based analysis", probability: 0.45, chosen: false },
      ],
      riskAssessment: 0.12,
    },
  ]);
  const [decisionTree, setDecisionTree] = useState<DecisionTree | null>({
    // Initial sample decision tree for demo purposes
    rootNode: {
      id: "root-sample",
      nodeType: "analysis",
      label: "System Health Assessment - All systems operational",
      confidence: 0.92,
      children: [
        {
          id: "monitoring",
          nodeType: "action",
          label: "Continuous Monitoring",
          confidence: 0.95,
          children: [
            {
              id: "metrics",
              nodeType: "execution",
              label: "Monitor Key Metrics",
              confidence: 0.94,
            },
          ],
        },
        {
          id: "prevention",
          nodeType: "action",
          label: "Predictive Prevention",
          confidence: 0.87,
          children: [
            {
              id: "forecast",
              nodeType: "execution",
              label: "Forecast Potential Issues",
              confidence: 0.85,
            },
          ],
        },
      ],
    },
    totalNodes: 5,
    maxDepth: 3,
  });
  const [confidenceScores, setConfidenceScores] = useState<
    Record<string, number>
  >({
    // Initial sample confidence scores for demo purposes
    Detection: 0.92,
    Diagnosis: 0.88,
    Prediction: 0.85,
    Resolution: 0.9,
    Communication: 0.94,
  });
  const [agentCommunications, setAgentCommunications] = useState<
    AgentCommunication[]
  >([
    // Initial sample communications for demo purposes
    {
      id: "sample-comm-1",
      timestamp: "System Ready",
      from: "Detection",
      to: "Diagnosis",
      message: "System baseline established - ready for incident analysis",
      messageType: "status_update",
      confidence: 0.92,
    },
    {
      id: "sample-comm-2",
      timestamp: "System Ready",
      from: "Diagnosis",
      to: "Prediction",
      message: "Analysis models loaded - pattern recognition active",
      messageType: "capability_sync",
      confidence: 0.88,
    },
    {
      id: "sample-comm-3",
      timestamp: "System Ready",
      from: "Prediction",
      to: "Resolution",
      message: "Forecasting models ready - 15-30min prediction window",
      messageType: "capability_sync",
      confidence: 0.85,
    },
  ]);
  const [performanceMetrics, setPerformanceMetrics] =
    useState<PerformanceMetrics | null>({
      // Initial sample metrics for demo purposes
      mttr: 147,
      detectionTime: 15,
      resolutionTime: 45,
      agentEfficiency: 0.92,
      accuracy: 0.95,
      confidenceCalibration: 0.88,
    });
  const [selectedScenario, setSelectedScenario] = useState("database_cascade");
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customScenario, setCustomScenario] = useState("");

  // Helper function for alternatives
  const generateAlternatives = (step: string) => {
    const alternatives: Record<
      string,
      Array<{ option: string; probability: number; chosen: boolean }>
    > = {
      "Analyzing symptoms": [
        {
          option: "Database connection issue",
          probability: 0.87,
          chosen: true,
        },
        { option: "Network partition", probability: 0.23, chosen: false },
        { option: "Memory exhaustion", probability: 0.15, chosen: false },
      ],
      "Identifying root cause": [
        { option: "Slow query cascade", probability: 0.94, chosen: true },
        { option: "Connection pool leak", probability: 0.31, chosen: false },
        { option: "Lock contention", probability: 0.18, chosen: false },
      ],
      "Planning remediation": [
        { option: "Kill query + Scale pool", probability: 0.96, chosen: true },
        { option: "Restart database", probability: 0.12, chosen: false },
        { option: "Scale horizontally", probability: 0.45, chosen: false },
      ],
    };
    return alternatives[step] || [];
  };

  const simulateAgentCommunication = (
    from: string,
    to: string,
    messageType: string
  ) => {
    const communication: AgentCommunication = {
      id: `${from}-${to}-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      from,
      to,
      message: `${messageType} communication`,
      messageType,
      confidence: Math.random() * 0.3 + 0.7,
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

  // Simulated agent reasoning function
  const simulateAgentReasoning = useCallback(
    (agent: string, step: string, evidence: string[], confidence: number) => {
      const reasoning: AgentReasoning = {
        id: `${agent}-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        agent,
        message: `${step} - Confidence: ${(confidence * 100).toFixed(1)}%`,
        confidence,
        reasoning: `Analyzing ${step.toLowerCase()} with ${(
          confidence * 100
        ).toFixed(1)}% confidence based on evidence`,
        step,
        explanation: `${agent} agent processing ${step} with high confidence based on system metrics`,
        evidence,
        alternatives: generateAlternatives(step),
        riskAssessment: 1 - confidence,
      };

      setAgentReasonings((prev) => [reasoning, ...prev]);
      setConfidenceScores((prev) => ({ ...prev, [agent]: confidence }));
    },
    []
  );

  // Load cached AWS-generated scenario
  const loadCachedScenario = useCallback(async (scenarioType: string) => {
    try {
      const response = await fetch(`/scenarios/${scenarioType}.json`);
      if (response.ok) {
        const data = await response.json();
        setCachedScenario(data);
        setScenarioMetadata(data.metadata);

        // Load AWS-generated agent reasonings if available
        if (data.agent_reasonings && data.agent_reasonings.length > 0) {
          console.log("✓ Loaded AWS-generated reasonings from cache");
        }

        return data;
      }
    } catch (error) {
      console.warn("Failed to load cached scenario, using simulated data:", error);
    }
    return null;
  }, []);

  // Main incident trigger function
  const triggerIncident = useCallback(async () => {
    if (incidentActive) return;

    setIncidentActive(true);
    setMttrSeconds(0);
    setCurrentPhase("detection");
    setAgentReasonings([]);
    setAgentCommunications([]);
    setConfidenceScores({});

    // Check if we have cached AWS-generated scenario data
    const useAwsData = cachedScenario && cachedScenario.agent_reasonings;

    if (useAwsData) {
      console.log("✓ Using AWS-generated scenario data from cache");

      // Load AWS-generated agent reasonings progressively
      const reasonings = cachedScenario.agent_reasonings;
      for (let i = 0; i < reasonings.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        setAgentReasonings((prev) => [reasonings[i], ...prev]);

        // Update confidence scores
        setConfidenceScores((prev) => ({
          ...prev,
          [reasonings[i].agent]: reasonings[i].confidence,
        }));
      }

      // Load AWS-generated decision tree
      if (cachedScenario.decision_tree) {
        setDecisionTree(cachedScenario.decision_tree);
      }

      // Load AWS-generated communications
      if (cachedScenario.agent_communications) {
        setAgentCommunications(cachedScenario.agent_communications);
      }

      // Load AWS-generated metrics
      if (cachedScenario.performance_metrics) {
        setPerformanceMetrics(cachedScenario.performance_metrics);
      }

      setTimeout(() => {
        setCurrentPhase("complete");
        setIncidentActive(false);
      }, reasonings.length * 2000 + 1000);

      return;
    }

    // Fallback to simulated data if no AWS data available
    // Phase 1: Detection
    simulateAgentReasoning(
      "Detection",
      "Analyzing symptoms",
      [
        "Connection pool: 500/500 (100% utilization)",
        "Error rate: 47% (baseline: 0.1%)",
        "Response time: 8.5s (baseline: 120ms)",
      ],
      0.92
    );

    await new Promise((resolve) => setTimeout(resolve, 2000));
    simulateAgentCommunication("Detection", "Diagnosis", "evidence_sharing");

    // Phase 2: Diagnosis
    setTimeout(() => {
      setCurrentPhase("diagnosis");
      simulateAgentReasoning(
        "Diagnosis",
        "Identifying root cause",
        [
          "Query analytics_rollup running 47s",
          "12 queries blocked in queue",
          "Lock wait timeout exceeded",
        ],
        0.94
      );

      const tree: DecisionTree = {
        rootNode: {
          id: "root",
          nodeType: "analysis",
          label: "N+1 query pattern in authentication service",
          confidence: 0.88,
          children: [
            {
              id: "immediate",
              nodeType: "action",
              label: "Immediate Response",
              confidence: 0.95,
              children: [
                {
                  id: "scale",
                  nodeType: "execution",
                  label: "Scale Connection Pool",
                  confidence: 0.92,
                },
              ],
            },
            {
              id: "longterm",
              nodeType: "action",
              label: "Long-term Fix",
              confidence: 0.87,
              children: [
                {
                  id: "optimize",
                  nodeType: "execution",
                  label: "Optimize Query Patterns",
                  confidence: 0.91,
                },
              ],
            },
          ],
        },
        totalNodes: 5,
        maxDepth: 3,
      };

      setDecisionTree(tree);
      simulateAgentCommunication(
        "Diagnosis",
        "Resolution",
        "consensus_building"
      );
    }, 3000);

    // Phase 3: Consensus
    setTimeout(() => {
      setCurrentPhase("consensus");
      simulateAgentReasoning(
        "Prediction",
        "Forecasting impact",
        ["Dual approach success rate: 96%", "Expected MTTR: 45-60 seconds"],
        0.96
      );
    }, 5000);

    // Phase 4: Resolution
    setTimeout(() => {
      setCurrentPhase("resolution");
      simulateAgentReasoning(
        "Resolution",
        "Executing remediation",
        ["Query terminated successfully", "Connection pool scaling initiated"],
        0.98
      );

      const metrics: PerformanceMetrics = {
        mttr: 147,
        detectionTime: 15,
        resolutionTime: 45,
        agentEfficiency: 0.92,
        accuracy: 0.95,
        confidenceCalibration: 0.88,
      };
      setPerformanceMetrics(metrics);
    }, 7000);

    // Phase 5: Complete
    setTimeout(() => {
      setCurrentPhase("complete");
      setIncidentActive(false);
    }, 9000);
  }, [incidentActive, simulateAgentReasoning, cachedScenario]);

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

  // Load cached scenario when selection changes
  useEffect(() => {
    if (!showCustomInput && selectedScenario) {
      loadCachedScenario(selectedScenario);
    }
  }, [selectedScenario, showCustomInput, loadCachedScenario]);

  // Auto-demo effect - Reduced delay for better demo experience
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("auto-demo") === "true" && !incidentActive) {
      const timer = setTimeout(() => {
        triggerIncident();
      }, 1000); // Reduced from 3000ms to 1000ms
      return () => clearTimeout(timer);
    }
  }, [incidentActive, triggerIncident]);

  return (
    <DashboardLayout
      title="AI Transparency Dashboard"
      subtitle="Complete AI explainability for incident response - Deep technical demonstration"
      icon="🧠"
    >
      {/* Status Bar */}
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
          </div>
          <div className="flex-1 mx-6">
            <Progress value={getPhaseProgress()} className="h-2" />
          </div>
          <Button
            onClick={triggerIncident}
            disabled={incidentActive}
            className="bg-red-600 hover:bg-red-700 focus-ring-primary focus-ring-primary"
          >
            {incidentActive ? "Analyzing..." : "🚨 Trigger Demo"}
          </Button>
        </div>
      </DashboardSection>

      {/* AWS Attribution Badge */}
      {scenarioMetadata && (
        <DashboardSection variant="glass" className="mb-4">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-orange-500/20 text-orange-200 border-orange-500/50">
                🧠 AWS-Generated Scenario
              </Badge>
              <span className="text-slate-400">
                Generated: {new Date(scenarioMetadata.generated_at).toLocaleDateString()}
              </span>
              {scenarioMetadata.aws_services_used && scenarioMetadata.aws_services_used.length > 0 && (
                <span className="text-slate-400">
                  Services: {scenarioMetadata.aws_services_used.join(", ") || "Cached Demo Data"}
                </span>
              )}
            </div>
            <Badge variant="default" className="bg-purple-500/20 text-purple-200 border-purple-500/50">
              Phase 0: Hybrid Approach
            </Badge>
          </div>
        </DashboardSection>
      )}

      {/* Scenario Selection */}
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

        {/* Custom Scenario */}
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
              Describe your own incident
            </p>
          </div>
        </div>

        {showCustomInput && (
          <textarea
            value={customScenario}
            onChange={(e) => setCustomScenario(e.target.value)}
            placeholder="Describe your incident scenario..."
            className="w-full mt-4 p-3 bg-slate-700 border border-slate-600 rounded-lg text-sm"
            rows={3}
          />
        )}
      </DashboardSection>

      {/* Enhanced V2 Visual Proof Components */}
      <DashboardSection variant="glass" className="mb-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Predictive Prevention Demo */}
          <PredictivePreventionDemo
            className="w-full"
            onPreventionComplete={() => {
              // Prevention demo completed - could track analytics here
            }}
          />

          {/* Byzantine Fault Tolerance Demo */}
          <ByzantineConsensusDemo className="w-full" />
        </div>
      </DashboardSection>

      {/* Main Transparency Tabs */}
      <Tabs defaultValue="reasoning" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 card-glass">
          <TabsTrigger value="reasoning" data-testid="tab-reasoning">
            Reasoning
          </TabsTrigger>
          <TabsTrigger value="decisions" data-testid="tab-decisions">
            Decisions
          </TabsTrigger>
          <TabsTrigger value="confidence" data-testid="tab-confidence">
            Confidence
          </TabsTrigger>
          <TabsTrigger value="communication" data-testid="tab-communication">
            Communication
          </TabsTrigger>
          <TabsTrigger value="analytics" data-testid="tab-analytics">
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Reasoning Tab - Enhanced with new ReasoningPanel */}
        <TabsContent value="reasoning" data-testid="panel-reasoning">
          <ReasoningPanel
            reasoningSteps={agentReasonings}
            onStepClick={(step) => {
              // Could track reasoning step interactions for analytics
            }}
            className="w-full"
          />
        </TabsContent>

        {/* Decision Trees Tab - Enhanced with new DecisionTreeVisualization */}
        <TabsContent value="decisions" data-testid="panel-decisions">
          {decisionTree ? (
            <DecisionTreeVisualization
              rootNode={decisionTree.rootNode}
              onNodeClick={(node) => {
                // Could track decision node interactions for analytics
              }}
              className="w-full"
            />
          ) : (
            <Card className="card-glass">
              <CardContent className="py-12">
                <div className="text-center text-status-neutral">
                  <div className="text-4xl mb-3">🌳</div>
                  <h3 className="text-lg font-medium mb-2">
                    No Decision Tree Yet
                  </h3>
                  <p className="text-sm">
                    Decision tree will appear during analysis phase
                  </p>
                  <p className="text-xs mt-2 text-slate-500">
                    Click '🚨 Trigger Demo&apos; to see interactive decision
                    tree visualization
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Confidence Tab */}
        <TabsContent value="confidence" data-testid="panel-confidence">
          <Card className="card-glass">
            <CardHeader>
              <CardTitle>📈 Confidence & Uncertainty Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(confidenceScores).map(([agent, confidence]) => (
                  <div
                    key={agent}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm font-medium">{agent}</span>
                    <ConfidenceScore
                      confidence={confidence}
                      size="md"
                      className="flex-1 ml-4"
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Communication Tab - Enhanced with new CommunicationPanel */}
        <TabsContent value="communication" data-testid="panel-communication">
          <CommunicationPanel
            messages={agentCommunications}
            onMessageClick={(message) => {
              // Could track communication message interactions for analytics
            }}
            className="w-full"
          />
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" data-testid="panel-analytics">
          <Card className="card-glass">
            <CardHeader>
              <CardTitle>📊 Performance Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              {!performanceMetrics ? (
                <div className="text-center text-status-neutral py-8">
                  <div className="text-3xl mb-2">📊</div>
                  <p>Performance metrics will appear during resolution...</p>
                  <p className="text-xs mt-2">
                    No metrics yet — click &apos;🚨 Trigger Demo&apos; to
                    generate a live sample
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  <div className="spacing-md bg-slate-700/20 backdrop-blur-sm rounded-lg">
                    <div className="text-sm text-status-neutral">MTTR</div>
                    <div className="text-2xl font-mono text-green-400">
                      {performanceMetrics.mttr}s
                    </div>
                  </div>
                  <div className="spacing-md bg-slate-700/20 backdrop-blur-sm rounded-lg">
                    <div className="text-sm text-status-neutral">Accuracy</div>
                    <div className="text-2xl font-mono text-green-400">
                      {((performanceMetrics.accuracy || 0.95) * 100).toFixed(1)}
                      %
                    </div>
                  </div>
                  <div className="spacing-md bg-slate-700/20 backdrop-blur-sm rounded-lg">
                    <div className="text-sm text-status-neutral">
                      Detection Time
                    </div>
                    <div className="text-2xl font-mono text-blue-400">
                      {performanceMetrics.detectionTime}s
                    </div>
                  </div>
                  <div className="spacing-md bg-slate-700/20 backdrop-blur-sm rounded-lg">
                    <div className="text-sm text-status-neutral">
                      Resolution Time
                    </div>
                    <div className="text-2xl font-mono text-blue-400">
                      {performanceMetrics.resolutionTime}s
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  );
}
