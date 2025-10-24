"use client";

import React, { useState, useEffect } from "react";

/**
 * PowerDashboard Component - Interactive Version
 *
 * Interactive demo dashboard with all the power features and working controls
 */
export function PowerDashboard() {
  // Demo state management
  const [demoStep, setDemoStep] = useState(6); // Start completed
  const [isPlaying, setIsPlaying] = useState(false);
  const [animationSpeed, setAnimationSpeed] = useState(2000); // 1x speed
  const [liveMetrics, setLiveMetrics] = useState({
    incidentsResolved: 47,
    timeSaved: "18h 23m",
    costAvoided: 156000,
    zeroTouchStreak: 47,
  });

  // Auto-increment metrics for live feel
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveMetrics((prev) => ({
        ...prev,
        incidentsResolved:
          prev.incidentsResolved + (Math.random() > 0.8 ? 1 : 0),
        costAvoided:
          prev.costAvoided +
          (Math.random() > 0.7 ? Math.floor(Math.random() * 5000) : 0),
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Demo animation logic
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setDemoStep((prev) => {
        if (prev >= 6) {
          setIsPlaying(false);
          return 6;
        }
        return prev + 1;
      });
    }, animationSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, animationSpeed]);

  // Demo control functions
  const startDemo = () => {
    setDemoStep(0);
    setIsPlaying(true);
  };

  const restartDemo = () => {
    setDemoStep(0);
    setIsPlaying(false);
  };

  const replayAnimation = () => {
    if (demoStep === 6) {
      setDemoStep(0);
      setIsPlaying(true);
    } else {
      setIsPlaying(!isPlaying);
    }
  };

  const toggleSpeed = () => {
    setAnimationSpeed((prev) => {
      if (prev === 2000) return 1000; // 2x
      if (prev === 1000) return 500; // 4x
      return 2000; // 1x
    });
  };

  const getSpeedLabel = () => {
    if (animationSpeed === 2000) return "1x";
    if (animationSpeed === 1000) return "2x";
    return "4x";
  };

  const getDemoStatus = () => {
    if (demoStep === 0 && !isPlaying)
      return "Ready to demonstrate incident resolution";
    if (isPlaying) {
      const steps = [
        "Starting...",
        "Detection",
        "Diagnosis",
        "Prediction",
        "Consensus",
        "Resolution",
        "Validation",
      ];
      return `Step ${demoStep} of 6 - ${steps[demoStep]}`;
    }
    if (demoStep === 6)
      return "Incident resolved - Database Cascade Failure (completed in 32s)";
    return `Paused at step ${demoStep} of 6`;
  };

  const getProgressPercentage = () => {
    return (demoStep / 6) * 100;
  };

  // Get dynamic agent status based on demo step
  const getAgentStatus = (agentIndex: number) => {
    const agents = [
      { name: "Detection Agent", confidence: 92, baseStep: 1 },
      { name: "Diagnosis Agent", confidence: 87, baseStep: 2 },
      { name: "Prediction Agent", confidence: 94, baseStep: 3 },
      { name: "Resolution Agent", confidence: 91, baseStep: 5 },
      { name: "Validation Agent", confidence: 98, baseStep: 6 },
    ];

    const agent = agents[agentIndex];
    if (demoStep >= agent.baseStep) {
      return { ...agent, status: "complete" };
    } else if (demoStep === agent.baseStep - 1 && isPlaying) {
      return {
        ...agent,
        status: "active",
        confidence: Math.floor(agent.confidence * 0.6),
      };
    } else {
      return { ...agent, status: "idle", confidence: 0 };
    }
  };
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 text-white p-6">
      <div className="max-w-[1800px] mx-auto space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex justify-start mb-4">
          <a
            href="/transparency"
            className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
          >
            &lt;&lt; View Technical Deep-Dive
          </a>
        </div>

        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-3">
            PowerDashboard - Interactive Demo
          </h1>
          <p className="text-xl text-slate-400">
            Complete Multi-Agent Incident Response System
          </p>
          <div className="flex items-center justify-center gap-3 mt-4">
            <span className="px-3 py-1 bg-green-600 rounded text-sm">
              ✅ {liveMetrics.incidentsResolved} Incidents Resolved Today
            </span>
            <span className="px-3 py-1 bg-blue-600 rounded text-sm">
              ⚡ 2.5min Average Resolution
            </span>
            <span className="px-3 py-1 bg-purple-600 rounded text-sm">
              🔥 Zero-Touch Streak: 47
            </span>
          </div>
        </div>

        {/* 4-Column Layout */}
        <div className="grid grid-cols-4 gap-6">
          {/* Column 1: Live Savings */}
          <div className="space-y-6">
            <div className="bg-slate-800/50 border border-blue-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                ⏱️ LIVE SAVINGS TODAY (MOCK)
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">
                    Incidents Resolved:
                  </span>
                  <span className="text-2xl font-bold text-green-400">
                    {liveMetrics.incidentsResolved}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Time Saved:</span>
                  <span className="text-2xl font-bold text-blue-400">
                    {liveMetrics.timeSaved}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Cost Avoided (Projected):</span>
                  <span className="text-2xl font-bold text-purple-400">
                    ${Math.floor(liveMetrics.costAvoided / 1000)}K
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">
                    Human Interventions:
                  </span>
                  <span className="text-2xl font-bold text-green-400">0</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-green-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                🤖 Multi-Agent Status (Mock)
              </h3>
              <div className="space-y-2">
                {Array.from({ length: 5 }, (_, i) => getAgentStatus(i)).map(
                  (agent, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-lg transition-all duration-500 ${
                        agent.status === "active"
                          ? "bg-blue-600/30 ring-2 ring-blue-400 animate-pulse"
                          : agent.status === "complete"
                          ? "bg-slate-700/50 hover:bg-slate-700"
                          : "bg-slate-800/30 opacity-50"
                      }`}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-semibold text-sm">
                          {agent.name}
                        </span>
                        <span
                          className={`px-2 py-1 rounded text-xs transition-all duration-300 ${
                            agent.status === "complete"
                              ? "bg-green-600"
                              : agent.status === "active"
                              ? "bg-blue-600 animate-pulse"
                              : "bg-slate-600 opacity-30"
                          }`}
                        >
                          {agent.status === "complete"
                            ? "✓"
                            : agent.status === "active"
                            ? "⚡"
                            : "○"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-600 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${
                              agent.status === "active"
                                ? "bg-blue-400"
                                : "bg-green-400"
                            }`}
                            style={{ width: `${agent.confidence}%` }}
                          ></div>
                        </div>
                        <span
                          className={`text-xs transition-all duration-300 ${
                            agent.confidence > 0
                              ? "text-green-400"
                              : "text-slate-600"
                          }`}
                        >
                          {agent.confidence}%
                        </span>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>

            <div className="bg-gradient-to-br from-amber-900/30 to-orange-900/30 border border-amber-500/50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                🏆 INDUSTRY FIRSTS (Mock)
              </h3>
              <div className="space-y-2 text-sm">
                {[
                  "Byzantine fault-tolerant consensus",
                  "Predictive incident prevention",
                  "Zero-touch resolution",
                  "Self-improving via RAG memory",
                  "8/8 AWS AI services integrated",
                  "Complete decision transparency",
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Column 2: Before/After & Timeline */}
          <div className="space-y-6">
            <div className="bg-slate-800/50 border border-purple-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                📊 IMPACT COMPARISON (Mock)
              </h3>
              <div className="space-y-4">
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-slate-400">
                        Manual Response
                      </p>
                      <p className="text-2xl font-bold text-red-400">30.2m</p>
                    </div>
                    <span className="text-4xl">😰</span>
                  </div>
                </div>
                <div className="p-3 bg-green-900/20 border border-green-500/30 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-slate-400">
                        AI Response
                      </p>
                      <p className="text-2xl font-bold text-green-400">2.5m</p>
                    </div>
                    <span className="text-4xl">✓</span>
                  </div>
                </div>
                <div className="border-t border-gray-700 pt-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Improvement:</span>
                    <span className="text-xl font-bold text-green-400">
                      91.8% faster
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-blue-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                ⏰ INCIDENT TIMELINE (Mock)
              </h3>
              <div className="space-y-3">
                {[
                  {
                    time: "14:23:15",
                    agent: "Detection Agent",
                    action: "Anomaly detected",
                    duration: "3s",
                    icon: "🔍",
                  },
                  {
                    time: "14:23:18",
                    agent: "Diagnosis Agent",
                    action: "Root cause identified",
                    duration: "7s",
                    icon: "🧠",
                  },
                  {
                    time: "14:23:25",
                    agent: "Prediction Agent",
                    action: "Impact forecast complete",
                    duration: "5s",
                    icon: "🔮",
                  },
                  {
                    time: "14:23:30",
                    agent: "Consensus Engine",
                    action: "3/3 agents agree (94% confidence)",
                    duration: "2s",
                    icon: "⚖️",
                  },
                  {
                    time: "14:23:32",
                    agent: "Resolution Agent",
                    action: "Fix applied",
                    duration: "8s",
                    icon: "✅",
                  },
                  {
                    time: "14:23:40",
                    agent: "Validation Agent",
                    action: "Issue resolved",
                    duration: "7s",
                    icon: "✓",
                  },
                ].map((event, i) => (
                  <div key={i} className="flex items-start gap-3 relative">
                    {i < 5 && (
                      <div className="absolute left-[15px] top-8 bottom-[-12px] w-0.5 bg-blue-500/30"></div>
                    )}
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center z-10 flex-shrink-0">
                      <span className="text-sm">{event.icon}</span>
                    </div>
                    <div className="flex-1 pt-1">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-sm">
                          {event.agent}
                        </span>
                        <span className="text-xs text-slate-500">
                          {event.time}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400">{event.action}</p>
                      <p className="text-xs text-green-400 mt-1">
                        {event.duration}
                      </p>
                    </div>
                  </div>
                ))}
                <div className="border-t border-green-500/50 pt-3 mt-4 text-center">
                  <p className="text-sm text-slate-400">
                    Total Resolution Time (Mock)
                  </p>
                  <p className="text-3xl font-bold text-green-400">
                    32s
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    vs 30+ minutes manual (98.2% faster)
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Column 3: Agent Coordination & AI Transparency */}
          <div className="space-y-6">
            <div className="bg-slate-800/50 border border-green-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                🔄 AGENT COORDINATION (Mock)
              </h3>
              <div className="space-y-4">
                <div className="p-4 bg-slate-700/50 rounded-lg">
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
                    <div className="flex items-center justify-center gap-3 my-4">
                      <div className="flex-1 h-0.5 bg-gradient-to-r from-transparent to-green-500"></div>
                      <div className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg">
                        <p className="text-xs font-semibold">
                          ⚖️ Consensus Engine
                        </p>
                        <p className="text-lg font-bold text-center">94%</p>
                      </div>
                      <div className="flex-1 h-0.5 bg-gradient-to-l from-transparent to-green-500"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="px-3 py-1 bg-green-600 rounded text-sm font-semibold">
                        Resolution
                      </div>
                      <div className="flex-1 h-0.5 bg-green-500/50"></div>
                      <span className="text-xs text-green-400">2.8s</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-purple-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                🧠 AI TRANSPARENCY (Mock)
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-slate-400 uppercase">
                    Agent Reasoning
                  </p>
                  <div className="space-y-2 text-xs">
                    <div className="p-2 bg-slate-700/50 rounded">
                      <p className="font-semibold text-blue-400 mb-1">
                        Detection:
                      </p>
                      <p className="text-slate-300">
                        "CPU spike at 14:23, correlating with database queries"
                      </p>
                    </div>
                    <div className="p-2 bg-slate-700/50 rounded">
                      <p className="font-semibold text-purple-400 mb-1">
                        Diagnosis:
                      </p>
                      <p className="text-slate-300">
                        "Connection pool exhaustion due to slow query at line
                        247"
                      </p>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-slate-400 uppercase">
                    Confidence Scores
                  </p>
                  <div className="space-y-3">
                    {[
                      { name: "Detection", confidence: 92 },
                      { name: "Diagnosis", confidence: 87 },
                      { name: "Prediction", confidence: 94 },
                    ].map((agent, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">{agent.name}:</span>
                          <span className="font-semibold text-green-400">
                            {agent.confidence}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-600 rounded-full h-1.5">
                          <div
                            className="bg-green-400 h-1.5 rounded-full"
                            style={{ width: `${agent.confidence}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                    <div className="border-t border-gray-700 pt-2 mt-3">
                      <div className="flex justify-between text-xs font-bold">
                        <span className="text-slate-300">CONSENSUS:</span>
                        <span className="text-green-400">94%</span>
                      </div>
                      <p className="text-xs text-green-400 mt-1">
                        ✓ Auto-approved
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Column 4: Business Impact & Predictions */}
          <div className="space-y-6">
            <div className="bg-gradient-to-br from-emerald-900/30 to-green-900/30 border border-emerald-500/50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                💰 BUSINESS IMPACT (MOCK)
              </h3>
              <p className="text-xs text-slate-400 mb-4">This Incident</p>
              <div className="space-y-3">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Severity:</span>
                    <span className="px-2 py-1 bg-red-600 rounded text-xs">
                      CRITICAL
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Service:</span>
                    <span className="font-semibold">Payment API</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Cost per minute:</span>
                    <span className="font-semibold text-red-400">$10,000</span>
                  </div>
                </div>
                <div className="border-t border-gray-700 pt-3 space-y-2">
                  <div className="flex justify-between items-center p-2 bg-red-900/20 rounded">
                    <span className="text-slate-400 text-sm">
                      If Manual (30.2m):
                    </span>
                    <span className="font-semibold text-red-400">
                      $302K loss
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-blue-900/20 rounded">
                    <span className="text-slate-400 text-sm">
                      AI Response (2.5m):
                    </span>
                    <span className="font-semibold text-blue-400">
                      $25K loss
                    </span>
                  </div>
                </div>
                <div className="border-t-2 border-green-500/50 pt-3 text-center">
                  <p className="text-sm text-slate-400 mb-1">SAVED</p>
                  <p className="text-3xl font-bold text-green-400">
                    $277K (Projected)
                  </p>
                  <p className="text-xs text-green-300 mt-1">
                    91.8% cost reduction (Projected)
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-orange-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                🔮 PREDICTED INCIDENTS (MOCK)
              </h3>
              <p className="text-xs text-slate-400 mb-4">Next 30 minutes</p>
              <div className="space-y-3">
                {[
                  {
                    title: "Memory leak in User Service",
                    confidence: 87,
                    action: "Preemptive restart at 15:00",
                    impact: "Prevented $45K downtime (Projected)",
                    status: "preventive_action",
                  },
                  {
                    title: "Database connection spike",
                    confidence: 72,
                    action: "Scale connection pool",
                    impact: "Monitoring - 30 min window",
                    status: "monitoring",
                  },
                ].map((incident, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border ${
                      incident.status === "preventive_action"
                        ? "bg-orange-900/20 border-orange-500/30"
                        : "bg-blue-900/20 border-blue-500/30"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <p className="font-semibold text-sm">{incident.title}</p>
                      <span className="px-2 py-1 bg-slate-600 rounded text-xs">
                        {incident.confidence}%
                      </span>
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-start gap-2">
                        <span className="text-yellow-400 mt-0.5">⚡</span>
                        <span className="text-slate-300">
                          Action: {incident.action}
                        </span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="text-green-400 mt-0.5">💰</span>
                        <span className="text-slate-300">
                          Impact: {incident.impact}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-violet-900/30 to-purple-900/30 border border-violet-500/50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                ⚔️ VS. COMPETITORS (Mock)
              </h3>
              <div className="space-y-2 text-xs">
                <div className="p-2 bg-slate-800/50 rounded">
                  <p className="font-semibold text-slate-300 mb-1">
                    PagerDuty Advance:
                  </p>
                  <p className="text-slate-400">
                    Still requires human approval
                  </p>
                </div>
                <div className="p-2 bg-slate-800/50 rounded">
                  <p className="font-semibold text-slate-300 mb-1">
                    ServiceNow:
                  </p>
                  <p className="text-slate-400">Rule-based only, no AI</p>
                </div>
                <div className="p-2 bg-green-900/30 border border-green-500/30 rounded mt-3">
                  <p className="font-semibold text-green-400 mb-1">
                    ✓ Incident Commander:
                  </p>
                  <p className="text-green-300 text-xs">
                    Fully autonomous + predictive + transparent
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Demo Controls */}
        <div className="bg-slate-800/50 border border-blue-500/30 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold mb-1">
                🎬 Live Incident Demo
              </h3>
              <p className="text-sm text-slate-400">{getDemoStatus()}</p>
            </div>
            <span
              className={`px-3 py-1 rounded text-sm ${
                isPlaying
                  ? "bg-blue-600 animate-pulse"
                  : demoStep === 6
                  ? "bg-green-600"
                  : "bg-slate-600"
              }`}
            >
              {isPlaying
                ? "🔴 LIVE"
                : demoStep === 6
                ? "✅ Complete"
                : "⏸️ Ready"}
            </span>
          </div>

          <div className="mb-4">
            <div className="w-full bg-slate-600 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  isPlaying ? "bg-blue-400" : "bg-green-400"
                }`}
                style={{ width: `${getProgressPercentage()}%` }}
              ></div>
            </div>
            <div className="flex justify-between mt-2 text-xs text-slate-500">
              <span>Start</span>
              <span className="text-blue-400 font-semibold">
                {demoStep === 6 ? "Complete" : `${demoStep}/6 Steps`}
              </span>
              <span>Resolved</span>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={restartDemo}
              disabled={isPlaying}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold transition-colors"
            >
              ⏮️ Restart Demo
            </button>
            <button
              onClick={replayAnimation}
              className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-semibold transition-colors"
            >
              {isPlaying
                ? "⏸️ Pause"
                : demoStep === 6
                ? "▶️ Replay"
                : "▶️ Resume"}
            </button>
            <button
              onClick={toggleSpeed}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-700 rounded text-sm transition-colors"
            >
              {getSpeedLabel()} ⚡
            </button>
          </div>

          <div className="mt-4 p-3 bg-slate-700/50 rounded-lg">
            <p className="text-sm text-slate-300">
              {demoStep === 0 &&
                "🎬 Ready to demonstrate live incident resolution from detection to validation"}
              {demoStep === 1 &&
                "🔍 Detection Agent analyzing CPU spike and database query patterns"}
              {demoStep === 2 &&
                "🧠 Diagnosis Agent identifying root cause: connection pool exhaustion"}
              {demoStep === 3 &&
                "🔮 Prediction Agent forecasting 96% probability of cascade failure"}
              {demoStep === 4 &&
                "⚖️ Consensus Engine achieving 94% confidence across all agents"}
              {demoStep === 5 &&
                "✅ Resolution Agent deploying dual strategy: scale + optimize"}
              {demoStep === 6 &&
                "✓ Validation Agent confirming resolution: CPU normalized, query time reduced 94%, no cascade detected"}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-slate-500 text-sm py-4">
          <p className="mb-1">
            🏆 AWS Hackathon 2025 - World's First Transparent Autonomous
            Incident Commander
          </p>
          <p className="text-xs">
            Built with AWS Bedrock • Claude 3.5 Sonnet • Byzantine Consensus •
            RAG Memory • 8/8 AWS AI Services
          </p>
        </div>
      </div>
    </div>
  );
}

export default PowerDashboard;
