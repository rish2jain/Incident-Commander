"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../src/components/ui/card";
import { Button } from "../../src/components/ui/button";
import { Badge } from "../../src/components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../src/components/ui/tabs";
import { Progress } from "../../src/components/ui/progress";

// Enhanced dashboard with AI insights and transparency features
export default function InsightsDemoPage() {
  const [incidentActive, setIncidentActive] = useState(false);
  const [mttrSeconds, setMttrSeconds] = useState(0);
  const [currentPhase, setCurrentPhase] = useState("idle");
  const [agentReasonings, setAgentReasonings] = useState<any[]>([]);
  const [decisionTree, setDecisionTree] = useState<any>(null);
  const [confidenceScores, setConfidenceScores] = useState<any>({});
  const [agentCommunications, setAgentCommunications] = useState<any[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>({});

  // Agent reasoning simulation
  const simulateAgentReasoning = (
    agent: string,
    step: string,
    evidence: string[],
    confidence: number
  ) => {
    const reasoning = {
      id: Date.now().toString(),
      agent,
      step,
      evidence,
      confidence,
      timestamp: new Date().toLocaleTimeString(),
      alternatives: generateAlternatives(step),
      riskAssessment: calculateRisk(step, confidence),
    };

    setAgentReasonings((prev: any[]) => [reasoning, ...prev]);
    setConfidenceScores((prev: Record<string, number>) => ({
      ...prev,
      [agent]: confidence,
    }));
  };

  const generateAlternatives = (step: string) => {
    const alternatives = {
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
    return (alternatives as any)[step] || [];
  };

  const calculateRisk = (step: string, confidence: number) => {
    const baseRisk = 1 - confidence;
    const stepRisk = {
      "Analyzing symptoms": 0.1,
      "Identifying root cause": 0.3,
      "Planning remediation": 0.5,
    };
    return Math.min(baseRisk + ((stepRisk as any)[step] || 0.2), 1);
  };

  const simulateAgentCommunication = (
    from: string,
    to: string,
    message: string,
    type: string
  ) => {
    const communication = {
      id: Date.now().toString(),
      from,
      to,
      message,
      type,
      timestamp: new Date().toLocaleTimeString(),
      confidence: Math.random() * 0.3 + 0.7,
    };

    setAgentCommunications((prev: any[]) => [communication, ...prev]);
  };

  const updateDecisionTree = (decision: any) => {
    setDecisionTree(decision);
  };

  const triggerEnhancedIncident = useCallback(async () => {
    if (incidentActive) return;

    setIncidentActive(true);
    setMttrSeconds(0);
    setCurrentPhase("detection");
    setAgentReasonings([]);

    // Capture current MTTR for use in async operations
    let currentMttr = 0;
    setAgentCommunications([]);
    setConfidenceScores({});

    // Phase 1: Detection with reasoning
    simulateAgentReasoning(
      "Detection",
      "Analyzing symptoms",
      [
        "Connection pool: 500/500 (100% utilization)",
        "Error rate: 47% (baseline: 0.1%)",
        "Response time: 8.5s (baseline: 120ms)",
        "Pattern matches: Database cascade (87% similarity)",
      ],
      0.89
    );

    await new Promise((resolve) => setTimeout(resolve, 3000));

    simulateAgentCommunication(
      "Detection",
      "Diagnosis",
      "High confidence database cascade detected. Escalating for root cause analysis.",
      "escalation"
    );

    // Phase 2: Diagnosis with decision tree
    setCurrentPhase("diagnosis");
    simulateAgentReasoning(
      "Diagnosis",
      "Identifying root cause",
      [
        "Query analytics_daily_rollup_20251019 running 47s",
        "12 queries blocked in queue",
        "Lock wait timeout exceeded",
        "Historical pattern: 94% match to slow query cascade",
      ],
      0.94
    );

    updateDecisionTree({
      root: "Database Performance Issue",
      branches: [
        {
          condition: "Query Duration > 30s",
          probability: 0.94,
          chosen: true,
          action: "Kill slow query",
          children: [
            {
              condition: "Pool utilization > 90%",
              probability: 0.96,
              chosen: true,
              action: "Scale connection pool",
            },
            {
              condition: "Memory usage normal",
              probability: 0.85,
              chosen: false,
              action: "Monitor only",
            },
          ],
        },
        {
          condition: "Connection leak detected",
          probability: 0.31,
          chosen: false,
          action: "Restart connections",
          children: [],
        },
      ],
    });

    await new Promise((resolve) => setTimeout(resolve, 4000));

    simulateAgentCommunication(
      "Diagnosis",
      "Prediction",
      "Root cause: Slow query cascade. Recommending dual remediation approach.",
      "recommendation"
    );

    // Phase 3: Prediction and consensus
    setCurrentPhase("consensus");
    simulateAgentReasoning(
      "Prediction",
      "Forecasting impact",
      [
        "Dual approach success rate: 96%",
        "Query kill impact: Minimal (read-only operation)",
        "Pool scaling time: 8-12 seconds",
        "Expected MTTR: 45-60 seconds",
      ],
      0.96
    );

    simulateAgentCommunication(
      "Prediction",
      "Resolution",
      "96% confidence in dual remediation. Minimal risk assessment.",
      "consensus"
    );

    await new Promise((resolve) => setTimeout(resolve, 3000));

    // Phase 4: Resolution execution
    setCurrentPhase("resolution");
    simulateAgentReasoning(
      "Resolution",
      "Executing remediation",
      [
        "Query terminated successfully (0.3s)",
        "Connection pool scaling initiated",
        "Monitoring recovery metrics",
        "No rollback triggers detected",
      ],
      0.98
    );

    await new Promise((resolve) => setTimeout(resolve, 5000));

    // Phase 5: Verification
    setCurrentPhase("verification");
    simulateAgentReasoning(
      "Communication",
      "Verifying resolution",
      [
        "Error rate: 0.1% (normal)",
        "Response time: 118ms (normal)",
        "Connection utilization: 12.7%",
        "All systems nominal",
      ],
      0.99
    );

    simulateAgentCommunication(
      "Communication",
      "All",
      "Incident resolved successfully. All metrics within normal parameters.",
      "resolution"
    );

    // Calculate total time (3000 + 4000 + 3000 + 5000 = 15000ms = 15 seconds)
    currentMttr = 15;

    // Update performance metrics
    setPerformanceMetrics({
      mttr: currentMttr,
      accuracy: 0.96,
      confidenceCalibration: 0.94,
      consensusTime: 12,
      learningGain: 0.03,
    });

    setTimeout(() => {
      setIncidentActive(false);
      setCurrentPhase("idle");
    }, 2000);
  }, [incidentActive]);

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
        triggerEnhancedIncident();
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [incidentActive, triggerEnhancedIncident]);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          🧠 AI Insights & Transparency Dashboard
        </h1>
        <p className="text-slate-400">
          Enhanced interpretability and explainable AI for incident response
        </p>
      </div>

      {/* Status Bar */}
      <Card className="bg-slate-800/50 border-slate-700 mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge variant={incidentActive ? "destructive" : "default"}>
                {incidentActive ? `Phase: ${currentPhase}` : "System Ready"}
              </Badge>
              <div className="text-sm text-slate-400">
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
              onClick={triggerEnhancedIncident}
              disabled={incidentActive}
              className="bg-red-600 hover:bg-red-700"
            >
              {incidentActive ? "Analyzing..." : "🚨 Trigger Enhanced Demo"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Insights Dashboard */}
      <Tabs defaultValue="reasoning" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 bg-slate-800/50">
          <TabsTrigger value="reasoning">Agent Reasoning</TabsTrigger>
          <TabsTrigger value="decisions">Decision Trees</TabsTrigger>
          <TabsTrigger value="confidence">Confidence</TabsTrigger>
          <TabsTrigger value="communication">Communication</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Agent Reasoning Tab */}
        <TabsContent value="reasoning" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  🧠 Agent Reasoning Process
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {agentReasonings.length === 0 ? (
                    <div className="text-center text-slate-400 py-8">
                      <div className="text-4xl mb-2">🤔</div>
                      <p>Trigger incident to see agent reasoning...</p>
                    </div>
                  ) : (
                    agentReasonings.map((reasoning: any) => (
                      <div
                        key={reasoning.id}
                        className="border border-slate-600 rounded-lg p-4"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{reasoning.agent}</Badge>
                            <span className="text-sm text-slate-400">
                              {reasoning.timestamp}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400">
                              Confidence:
                            </span>
                            <Badge
                              variant={
                                reasoning.confidence > 0.8
                                  ? "default"
                                  : "secondary"
                              }
                            >
                              {(reasoning.confidence * 100).toFixed(1)}%
                            </Badge>
                          </div>
                        </div>

                        <h4 className="font-semibold mb-2">{reasoning.step}</h4>

                        <div className="mb-3">
                          <p className="text-sm text-slate-400 mb-1">
                            Evidence considered:
                          </p>
                          <ul className="text-sm space-y-1">
                            {reasoning.evidence.map(
                              (item: string, idx: number) => (
                                <li
                                  key={idx}
                                  className="flex items-start gap-2"
                                >
                                  <span className="text-blue-400">•</span>
                                  <span>{item}</span>
                                </li>
                              )
                            )}
                          </ul>
                        </div>

                        {reasoning.alternatives.length > 0 && (
                          <div className="mb-3">
                            <p className="text-sm text-slate-400 mb-2">
                              Alternatives considered:
                            </p>
                            <div className="space-y-1">
                              {reasoning.alternatives.map(
                                (alt: any, idx: number) => (
                                  <div
                                    key={idx}
                                    className={`text-sm p-2 rounded ${
                                      alt.chosen
                                        ? "bg-green-500/20 border border-green-500/30"
                                        : "bg-slate-700/30"
                                    }`}
                                  >
                                    <div className="flex justify-between items-center">
                                      <span>{alt.option}</span>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs">
                                          {(alt.probability * 100).toFixed(0)}%
                                        </span>
                                        {alt.chosen && (
                                          <span className="text-green-400">
                                            ✓
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        )}

                        <div className="flex justify-between items-center text-xs text-slate-400">
                          <span>
                            Risk Level:{" "}
                            {(reasoning.riskAssessment * 100).toFixed(1)}%
                          </span>
                          <span>
                            Processing Time: {(Math.random() * 2 + 0.5) | 0}s
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Current Agent Status */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  📊 Real-Time Agent Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    "Detection",
                    "Diagnosis",
                    "Prediction",
                    "Resolution",
                    "Communication",
                  ].map((agent: string) => (
                    <div
                      key={agent}
                      className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-3 h-3 rounded-full ${
                            confidenceScores[agent]
                              ? "bg-green-400"
                              : "bg-slate-500"
                          }`}
                        />
                        <span className="font-medium">{agent}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        {confidenceScores[agent] && (
                          <>
                            <Progress
                              value={confidenceScores[agent] * 100}
                              className="w-20 h-2"
                            />
                            <span className="text-sm font-mono">
                              {(confidenceScores[agent] * 100).toFixed(1)}%
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Decision Trees Tab */}
        <TabsContent value="decisions" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🌳 Interactive Decision Tree
              </CardTitle>
            </CardHeader>
            <CardContent>
              {decisionTree ? (
                <div className="space-y-4">
                  <div className="text-center p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                    <h3 className="font-bold text-lg">{decisionTree.root}</h3>
                  </div>

                  <div className="space-y-3">
                    {decisionTree.branches.map((branch: any, idx: number) => (
                      <div
                        key={idx}
                        className={`p-4 rounded-lg border ${
                          branch.chosen
                            ? "bg-green-500/20 border-green-500/30"
                            : "bg-slate-700/30 border-slate-600"
                        }`}
                      >
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium">
                            {branch.condition}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm">
                              P: {(branch.probability * 100).toFixed(0)}%
                            </span>
                            {branch.chosen && (
                              <span className="text-green-400">✓ Chosen</span>
                            )}
                          </div>
                        </div>

                        <div className="text-sm text-slate-300 mb-2">
                          Action:{" "}
                          <span className="font-medium">{branch.action}</span>
                        </div>

                        {branch.children.length > 0 && (
                          <div className="ml-4 space-y-2 border-l-2 border-slate-600 pl-4">
                            {branch.children.map(
                              (child: any, childIdx: number) => (
                                <div
                                  key={childIdx}
                                  className={`p-2 rounded text-sm ${
                                    child.chosen
                                      ? "bg-green-500/10"
                                      : "bg-slate-700/20"
                                  }`}
                                >
                                  <div className="flex justify-between items-center">
                                    <span>{child.condition}</span>
                                    <div className="flex items-center gap-2">
                                      <span>
                                        P:{" "}
                                        {(child.probability * 100).toFixed(0)}%
                                      </span>
                                      {child.chosen && (
                                        <span className="text-green-400">
                                          ✓
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="text-slate-400">
                                    → {child.action}
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center text-slate-400 py-12">
                  <div className="text-4xl mb-2">🌳</div>
                  <p>Decision tree will appear during incident analysis...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Confidence Tab */}
        <TabsContent value="confidence" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle>📈 Confidence Evolution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(confidenceScores).map(
                    ([agent, confidence]) => (
                      <div key={agent} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">{agent}</span>
                          <span className="text-sm font-mono">
                            {((confidence as number) * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress
                          value={(confidence as number) * 100}
                          className="h-3"
                        />
                        <div className="flex justify-between text-xs text-slate-400">
                          <span>
                            Calibration:{" "}
                            {(0.85 + Math.random() * 0.1).toFixed(2)}
                          </span>
                          <span>
                            Uncertainty:{" "}
                            {((1 - (confidence as number)) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle>🎯 Confidence Calibration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-sm text-slate-400 mb-4">
                    How well agent confidence matches actual accuracy
                  </div>

                  {["Detection", "Diagnosis", "Prediction", "Resolution"].map(
                    (agent) => (
                      <div key={agent} className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm">{agent}</span>
                          <span className="text-sm font-mono">
                            {(0.88 + Math.random() * 0.1).toFixed(2)}
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full"
                            style={{ width: `${88 + Math.random() * 10}%` }}
                          />
                        </div>
                      </div>
                    )
                  )}

                  <div className="mt-4 p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                    <div className="text-sm">
                      <div className="font-medium mb-1">
                        Calibration Quality: Excellent
                      </div>
                      <div className="text-slate-300">
                        Agents show well-calibrated confidence scores with
                        minimal overconfidence bias.
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Communication Tab */}
        <TabsContent value="communication" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                💬 Inter-Agent Communication
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {agentCommunications.length === 0 ? (
                  <div className="text-center text-slate-400 py-8">
                    <div className="text-4xl mb-2">💬</div>
                    <p>Agent communications will appear here...</p>
                  </div>
                ) : (
                  agentCommunications.map((comm: any) => (
                    <div
                      key={comm.id}
                      className={`p-4 rounded-lg border ${
                        comm.type === "escalation"
                          ? "border-red-500/30 bg-red-500/10"
                          : comm.type === "consensus"
                          ? "border-green-500/30 bg-green-500/10"
                          : comm.type === "recommendation"
                          ? "border-blue-500/30 bg-blue-500/10"
                          : "border-slate-600 bg-slate-700/30"
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{comm.from}</Badge>
                          <span className="text-slate-400">→</span>
                          <Badge variant="outline">{comm.to}</Badge>
                          <Badge variant="secondary" className="text-xs">
                            {comm.type}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <span>{comm.timestamp}</span>
                          <span>
                            Conf: {(comm.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-sm">{comm.message}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-lg">
                  📊 Performance Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Accuracy</span>
                    <span className="font-mono text-green-400">
                      {((performanceMetrics.accuracy || 0.96) * 100).toFixed(1)}
                      %
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Calibration</span>
                    <span className="font-mono text-blue-400">
                      {(
                        (performanceMetrics.confidenceCalibration || 0.94) * 100
                      ).toFixed(1)}
                      %
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">
                      Consensus Time
                    </span>
                    <span className="font-mono text-yellow-400">
                      {performanceMetrics.consensusTime || 0}s
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">
                      Learning Gain
                    </span>
                    <span className="font-mono text-purple-400">
                      +
                      {(
                        (performanceMetrics.learningGain || 0.03) * 100
                      ).toFixed(1)}
                      %
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-lg">🎯 Bias Detection</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Confirmation Bias</span>
                    <Badge variant="default" className="bg-green-600">
                      Low
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Availability Bias</span>
                    <Badge variant="default" className="bg-green-600">
                      Low
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Anchoring Bias</span>
                    <Badge variant="secondary">Medium</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Overconfidence</span>
                    <Badge variant="default" className="bg-green-600">
                      Low
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-lg">🧠 Learning Insights</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="p-2 bg-blue-500/20 rounded">
                    <div className="font-medium">Pattern Recognition</div>
                    <div className="text-slate-300">
                      Improved database cascade detection by 3.2%
                    </div>
                  </div>
                  <div className="p-2 bg-green-500/20 rounded">
                    <div className="font-medium">Decision Speed</div>
                    <div className="text-slate-300">
                      Reduced analysis time by 1.8s
                    </div>
                  </div>
                  <div className="p-2 bg-purple-500/20 rounded">
                    <div className="font-medium">Accuracy Gain</div>
                    <div className="text-slate-300">
                      Overall accuracy improved by 2.1%
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
