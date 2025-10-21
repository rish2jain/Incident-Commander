"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../src/components/ui/card";
import { Button } from "../../src/components/ui/button";
import { Badge } from "../../src/components/ui/badge";

// Simple demo component without complex dependencies
export default function SimpleDemoPage() {
  const [incidentActive, setIncidentActive] = useState(false);
  const [mttrSeconds, setMttrSeconds] = useState(0);
  const [events, setEvents] = useState<
    Array<{
      id: string;
      agent: string;
      message: string;
      timestamp: string;
      type: string;
    }>
  >([]);

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
    if (window.location.search.includes("auto-demo=true")) {
      const timer = setTimeout(() => {
        const button = document.querySelector("button");
        if (button && !button.disabled) {
          button.click();
        }
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, []);

  const addEvent = (agent: string, message: string, type: string = "info") => {
    const newEvent = {
      id: crypto.randomUUID(),
      agent,
      message,
      timestamp: new Date().toLocaleTimeString(),
      type,
    };
    setEvents((prev) => [newEvent, ...prev]);
  };

  const triggerIncident = async () => {
    if (incidentActive) return;

    setIncidentActive(true);
    setMttrSeconds(0);
    setEvents([]);

    // Simulate incident flow
    addEvent(
      "Detection",
      "🚨 Database connection pool exhausted detected",
      "critical"
    );

    await new Promise((resolve) => setTimeout(resolve, 2000));
    addEvent(
      "Detection",
      "✅ Incident confirmed - escalating to diagnosis",
      "success"
    );

    await new Promise((resolve) => setTimeout(resolve, 1500));
    addEvent(
      "Diagnosis",
      "🔬 Analyzing root cause - checking query performance",
      "analysis"
    );

    await new Promise((resolve) => setTimeout(resolve, 3000));
    addEvent(
      "Diagnosis",
      "💡 Root cause identified: Slow query cascade",
      "analysis"
    );

    await new Promise((resolve) => setTimeout(resolve, 1000));
    addEvent(
      "Prediction",
      "🔮 Forecasting remediation impact - 96% success rate",
      "analysis"
    );

    await new Promise((resolve) => setTimeout(resolve, 1500));
    addEvent(
      "Resolution",
      "⚡ Executing remediation: Kill slow query + Scale pool",
      "action"
    );

    await new Promise((resolve) => setTimeout(resolve, 4000));
    addEvent(
      "Resolution",
      "✅ Remediation complete - system restored",
      "success"
    );

    await new Promise((resolve) => setTimeout(resolve, 1000));
    addEvent(
      "Communication",
      "📢 Incident resolved - notifications sent",
      "success"
    );

    setTimeout(() => {
      setIncidentActive(false);
    }, 2000);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          🛡️ Autonomous Incident Commander
        </h1>
        <p className="text-slate-400">
          Enhanced React Dashboard with Auto-scroll
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">MTTR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">
              {formatTime(mttrSeconds)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={incidentActive ? "destructive" : "default"}>
              {incidentActive ? "Active Incident" : "All Clear"}
            </Badge>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-400">
              {events.length}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">Cost Saved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">
              ${incidentActive ? (mttrSeconds * 93).toLocaleString() : "0"}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Control Panel */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              🎮 Demo Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={triggerIncident}
              disabled={incidentActive}
              className="w-full bg-red-600 hover:bg-red-700"
            >
              {incidentActive
                ? "Incident In Progress..."
                : "🚨 Trigger Database Cascade"}
            </Button>

            <div className="text-sm text-slate-400">
              This demo showcases the enhanced React dashboard with:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Auto-scrolling timeline</li>
                <li>Real-time metrics updates</li>
                <li>Multi-agent coordination</li>
                <li>Professional UX components</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 Live Event Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-96 overflow-y-auto space-y-3 pr-2">
              {events.length === 0 ? (
                <div className="text-center text-slate-400 py-8">
                  <div className="text-4xl mb-2">⏳</div>
                  <p>Waiting for incident...</p>
                </div>
              ) : (
                events.map((event) => (
                  <div
                    key={event.id}
                    className={`p-3 rounded-lg border-l-4 ${
                      event.type === "critical"
                        ? "border-red-500 bg-red-500/10"
                        : event.type === "success"
                        ? "border-green-500 bg-green-500/10"
                        : event.type === "analysis"
                        ? "border-blue-500 bg-blue-500/10"
                        : event.type === "action"
                        ? "border-orange-500 bg-orange-500/10"
                        : "border-slate-500 bg-slate-500/10"
                    }`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-semibold text-sm">
                        {event.agent}
                      </span>
                      <span className="text-xs text-slate-400">
                        {event.timestamp}
                      </span>
                    </div>
                    <p className="text-sm">{event.message}</p>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
