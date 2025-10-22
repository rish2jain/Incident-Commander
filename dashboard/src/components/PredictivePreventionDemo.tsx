"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
  Badge,
} from "./shared";

interface PredictiveAlert {
  id: string;
  timestamp: string;
  severity: "warning" | "critical";
  message: string;
  confidence: number;
  timeToImpact: number; // minutes
  preventionAction: string;
}

interface PredictivePreventionDemoProps {
  className?: string;
  onPreventionComplete?: () => void;
}

export const PredictivePreventionDemo: React.FC<
  PredictivePreventionDemoProps
> = ({ className, onPreventionComplete }) => {
  const [phase, setPhase] = useState<
    "monitoring" | "alert" | "prevention" | "success"
  >("monitoring");
  const [alert, setAlert] = useState<PredictiveAlert | null>(null);
  const [preventionProgress, setPreventionProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(0);

  useEffect(() => {
    const demoSequence = async () => {
      // Phase 1: Monitoring (3 seconds)
      await new Promise((resolve) => setTimeout(resolve, 3000));

      // Phase 2: Predictive Alert (4 seconds)
      setPhase("alert");
      setAlert({
        id: "pred-001",
        timestamp: new Date().toLocaleTimeString(),
        severity: "warning",
        message: "Log velocity suggests database failure in 15-30 minutes",
        confidence: 0.87,
        timeToImpact: 22,
        preventionAction:
          "Proactive connection pool scaling and query optimization",
      });
      setTimeRemaining(22);

      await new Promise((resolve) => setTimeout(resolve, 4000));

      // Phase 3: Prevention in progress (4 seconds)
      setPhase("prevention");

      // Simulate prevention progress
      const progressInterval = setInterval(() => {
        setPreventionProgress((prev) => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            return 100;
          }
          return prev + 25;
        });
      }, 1000);

      // Countdown timer
      const countdownInterval = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 0) {
            clearInterval(countdownInterval);
            return 0;
          }
          return prev - 1;
        });
      }, 200); // Faster countdown for demo

      await new Promise((resolve) => setTimeout(resolve, 4000));

      // Phase 4: Success (4 seconds)
      setPhase("success");
      clearInterval(progressInterval);
      clearInterval(countdownInterval);
      setPreventionProgress(100);
      setTimeRemaining(0);

      await new Promise((resolve) => setTimeout(resolve, 4000));

      // Notify completion
      if (onPreventionComplete) {
        onPreventionComplete();
      }
    };

    demoSequence();
  }, [onPreventionComplete]);

  const getPhaseIcon = () => {
    switch (phase) {
      case "monitoring":
        return "👁️";
      case "alert":
        return "⚠️";
      case "prevention":
        return "🔧";
      case "success":
        return "✅";
      default:
        return "👁️";
    }
  };

  const getPhaseTitle = () => {
    switch (phase) {
      case "monitoring":
        return "Continuous Monitoring";
      case "alert":
        return "Predictive Alert Triggered";
      case "prevention":
        return "Proactive Prevention in Progress";
      case "success":
        return "Incident Prevented Successfully";
      default:
        return "Monitoring";
    }
  };

  const getPhaseDescription = () => {
    switch (phase) {
      case "monitoring":
        return "AI agents continuously monitoring system patterns and early warning indicators";
      case "alert":
        return "Predictive models detected early warning signs 15-30 minutes before potential impact";
      case "prevention":
        return "Agents autonomously executing preventive measures to avoid incident occurrence";
      case "success":
        return "Incident successfully prevented - no customer impact, no reactive response needed";
      default:
        return "";
    }
  };

  return (
    <Card className={`card-glass ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getPhaseIcon()} Predictive Prevention System
          <Badge variant={phase === "success" ? "default" : "secondary"}>
            85% Prevention Rate
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Phase Status */}
        <div className="bg-slate-700/20 backdrop-blur-sm rounded-lg p-4">
          <h4 className="font-semibold mb-2">{getPhaseTitle()}</h4>
          <p className="text-sm text-status-neutral">{getPhaseDescription()}</p>
        </div>

        {/* Monitoring Phase */}
        {phase === "monitoring" && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-green-500/20 rounded-lg">
                <div className="text-2xl font-mono text-green-400">47</div>
                <div className="text-xs text-status-neutral">
                  Metrics Monitored
                </div>
              </div>
              <div className="text-center p-3 bg-blue-500/20 rounded-lg">
                <div className="text-2xl font-mono text-blue-400">12</div>
                <div className="text-xs text-status-neutral">
                  Services Tracked
                </div>
              </div>
              <div className="text-center p-3 bg-purple-500/20 rounded-lg">
                <div className="text-2xl font-mono text-purple-400">0.1%</div>
                <div className="text-xs text-status-neutral">
                  Current Error Rate
                </div>
              </div>
            </div>

            <div className="bg-green-500/20 rounded-lg p-4">
              <h4 className="font-semibold text-green-400 mb-2">
                System Health: Optimal
              </h4>
              <div className="text-sm space-y-1">
                <p>• All metrics within normal ranges</p>
                <p>• Predictive models analyzing patterns</p>
                <p>• Ready to detect early warning signs</p>
              </div>
            </div>
          </div>
        )}

        {/* Alert Phase */}
        {phase === "alert" && alert && (
          <div className="space-y-4">
            <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-yellow-400">
                  Predictive Alert
                </h4>
                <Badge
                  variant="outline"
                  className="text-yellow-400 border-yellow-400"
                >
                  {(alert.confidence * 100).toFixed(0)}% Confidence
                </Badge>
              </div>
              <p className="text-sm mb-3">{alert.message}</p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-status-neutral">Time to Impact:</span>
                  <span className="ml-2 font-mono text-yellow-400">
                    {timeRemaining} minutes
                  </span>
                </div>
                <div>
                  <span className="text-status-neutral">Severity:</span>
                  <span className="ml-2 capitalize text-yellow-400">
                    {alert.severity}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-blue-500/20 rounded-lg p-4">
              <h4 className="font-semibold text-blue-400 mb-2">
                Planned Prevention Action
              </h4>
              <p className="text-sm">{alert.preventionAction}</p>
            </div>
          </div>
        )}

        {/* Prevention Phase */}
        {phase === "prevention" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Prevention Progress</span>
                <span className="font-mono text-lg text-blue-400">
                  {preventionProgress}%
                </span>
              </div>
              <Progress value={preventionProgress} className="h-3" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-500/20 rounded-lg p-3">
                <h5 className="font-semibold text-blue-400 mb-2">
                  Actions Taken
                </h5>
                <div className="text-sm space-y-1">
                  <div
                    className={
                      preventionProgress >= 25
                        ? "text-green-400"
                        : "text-status-neutral"
                    }
                  >
                    {preventionProgress >= 25 ? "✅" : "⏳"} Scale connection
                    pool
                  </div>
                  <div
                    className={
                      preventionProgress >= 50
                        ? "text-green-400"
                        : "text-status-neutral"
                    }
                  >
                    {preventionProgress >= 50 ? "✅" : "⏳"} Optimize query
                    patterns
                  </div>
                  <div
                    className={
                      preventionProgress >= 75
                        ? "text-green-400"
                        : "text-status-neutral"
                    }
                  >
                    {preventionProgress >= 75 ? "✅" : "⏳"} Adjust load
                    balancing
                  </div>
                  <div
                    className={
                      preventionProgress >= 100
                        ? "text-green-400"
                        : "text-status-neutral"
                    }
                  >
                    {preventionProgress >= 100 ? "✅" : "⏳"} Verify system
                    stability
                  </div>
                </div>
              </div>

              <div className="bg-yellow-500/20 rounded-lg p-3">
                <h5 className="font-semibold text-yellow-400 mb-2">
                  Time Remaining
                </h5>
                <div className="text-center">
                  <div className="text-3xl font-mono text-yellow-400">
                    {timeRemaining}
                  </div>
                  <div className="text-xs text-status-neutral">
                    minutes to potential impact
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Success Phase */}
        {phase === "success" && (
          <div className="space-y-4">
            <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4">
              <h4 className="font-semibold text-green-400 mb-2">
                🎉 Incident Successfully Prevented
              </h4>
              <div className="text-sm space-y-1">
                <p>• Proactive measures completed before any customer impact</p>
                <p>• System performance maintained at optimal levels</p>
                <p>• No reactive incident response required</p>
                <p>• Cost savings: $5,600 (avoided incident cost)</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-green-500/20 rounded-lg">
                <div className="text-2xl font-mono text-green-400">85%</div>
                <div className="text-xs text-status-neutral">
                  Prevention Success Rate
                </div>
              </div>
              <div className="text-center p-3 bg-blue-500/20 rounded-lg">
                <div className="text-2xl font-mono text-blue-400">$0</div>
                <div className="text-xs text-status-neutral">
                  Customer Impact Cost
                </div>
              </div>
              <div className="text-center p-3 bg-purple-500/20 rounded-lg">
                <div className="text-2xl font-mono text-purple-400">0min</div>
                <div className="text-xs text-status-neutral">Downtime</div>
              </div>
            </div>
          </div>
        )}

        {/* Competitive Advantage */}
        <div className="bg-purple-500/20 rounded-lg p-4">
          <h4 className="font-semibold text-purple-400 mb-2">
            🏆 Unique Competitive Advantage
          </h4>
          <div className="text-sm space-y-1">
            <p>
              • <strong>Only predictive prevention system</strong> - competitors
              are reactive only
            </p>
            <p>
              • 15-30 minute advance warning vs 0 minutes (traditional systems)
            </p>
            <p>• 85% incident prevention rate vs 0% (reactive systems)</p>
            <p>• Proactive cost avoidance vs reactive damage control</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PredictivePreventionDemo;
