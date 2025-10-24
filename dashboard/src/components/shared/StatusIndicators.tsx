/**
 * Shared Status Indicator Components
 *
 * Provides consistent status indicators for agents, incidents, and system states.
 * Uses centralized design tokens for uniform styling.
 */

import React from "react";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";

// Agent Status Indicator
interface AgentStatusProps {
  agent: string;
  status: "active" | "idle" | "error" | "analyzing" | "complete";
  confidence?: number;
  className?: string;
}

export function AgentStatus({
  agent,
  status,
  confidence,
  className,
}: AgentStatusProps) {
  const getAgentIcon = (agentType: string) => {
    const icons: Record<string, string> = {
      detection: "🔍",
      diagnosis: "🔬",
      prediction: "🔮",
      resolution: "⚙️",
      communication: "📢",
    };
    return icons[agentType.toLowerCase()] || "🤖";
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: "status-active",
      idle: "status-idle",
      error: "severity-critical",
      analyzing: "severity-high",
      complete: "status-resolved",
    };
    return colors[status] || "status-idle";
  };

  const agentClass = `agent-${agent.toLowerCase()}`;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="text-lg">{getAgentIcon(agent)}</span>
      <div className="flex flex-col">
        <Badge variant="outline" className={cn(agentClass, "text-xs")}>
          {agent}
        </Badge>
        <Badge
          variant="secondary"
          className={cn(getStatusColor(status), "text-xs mt-1")}
        >
          {status}
        </Badge>
      </div>
      {confidence !== undefined && (
        <div className="text-xs text-slate-400">
          {(confidence * 100).toFixed(1)}%
        </div>
      )}
    </div>
  );
}

// Incident Severity Indicator
interface SeverityIndicatorProps {
  severity: "critical" | "high" | "medium" | "low";
  className?: string;
}

export function SeverityIndicator({
  severity,
  className,
}: SeverityIndicatorProps) {
  const severityClass = `severity-${severity}`;

  const severityIcons: Record<string, string> = {
    critical: "🔴",
    high: "🟠",
    medium: "🟡",
    low: "🟢",
  };

  return (
    <Badge variant="outline" className={cn(severityClass, className)}>
      <span className="mr-1">{severityIcons[severity]}</span>
      {severity.toUpperCase()}
    </Badge>
  );
}

// Incident Status Indicator
interface IncidentStatusProps {
  status: "active" | "resolved" | "investigating";
  className?: string;
}

export function IncidentStatus({ status, className }: IncidentStatusProps) {
  const statusClass = `status-${status}`;

  const statusIcons: Record<string, string> = {
    active: "🚨",
    resolved: "✅",
    investigating: "🔍",
  };

  return (
    <Badge variant="secondary" className={cn(statusClass, className)}>
      <span className="mr-1">{statusIcons[status]}</span>
      {status.toUpperCase()}
    </Badge>
  );
}

// Confidence Score Indicator
interface ConfidenceScoreProps {
  confidence: number;
  showPercentage?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function ConfidenceScore({
  confidence,
  showPercentage = true,
  size = "md",
  className,
}: ConfidenceScoreProps) {
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "text-green-400";
    if (score >= 0.6) return "text-yellow-400";
    if (score >= 0.4) return "text-orange-400";
    return "text-red-400";
  };

  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "w-12 h-2 bg-slate-700 rounded-full overflow-hidden",
          size === "sm" && "w-8 h-1.5",
          size === "lg" && "w-16 h-3"
        )}
      >
        <div
          className={cn(
            "h-full transition-all duration-300",
            getConfidenceColor(confidence)
          )}
          style={{
            width: `${confidence * 100}%`,
            backgroundColor: "currentColor",
          }}
        />
      </div>
      {showPercentage && (
        <span
          className={cn(
            "font-mono font-medium",
            getConfidenceColor(confidence),
            sizeClasses[size]
          )}
        >
          {(confidence * 100).toFixed(1)}%
        </span>
      )}
    </div>
  );
}

// System Health Indicator
interface SystemHealthProps {
  health: "healthy" | "warning" | "critical";
  metric?: string;
  value?: string | number;
  className?: string;
}

export function SystemHealth({
  health,
  metric,
  value,
  className,
}: SystemHealthProps) {
  const healthColors: Record<string, string> = {
    healthy: "text-green-400",
    warning: "text-yellow-400",
    critical: "text-red-400",
  };

  const healthIcons: Record<string, string> = {
    healthy: "💚",
    warning: "⚠️",
    critical: "🔴",
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span>{healthIcons[health]}</span>
      <div className="flex flex-col">
        {metric && <span className="text-xs text-slate-400">{metric}</span>}
        <span className={cn("text-sm font-medium", healthColors[health])}>
          {value || health.toUpperCase()}
        </span>
      </div>
    </div>
  );
}

// MTTR Indicator
interface MTTRIndicatorProps {
  currentMTTR: number;
  targetMTTR?: number;
  unit?: "seconds" | "minutes";
  className?: string;
}

export function MTTRIndicator({
  currentMTTR,
  targetMTTR,
  unit = "seconds",
  className,
}: MTTRIndicatorProps) {
  const formatTime = (time: number, unit: string) => {
    if (unit === "minutes") {
      const mins = Math.floor(time);
      const secs = Math.floor((time - mins) * 60);
      return `${mins}:${secs.toString().padStart(2, "0")}`;
    }
    return `${time}s`;
  };

  const isUnderTarget = targetMTTR ? currentMTTR <= targetMTTR : true;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="text-lg">⏱️</span>
      <div className="flex flex-col">
        <span className="text-xs text-slate-400">MTTR</span>
        <span
          className={cn(
            "text-sm font-mono font-medium",
            isUnderTarget ? "text-green-400" : "text-red-400"
          )}
        >
          {formatTime(currentMTTR, unit)}
        </span>
        {targetMTTR && (
          <span className="text-xs text-slate-500">
            Target: {formatTime(targetMTTR, unit)}
          </span>
        )}
      </div>
    </div>
  );
}