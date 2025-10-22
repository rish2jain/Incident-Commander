/**
 * PowerDashboard Component
 *
 * Enhanced UX dashboard implementing all 10 power-demonstration recommendations:
 * 1. Pre-populated demo state showing completed analysis
 * 2. Before vs After comparison widget
 * 3. Real-time agent coordination visualization
 * 4. Live metrics counter with animated savings
 * 5. Enhanced transparency panel with side-by-side views
 * 6. Business Impact Calculator
 * 7. Incident Timeline with AI highlights
 * 8. Industry Firsts highlight panel
 * 9. Interactive hotspots and tooltips
 * 10. Predicted Incidents section
 */

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared";
import { Badge } from "@/components/shared";
import { Button } from "@/components/shared";
import { Progress } from "@/components/shared";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// Types
interface AgentState {
  id: string;
  name: string;
  status: "active" | "idle" | "complete";
  confidence: number;
  reasoning: string;
}

interface TimelineEvent {
  timestamp: string;
  agent: string;
  action: string;
  duration: number;
  icon: string;
}

interface PredictedIncident {
  id: string;
  title: string;
  confidence: number;
  action: string;
  impact: string;
  status: "monitoring" | "preventive_action" | "prevented";
}

interface LiveMetrics {
  incidentsResolved: number;
  timeSaved: string;
  costAvoided: number;
  humanInterventions: number;
  zeroTouchStreak: number;
}

