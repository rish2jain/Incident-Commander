"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import IncidentStatusPanel from "./IncidentStatusPanel";
import { globalIncidentTracker } from "../lib/incident-status-tracker";

/**
 * Enhanced Incident Status Panel Example
 *
 * Demonstrates all the new features implemented in task 4:
 * - 4.1: Prominent resolution status display with green coloring and resolution time
 * - 4.2: Progress indicators for active incidents showing each resolution phase
 * - 4.3: Incident overview panel with resolved vs active counts and 30-second visibility
 */
const EnhancedIncidentStatusExample: React.FC = () => {
  const [demoMode, setDemoMode] = useState<"static" | "active" | "resolved">(
    "static"
  );
  const [showOverview, setShowOverview] = useState(true);

  // Mock data for overview panel
  const overviewData = {
    activeIncidents: demoMode === "active" ? 1 : 0,
    resolvedIncidents: demoMode === "resolved" ? 6 : 5,
    totalIncidents: 6,
    recentResolution:
      demoMode === "resolved"
        ? {
            id: "INC-2024-001",
            title: "Database Performance Degradation",
            resolutionTime: 142, // 2 minutes 22 seconds
            timestamp: new Date(),
          }
        : null,
  };

  const timeoutIdsRef = React.useRef<number[]>([]);

  const clearAllTimeouts = () => {
    timeoutIdsRef.current.forEach((id) => clearTimeout(id));
    timeoutIdsRef.current = [];
  };

  const startActiveIncident = () => {
    // Clear any existing timeouts first
    clearAllTimeouts();

    setDemoMode("active");

    // Start a mock incident with the tracker
    globalIncidentTracker.startIncident({
      id: "INC-2024-001",
      title: "Database Performance Degradation",
      severity: "critical",
      description: "Performance issues detected in primary database cluster",
      phase: "detection",
    });

    // Simulate phase progression with stored timeout IDs
    timeoutIdsRef.current.push(
      window.setTimeout(() => {
        globalIncidentTracker.updateIncidentStatus({ phase: "diagnosis" });
      }, 2000)
    );

    timeoutIdsRef.current.push(
      window.setTimeout(() => {
        globalIncidentTracker.updateIncidentStatus({ phase: "prediction" });
      }, 4000)
    );

    timeoutIdsRef.current.push(
      window.setTimeout(() => {
        globalIncidentTracker.updateIncidentStatus({ phase: "resolution" });
      }, 6000)
    );

    timeoutIdsRef.current.push(
      window.setTimeout(() => {
        globalIncidentTracker.updateIncidentStatus({ phase: "communication" });
      }, 8000)
    );

    timeoutIdsRef.current.push(
      window.setTimeout(() => {
        globalIncidentTracker.markIncidentResolved(142); // 2 minutes 22 seconds
        setDemoMode("resolved");
        clearAllTimeouts(); // Clear timeouts after completion
      }, 10000)
    );
  };

  const resetDemo = () => {
    clearAllTimeouts(); // Cancel any pending timeouts
    setDemoMode("static");
    globalIncidentTracker.clearIncident();
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      clearAllTimeouts();
    };
  }, []);

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Enhanced Incident Status Panel Demo
            <div className="flex gap-2">
              <Button
                onClick={startActiveIncident}
                disabled={demoMode === "active"}
              >
                {demoMode === "active"
                  ? "Incident In Progress..."
                  : "Start Demo Incident"}
              </Button>
              <Button onClick={resetDemo}>Reset</Button>
              <Button onClick={() => setShowOverview(!showOverview)}>
                {showOverview ? "Hide" : "Show"} Overview
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div
                className={`p-3 rounded-lg border ${
                  demoMode === "static"
                    ? "bg-blue-50 border-blue-200"
                    : "bg-muted"
                }`}
              >
                <div className="font-medium">Static Mode</div>
                <div className="text-muted-foreground">
                  Shows traditional incident panel without real-time features
                </div>
              </div>
              <div
                className={`p-3 rounded-lg border ${
                  demoMode === "active"
                    ? "bg-orange-50 border-orange-200"
                    : "bg-muted"
                }`}
              >
                <div className="font-medium">Active Incident</div>
                <div className="text-muted-foreground">
                  Shows progress indicators and real-time phase updates
                </div>
              </div>
              <div
                className={`p-3 rounded-lg border ${
                  demoMode === "resolved"
                    ? "bg-green-50 border-green-200"
                    : "bg-muted"
                }`}
              >
                <div className="font-medium">Resolved</div>
                <div className="text-muted-foreground">
                  Shows resolution banner with celebration and metrics
                </div>
              </div>
            </div>

            <div className="text-sm text-muted-foreground">
              <strong>Features Demonstrated:</strong>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>
                  <strong>Task 4.1:</strong> Prominent "RESOLVED" status with
                  green coloring and total resolution time display
                </li>
                <li>
                  <strong>Task 4.2:</strong> Real-time progress indicators
                  showing each resolution phase (Detection → Diagnosis →
                  Prediction → Resolution → Communication)
                </li>
                <li>
                  <strong>Task 4.3:</strong> Incident overview panel with active
                  vs resolved counts, maintains resolved status visibility for
                  30 seconds
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Enhanced Incident Status Panel */}
      <IncidentStatusPanel
        useRealStatus={demoMode !== "static"}
        showOverview={showOverview}
        overviewData={overviewData}
        incidentId="INC-2024-001"
        title="Database Performance Degradation"
        severity="critical"
        startTime={new Date(Date.now() - 3600000)}
        description="We are currently experiencing performance issues with our primary database cluster. Our team is actively investigating and working on a resolution."
        affectedServices={[
          { name: "API Gateway", status: "degraded", impact: "High latency" },
          {
            name: "Database Cluster",
            status: "down",
            impact: "Connection timeouts",
          },
          {
            name: "Authentication Service",
            status: "operational",
            impact: "No impact",
          },
          {
            name: "Email Service",
            status: "degraded",
            impact: "Delayed delivery",
          },
        ]}
      />

      {/* Status Information */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center text-sm text-muted-foreground"
      >
        {demoMode === "static" &&
          "Static mode - showing traditional incident panel"}
        {demoMode === "active" &&
          "Active incident - watch the progress indicators update in real-time"}
        {demoMode === "resolved" &&
          "Incident resolved - notice the prominent resolution banner and updated overview"}
      </motion.div>
    </div>
  );
};

export default EnhancedIncidentStatusExample;