export const PowerDashboard: React.FC = () => {
  // Demo mode state - pre-populated for immediate impact
  const [demoMode, setDemoMode] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(6); // Start at complete (6), or 0 for beginning
  const [animationSpeed, setAnimationSpeed] = useState(2000); // ms per step
  
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics>({
    incidentsResolved: 47,
    timeSaved: "18h 23m",
    costAvoided: 156800,
    humanInterventions: 0,
    zeroTouchStreak: 47,
  });

  const [agents, setAgents] = useState<AgentState[]>([
    {
      id: "detection",
      name: "Detection Agent",
      status: "complete",
      confidence: 0.92,
      reasoning: "CPU spike at 14:23, correlating with database queries showing N+1 pattern in auth service",
    },
    {
      id: "diagnosis",
      name: "Diagnosis Agent",
      status: "complete",
      confidence: 0.87,
      reasoning: "Connection pool exhaustion due to slow query at line 247 in UserService.authenticate()",
    },
    {
      id: "prediction",
      name: "Prediction Agent",
      status: "complete",
      confidence: 0.94,
      reasoning: "Pattern matches 127 similar incidents. 96% probability of cascade if unresolved within 3 minutes",
    },
    {
      id: "resolution",
      name: "Resolution Agent",
      status: "complete",
      confidence: 0.91,
      reasoning: "Applied dual strategy: scaled connection pool + deployed query optimization patch",
    },
    {
      id: "validation",
      name: "Validation Agent",
      status: "complete",
      confidence: 0.98,
      reasoning: "Verified resolution: CPU normalized, query time reduced 94%, no cascade detected",
    },
  ]);

  const [timeline, setTimeline] = useState<TimelineEvent[]>([
    {
      timestamp: "14:23:15",
      agent: "Detection Agent",
      action: "Anomaly detected",
      duration: 3,
      icon: "🔍",
    },
    {
      timestamp: "14:23:18",
      agent: "Diagnosis Agent",
      action: "Root cause identified",
      duration: 7,
      icon: "🧠",
    },
    {
      timestamp: "14:23:25",
      agent: "Prediction Agent",
      action: "Impact forecast complete",
      duration: 5,
      icon: "🔮",
    },
    {
      timestamp: "14:23:30",
      agent: "Consensus Engine",
      action: "3/3 agents agree (94% confidence)",
      duration: 2,
      icon: "⚖️",
    },
    {
      timestamp: "14:23:32",
      agent: "Resolution Agent",
      action: "Fix applied",
      duration: 8,
      icon: "✅",
    },
    {
      timestamp: "14:23:40",
      agent: "Validation Agent",
      action: "Issue resolved",
      duration: 7,
      icon: "✓",
    },
  ]);

  const [predictedIncidents, setPredictedIncidents] = useState<PredictedIncident[]>([
    {
      id: "1",
      title: "Memory leak in User Service",
      confidence: 0.87,
      action: "Preemptive restart at 15:00",
      impact: "Prevented $45K downtime",
      status: "preventive_action",
    },
    {
      id: "2",
      title: "Database connection spike",
      confidence: 0.72,
      action: "Scale connection pool",
      impact: "Monitoring - 30 min window",
      status: "monitoring",
    },
  ]);

  const [consensusScore, setConsensusScore] = useState(0.94);
  const [mttrCurrent, setMttrCurrent] = useState(2.47);
  const [mttrManual, setMttrManual] = useState(30.25);

  // Animated counters for live metrics
  useEffect(() => {
    if (!demoMode) return;

    const interval = setInterval(() => {
      setLiveMetrics((prev) => ({
        ...prev,
        incidentsResolved: prev.incidentsResolved + (Math.random() > 0.7 ? 1 : 0),
        costAvoided: prev.costAvoided + (Math.random() > 0.7 ? Math.floor(Math.random() * 5000) : 0),
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, [demoMode]);

  // Live incident progression animation
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= 6) {
          setIsPlaying(false);
          return 6;
        }
        return prev + 1;
      });
    }, animationSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, animationSpeed]);

  // Get agent state based on current step
  const getAgentStateForStep = (agentId: string, step: number): AgentState => {
    const fullStates: Record<string, AgentState> = {
      detection: {
        id: "detection",
        name: "Detection Agent",
        status: step >= 1 ? "complete" : "idle",
        confidence: step >= 1 ? 0.92 : 0,
        reasoning: "CPU spike at 14:23, correlating with database queries showing N+1 pattern in auth service",
      },
      diagnosis: {
        id: "diagnosis",
        name: "Diagnosis Agent",
        status: step >= 2 ? "complete" : step === 1 ? "active" : "idle",
        confidence: step >= 2 ? 0.87 : step === 1 ? 0.45 : 0,
        reasoning: "Connection pool exhaustion due to slow query at line 247 in UserService.authenticate()",
      },
      prediction: {
        id: "prediction",
        name: "Prediction Agent",
        status: step >= 3 ? "complete" : step === 2 ? "active" : "idle",
        confidence: step >= 3 ? 0.94 : step === 2 ? 0.5 : 0,
        reasoning: "Pattern matches 127 similar incidents. 96% probability of cascade if unresolved within 3 minutes",
      },
      resolution: {
        id: "resolution",
        name: "Resolution Agent",
        status: step >= 5 ? "complete" : step === 4 ? "active" : "idle",
        confidence: step >= 5 ? 0.91 : step === 4 ? 0.6 : 0,
        reasoning: "Applied dual strategy: scaled connection pool + deployed query optimization patch",
      },
      validation: {
        id: "validation",
        name: "Validation Agent",
        status: step >= 6 ? "complete" : step === 5 ? "active" : "idle",
        confidence: step >= 6 ? 0.98 : step === 5 ? 0.7 : 0,
        reasoning: "Verified resolution: CPU normalized, query time reduced 94%, no cascade detected",
      },
    };

    return fullStates[agentId];
  };

  // Get visible timeline events based on current step
  const getTimelineEventsForStep = (step: number): TimelineEvent[] => {
    const allEvents: TimelineEvent[] = [
      {
        timestamp: "14:23:15",
        agent: "Detection Agent",
        action: "Anomaly detected",
        duration: 3,
        icon: "🔍",
      },
      {
        timestamp: "14:23:18",
        agent: "Diagnosis Agent",
        action: "Root cause identified",
        duration: 7,
        icon: "🧠",
      },
      {
        timestamp: "14:23:25",
        agent: "Prediction Agent",
        action: "Impact forecast complete",
        duration: 5,
        icon: "🔮",
      },
      {
        timestamp: "14:23:30",
        agent: "Consensus Engine",
        action: "3/3 agents agree (94% confidence)",
        duration: 2,
        icon: "⚖️",
      },
      {
        timestamp: "14:23:32",
        agent: "Resolution Agent",
        action: "Fix applied",
        duration: 8,
        icon: "✅",
      },
      {
        timestamp: "14:23:40",
        agent: "Validation Agent",
        action: "Issue resolved",
        duration: 7,
        icon: "✓",
      },
    ];

    return allEvents.slice(0, step);
  };

  // Playback control functions
  const startIncidentDemo = () => {
    setCurrentStep(0);
    setIsPlaying(true);
  };

  const pauseIncidentDemo = () => {
    setIsPlaying(false);
  };

  const resumeIncidentDemo = () => {
    if (currentStep < 6) {
      setIsPlaying(true);
    }
  };

  const resetIncidentDemo = () => {
    setCurrentStep(0);
    setIsPlaying(false);
  };

  const skipToEnd = () => {
    setCurrentStep(6);
    setIsPlaying(false);
  };

  // Calculate business impact for current incident
  const calculateBusinessImpact = () => {
    const costPerMinute = 10000;
    const severityCost = {
      CRITICAL: costPerMinute,
      HIGH: costPerMinute * 0.5,
      MEDIUM: costPerMinute * 0.25,
    };

    const manualCost = mttrManual * costPerMinute;
    const aiCost = mttrCurrent * costPerMinute;
    const saved = manualCost - aiCost;

    return {
      manualCost,
      aiCost,
      saved,
      improvement: ((saved / manualCost) * 100).toFixed(1),
    };
  };

  const impact = calculateBusinessImpact();

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 text-white p-6">
        <div className="max-w-[1800px] mx-auto space-y-6">
          {/* HERO METRICS - Make Power Immediately Visible */}
          <Card className="bg-gradient-to-r from-blue-900/40 to-purple-900/40 border-blue-500/50">
            <CardContent className="spacing-xl">
              <div className="text-center mb-6">
                <h1 className="text-5xl font-semibold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  {liveMetrics.incidentsResolved} Incidents Resolved Today
                </h1>
                <p className="text-xl text-slate-300">
                  Zero human interventions • {formatCurrency(liveMetrics.costAvoided)} saved • System uptime: 99.97%
                </p>
                <div className="mt-4 flex justify-center items-center gap-3">
                  <Badge variant="default" className="text-lg px-4 py-2 bg-green-600">
                    🔥 {liveMetrics.zeroTouchStreak} Zero-Touch Streak
                  </Badge>
                  <Badge variant="outline" className="text-lg px-4 py-2">
                    ⚡ Avg Resolution: {mttrCurrent}min (91% faster)
                  </Badge>
                </div>
              </div>

              {/* Demo Mode Banner */}
              {demoMode && (
                <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 text-center">
                  <p className="text-yellow-200 font-semibold">
                    💡 Demo Mode: Showing completed Database Cascade Failure resolution
                  </p>
                  <p className="text-sm text-yellow-300/80 mt-1">
                    Resolved in 2:47 (Target: &lt;3min) • ✓ 5/5 Agents Collaborated • Byzantine Consensus: 94%
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* FOUR COLUMN LAYOUT */}
          <div className="grid grid-cols-4 gap-6">
            {/* COLUMN 1: System Status & Live Savings */}
            <div className="space-y-6">
              {/* Live Savings Counter */}
              <Card className="card-glass">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    ⏱️ <span>LIVE SAVINGS TODAY</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                    <span className="text-slate-400">Incidents Resolved:</span>
                    <span className="text-2xl font-semibold text-metric-positive">{liveMetrics.incidentsResolved}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                    <span className="text-slate-400">Time Saved:</span>
                    <span className="text-2xl font-semibold text-blue-400">{liveMetrics.timeSaved}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                    <span className="text-slate-400">Cost Avoided:</span>
                    <span className="text-2xl font-semibold text-purple-400">{formatCurrency(liveMetrics.costAvoided)}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                    <span className="text-slate-400">Human Interventions:</span>
                    <span className="text-2xl font-semibold text-green-400">{liveMetrics.humanInterventions}</span>
                  </div>
                  <div className="pt-2 border-t-2 border-green-500/50">
                    <div className="text-center">
                      <p className="text-sm text-slate-400 mb-1">Current Streak</p>
                      <p className="text-3xl font-semibold text-green-400">🔥 {liveMetrics.zeroTouchStreak}</p>
                      <p className="text-xs text-green-300">Zero-Touch Resolutions</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Agent Status with Interactive Tooltips */}
              <Card className="card-glass">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">🤖 Multi-Agent Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {["detection", "diagnosis", "prediction", "resolution", "validation"].map((agentId) => {
                    const agent = getAgentStateForStep(agentId, currentStep);
                    return (
                      <Tooltip key={agent.id}>
                        <TooltipTrigger asChild>
                          <div className={`p-3 rounded-lg cursor-help transition-all duration-500 ${
                            agent.status === "active" ? "bg-blue-600/30 ring-2 ring-blue-400 animate-pulse" :
                            agent.status === "complete" ? "bg-slate-800/50 hover:bg-slate-800" :
                            "bg-slate-800/30 opacity-50"
                          }`}>
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-semibold text-sm">{agent.name}</span>
                              <Badge
                                variant={agent.status === "complete" ? "default" : "secondary"}
                                className={`transition-all duration-300 ${
                                  agent.status === "complete" ? "bg-green-600" :
                                  agent.status === "active" ? "bg-blue-600 animate-pulse" :
                                  "opacity-30"
                                }`}
                              >
                                {agent.status === "complete" ? "✓" : agent.status === "active" ? "⚡" : "○"}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Progress value={agent.confidence * 100} className="flex-1 h-2" />
                              <span className={`text-xs font-mono transition-all duration-300 ${
                                agent.confidence > 0 ? "text-green-400" : "text-slate-600"
                              }`}>
                                {(agent.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs bg-slate-800 border-blue-500/50">
                          <p className="font-semibold mb-1">{agent.name} Reasoning:</p>
                          <p className="text-sm text-slate-300">{agent.reasoning}</p>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </CardContent>
              </Card>

              {/* Industry Firsts */}
              <Card className="bg-gradient-to-br from-amber-900/30 to-orange-900/30 border-amber-500/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">🏆 INDUSTRY FIRSTS</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>Byzantine fault-tolerant consensus</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>Predictive incident prevention</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>Zero-touch resolution</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>Self-improving via RAG memory</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>8/8 AWS AI services integrated</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>Complete decision transparency</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* COLUMN 2: Active Incident & Timeline */}
            <div className="space-y-6">
              {/* Before vs After Comparison */}
              <Card className="card-glass">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">📊 IMPACT COMPARISON</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-3 bg-red-900/20 rounded-lg border border-red-500/30">
                      <div>
                        <p className="text-sm text-slate-400">Manual Response</p>
                        <p className="text-2xl font-semibold text-red-400">{mttrManual}m</p>
                      </div>
                      <span className="text-4xl">😰</span>
                    </div>

                    <div className="flex justify-between items-center p-3 bg-green-900/20 rounded-lg border border-green-500/30">
                      <div>
                        <p className="text-sm text-slate-400">AI Response</p>
                        <p className="text-2xl font-semibold text-green-400">{mttrCurrent}m</p>
                      </div>
                      <span className="text-4xl">✓</span>
                    </div>
                  </div>

                  <div className="border-t border-gray-700 pt-3 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Improvement:</span>
                      <span className="text-xl font-semibold text-green-400">91% faster</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Downtime Saved:</span>
                      <span className="text-lg font-semibold text-blue-400">
                        {(mttrManual - mttrCurrent).toFixed(1)} minutes
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Incident Timeline */}
              <Card className="card-glass">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">⏰ INCIDENT TIMELINE</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {getTimelineEventsForStep(currentStep).map((event, index) => (
                      <div key={index} className="flex items-start gap-3 relative">
                        {index < getTimelineEventsForStep(currentStep).length - 1 && (
                          <div className="absolute left-[15px] top-8 bottom-[-12px] w-0.5 bg-blue-500/30"></div>
                        )}
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center z-10 flex-shrink-0">
                          <span className="text-sm">{event.icon}</span>
                        </div>
                        <div className="flex-1 pt-1">
                          <div className="flex justify-between items-start mb-1">
                            <span className="font-medium text-sm">{event.agent}</span>
                            <span className="text-xs text-slate-500">{event.timestamp}</span>
                          </div>
                          <p className="text-sm text-slate-400">{event.action}</p>
                          <p className="text-xs text-green-400 mt-1">{event.duration}s</p>
                        </div>
                      </div>
                    ))}
                    <div className="border-t border-green-500/50 pt-3 mt-4">
                      <div className="text-center">
                        <p className="text-sm text-slate-400">Total Resolution Time</p>
                        <p className="text-3xl font-semibold text-green-400">
                          {getTimelineEventsForStep(currentStep).reduce((sum, event) => sum + event.duration, 0)}s
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          vs 30+ minutes manual (98.6% faster)
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* COLUMN 3: AI Reasoning & Decision Tree */}
            <div className="space-y-6">
              {/* Agent Coordination Visualization */}
              <Card className="card-glass">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">🔄 AGENT COORDINATION</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Flow Diagram */}
                    <div className="relative spacing-md bg-slate-800/50 rounded-lg">
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="px-3 py-1 bg-blue-600 rounded text-sm font-semibold">
                            Detection
                          </div>
                          <div className="flex-1 h-0.5 bg-blue-500/50"></div>
                          <span className="text-xs text-slate-400">92%</span>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <div className="px-3 py-1 bg-purple-600 rounded text-sm font-semibold">
                            Diagnosis
                          </div>
                          <div className="flex-1 h-0.5 bg-purple-500/50"></div>
                          <span className="text-xs text-slate-400">87%</span>
                        </div>
                        <div className="flex items-center gap-2 ml-8">
                          <div className="px-3 py-1 bg-pink-600 rounded text-sm font-semibold">
                            Prediction
                          </div>
                          <div className="flex-1 h-0.5 bg-pink-500/50"></div>
                          <span className="text-xs text-slate-400">94%</span>
                        </div>

                        {/* Consensus */}
                        <div className="flex items-center justify-center gap-3 my-4">
                          <div className="flex-1 h-0.5 bg-gradient-to-r from-transparent to-green-500"></div>
                          <div className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg">
                            <p className="text-xs font-semibold">⚖️ Consensus Engine</p>
                            <p className="text-lg font-semibold text-center">{(consensusScore * 100).toFixed(0)}%</p>
                          </div>
                          <div className="flex-1 h-0.5 bg-gradient-to-l from-transparent to-green-500"></div>
                        </div>

                        {/* Resolution */}
                        <div className="flex items-center gap-2">
                          <div className="px-3 py-1 bg-green-600 rounded text-sm font-semibold">
                            Resolution
                          </div>
                          <div className="flex-1 h-0.5 bg-green-500/50"></div>
                          <span className="text-xs text-green-400">2.8s</span>
                        </div>
                      </div>
                    </div>

                    {/* Consensus Details */}
                    <div className="space-y-2">
                      <p className="text-sm font-semibold text-slate-300">Why so confident?</p>
                      <div className="space-y-1 text-xs text-slate-400">
                        <div className="flex items-start gap-2">
                          <span className="text-green-400">•</span>
                          <span>5/5 agents agree on root cause</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-green-400">•</span>
                          <span>Similar pattern resolved 127x before</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-green-400">•</span>
                          <span>Root cause identified with 92% certainty</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-green-400">•</span>
                          <span>Byzantine consensus validated</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Enhanced Transparency - Side by Side */}
              <Card className="card-glass">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">🧠 AI TRANSPARENCY</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {/* Agent Reasoning Column */}
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-slate-400 uppercase">Agent Reasoning</p>
                      <div className="space-y-2 text-xs">
                        <div className="p-2 bg-slate-800/50 rounded">
                          <p className="font-semibold text-status-info mb-1">Detection:</p>
                          <p className="text-slate-300">"CPU spike at 14:23, correlating with database queries"</p>
                        </div>
                        <div className="p-2 bg-slate-800/50 rounded">
                          <p className="font-semibold text-purple-400 mb-1">Diagnosis:</p>
                          <p className="text-slate-300">"Connection pool exhaustion due to slow query at line 247"</p>
                        </div>
                        <div className="p-2 bg-slate-800/50 rounded">
                          <p className="font-semibold text-pink-400 mb-1">Prediction:</p>
                          <p className="text-slate-300">"96% probability of cascade within 3 min"</p>
                        </div>
                      </div>
                    </div>

                    {/* Confidence Scores Column */}
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-slate-400 uppercase">Confidence Scores</p>
                      <div className="space-y-3">
                        {agents.slice(0, 3).map((agent) => (
                          <div key={agent.id} className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-slate-400">{agent.name.split(" ")[0]}:</span>
                              <span className="font-semibold text-green-400">
                                {(agent.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                            <Progress value={agent.confidence * 100} className="h-1.5" />
                          </div>
                        ))}
                        <div className="border-t border-gray-700 pt-2 mt-3">
                          <div className="flex justify-between text-xs font-bold">
                            <span className="text-slate-300">CONSENSUS:</span>
                            <span className="text-green-400">{(consensusScore * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-xs text-green-400 mt-1">✓ Auto-approved</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* COLUMN 4: Business Impact & Predictions */}
            <div className="space-y-6">
              {/* Business Impact Calculator */}
              <Card className="bg-gradient-to-br from-emerald-900/30 to-green-900/30 border-emerald-500/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">💰 BUSINESS IMPACT</CardTitle>
                  <p className="text-xs text-slate-400">This Incident</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Severity:</span>
                      <Badge variant="destructive" className="bg-red-600">CRITICAL</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Service:</span>
                      <span className="font-semibold">Payment API</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Cost per minute:</span>
                      <span className="font-semibold text-red-400">{formatCurrency(10000)}</span>
                    </div>
                  </div>

                  <div className="border-t border-gray-700 pt-3 space-y-2">
                    <div className="flex justify-between items-center p-2 bg-red-900/20 rounded">
                      <span className="text-slate-400 text-sm">If Manual ({mttrManual}m):</span>
                      <span className="font-semibold text-red-400">{formatCurrency(impact.manualCost)} loss</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-blue-900/20 rounded">
                      <span className="text-slate-400 text-sm">AI Response ({mttrCurrent}m):</span>
                      <span className="font-semibold text-blue-400">{formatCurrency(impact.aiCost)} loss</span>
                    </div>
                  </div>

                  <div className="border-t-2 border-green-500/50 pt-3">
                    <div className="text-center">
                      <p className="text-sm text-slate-400 mb-1">SAVED</p>
                      <p className="text-3xl font-semibold text-green-400">{formatCurrency(impact.saved)}</p>
                      <p className="text-xs text-green-300 mt-1">{impact.improvement}% cost reduction</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Predicted Incidents */}
              <Card className="card-glass">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">🔮 PREDICTED INCIDENTS</CardTitle>
                  <p className="text-xs text-slate-400">Next 30 minutes</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  {predictedIncidents.map((incident) => (
                    <div
                      key={incident.id}
                      className={`p-3 rounded-lg border ${
                        incident.status === "preventive_action"
                          ? "bg-orange-900/20 border-orange-500/30"
                          : "bg-blue-900/20 border-blue-500/30"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-semibold text-sm">{incident.title}</p>
                        <Badge
                          variant={incident.status === "preventive_action" ? "default" : "secondary"}
                          className="text-xs"
                        >
                          {(incident.confidence * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <div className="space-y-1 text-xs">
                        <div className="flex items-start gap-2">
                          <span className="text-yellow-400 mt-0.5">⚡</span>
                          <span className="text-slate-300">Action: {incident.action}</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-green-400 mt-0.5">💰</span>
                          <span className="text-slate-300">Impact: {incident.impact}</span>
                        </div>
                        <div className="flex items-start gap-2 mt-2">
                          <Badge
                            variant={incident.status === "preventive_action" ? "default" : "outline"}
                            className="text-xs"
                          >
                            {incident.status === "preventive_action" ? "Action Scheduled" : "Monitoring"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Competitor Comparison */}
              <Card className="bg-gradient-to-br from-violet-900/30 to-purple-900/30 border-violet-500/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">⚔️ VS. COMPETITORS</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-xs">
                  <div className="p-2 bg-slate-800/50 rounded">
                    <p className="font-semibold text-slate-300 mb-1">PagerDuty Advance:</p>
                    <p className="text-slate-400">Still requires human approval</p>
                  </div>
                  <div className="p-2 bg-slate-800/50 rounded">
                    <p className="font-semibold text-slate-300 mb-1">ServiceNow:</p>
                    <p className="text-slate-400">Rule-based only, no AI</p>
                  </div>
                  <div className="p-2 bg-slate-800/50 rounded">
                    <p className="font-semibold text-slate-300 mb-1">Splunk SOAR:</p>
                    <p className="text-slate-400">No prediction capability</p>
                  </div>
                  <div className="p-2 bg-green-900/30 border border-green-500/30 rounded mt-3">
                    <p className="font-semibold text-green-400 mb-1">✓ Incident Commander:</p>
                    <p className="text-green-300 text-xs">Fully autonomous + predictive + transparent</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Demo Controls */}
          <Card className="card-glass">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold mb-1">🎬 Live Incident Demo</h3>
                  <p className="text-sm text-slate-400">
                    {currentStep === 0 && !isPlaying && "Ready to demonstrate incident resolution"}
                    {currentStep > 0 && currentStep < 6 && !isPlaying && `Paused at step ${currentStep} of 6`}
                    {isPlaying && `Step ${currentStep} of 6 - ${["Starting...", "Detection", "Diagnosis", "Prediction", "Consensus", "Resolution", "Validation"][currentStep]}`}
                    {currentStep === 6 && !isPlaying && "Incident resolved - Database Cascade Failure (completed in 32s)"}
                  </p>
                </div>
                <div>
                  <Badge variant={isPlaying ? "default" : "outline"} className="text-sm">
                    {isPlaying ? "🔴 LIVE" : currentStep === 6 ? "✅ Complete" : "⏸️ Ready"}
                  </Badge>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-4">
                <Progress value={(currentStep / 6) * 100} className="h-3" />
                <div className="flex justify-between mt-2 text-xs text-slate-500">
                  <span>Start</span>
                  <span className="text-blue-400 font-semibold">{currentStep === 6 ? "Complete" : `${currentStep}/6 Steps`}</span>
                  <span>Resolved</span>
                </div>
              </div>

              {/* Playback Controls */}
              <div className="flex gap-3">
                <Button
                  onClick={startIncidentDemo}
                  disabled={isPlaying || currentStep === 0}
                  variant="default"
                  className="flex-1 focus-ring-primary"
                >
                  ⏮️ Restart Demo
                </Button>
                
                {!isPlaying && currentStep < 6 && currentStep > 0 && (
                  <Button
                    onClick={resumeIncidentDemo}
                    variant="default"
                    className="flex-1 bg-green-600 hover:bg-green-700 focus-ring-primary"
                  >
                    ▶️ Resume
                  </Button>
                )}

                {!isPlaying && currentStep === 0 && (
                  <Button
                    onClick={startIncidentDemo}
                    variant="default"
                    className="flex-1 bg-green-600 hover:bg-green-700 focus-ring-primary"
                  >
                    ▶️ Start Incident Demo
                  </Button>
                )}

                {isPlaying && (
                  <Button
                    onClick={pauseIncidentDemo}
                    variant="default"
                    className="flex-1 bg-yellow-600 hover:bg-yellow-700 focus-ring-primary"
                  >
                    ⏸️ Pause
                  </Button>
                )}

                <Button
                  onClick={skipToEnd}
                  disabled={currentStep === 6}
                  variant="outline"
                  className="flex-1 focus-ring-primary"
                >
                  ⏭️ Skip to End
                </Button>

                <Button
                  onClick={() => setAnimationSpeed(animationSpeed === 2000 ? 1000 : animationSpeed === 1000 ? 500 : 2000)}
                  variant="outline"
                  className="px-4"
                  title="Toggle speed"
                >
                  {animationSpeed === 2000 ? "1x" : animationSpeed === 1000 ? "2x" : "4x"} ⚡
                </Button>
              </div>

              {/* Step Description */}
              <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
                <p className="text-sm text-slate-300">
                  {currentStep === 0 && "🎬 Ready to demonstrate live incident resolution from detection to validation"}
                  {currentStep === 1 && "🔍 Detection Agent analyzing CPU spike and database query patterns"}
                  {currentStep === 2 && "🧠 Diagnosis Agent identifying root cause: connection pool exhaustion"}
                  {currentStep === 3 && "🔮 Prediction Agent forecasting 96% probability of cascade failure"}
                  {currentStep === 4 && "⚖️ Consensus Engine achieving 94% confidence across all agents"}
                  {currentStep === 5 && "✅ Resolution Agent deploying dual strategy: scale + optimize"}
                  {currentStep === 6 && "✓ Validation Agent confirming resolution: CPU normalized, no cascade detected"}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center text-slate-500 text-sm py-4">
            <p className="mb-1">
              🏆 AWS Hackathon 2024 - World's First Transparent Autonomous Incident Commander
            </p>
            <p className="text-xs">
              Built with AWS Bedrock • Claude 3.5 Sonnet • Byzantine Consensus • RAG Memory • 8/8 AWS AI Services
            </p>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default PowerDashboard;