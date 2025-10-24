/**
 * Enhanced Interactive Metrics Components
 *
 * Implements improved readability, tooltips, and interactive features
 * based on user feedback for the AI Transparency Dashboard.
 */

import React, { useId, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Enhanced Tooltip Component
interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: "top" | "bottom" | "left" | "right";
}

export function Tooltip({ content, children, position = "top" }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipId = useId();

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setIsVisible(!isVisible);
    } else if (event.key === "Escape") {
      setIsVisible(false);
    }
  };

  return (
    <div
      className="relative inline-block"
      tabIndex={0}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
      onKeyDown={handleKeyDown}
      aria-describedby={isVisible ? tooltipId : undefined}
    >
      {children}
      {isVisible && (
        <div
          id={tooltipId}
          role="tooltip"
          aria-hidden={!isVisible}
          className={cn(
            "absolute z-50 px-3 py-2 text-sm text-white bg-slate-800 border border-slate-600 rounded-lg shadow-lg whitespace-nowrap",
            {
              "bottom-full left-1/2 transform -translate-x-1/2 mb-2":
                position === "top",
              "top-full left-1/2 transform -translate-x-1/2 mt-2":
                position === "bottom",
              "right-full top-1/2 transform -translate-y-1/2 mr-2":
                position === "left",
              "left-full top-1/2 transform -translate-y-1/2 ml-2":
                position === "right",
            }
          )}
        >
          {content}
          <div
            className={cn(
              "absolute w-2 h-2 bg-slate-800 border-slate-600 transform rotate-45",
              {
                "top-full left-1/2 -translate-x-1/2 -mt-1 border-b border-r":
                  position === "top",
                "bottom-full left-1/2 -translate-x-1/2 -mb-1 border-t border-l":
                  position === "bottom",
                "top-1/2 left-full -translate-y-1/2 -ml-1 border-t border-r":
                  position === "left",
                "top-1/2 right-full -translate-y-1/2 -mr-1 border-b border-l":
                  position === "right",
              }
            )}
          />
        </div>
      )}
    </div>
  );
}

// Enhanced Confidence Gauge with Uncertainty Range
interface EnhancedConfidenceGaugeProps {
  agent: string;
  confidence: number;
  uncertainty?: number;
  calculation?: string;
  className?: string;
}

export function EnhancedConfidenceGauge({
  agent,
  confidence,
  uncertainty = 0.02,
  calculation,
  className,
}: EnhancedConfidenceGaugeProps) {
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "bg-green-400";
    if (score >= 0.6) return "bg-yellow-400";
    if (score >= 0.4) return "bg-orange-400";
    return "bg-red-400";
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return "High";
    if (score >= 0.6) return "Medium";
    if (score >= 0.4) return "Low";
    return "Critical";
  };

  const tooltipContent =
    calculation ||
    `Confidence calculated from model accuracy (${(confidence * 100).toFixed(
      1
    )}%) across historical incidents. Uncertainty range: ±${(
      uncertainty * 100
    ).toFixed(1)}%`;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-white">{agent}</span>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {getConfidenceLabel(confidence)}
          </Badge>
          <Tooltip content={tooltipContent}>
            <span className="text-xs text-slate-400 cursor-help">ℹ️</span>
          </Tooltip>
        </div>
      </div>

      <div className="relative">
        {/* Main confidence bar */}
        <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full transition-all duration-500",
              getConfidenceColor(confidence)
            )}
            style={{ width: `${confidence * 100}%` }}
          />
        </div>

        {/* Uncertainty range indicator */}
        <div
          className="absolute top-0 h-3 bg-white/20 rounded-full"
          style={{
            left: `${Math.max(0, (confidence - uncertainty) * 100)}%`,
            width: `${Math.min(
              100 - Math.max(0, (confidence - uncertainty) * 100),
              uncertainty * 200
            )}%`,
          }}
        />
      </div>

      <div className="flex justify-between text-xs">
        <span className="text-slate-500">
          {((confidence - uncertainty) * 100).toFixed(1)}%
        </span>
        <span className="font-mono font-medium text-white">
          {(confidence * 100).toFixed(1)}%
        </span>
        <span className="text-slate-500">
          {((confidence + uncertainty) * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

// Interactive Metric Card with Click-to-Expand
interface InteractiveMetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
  details?: Array<{ label: string; value: string; description?: string }>;
  sparklineData?: number[];
  className?: string;
}

export function InteractiveMetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  details,
  sparklineData,
  className,
}: InteractiveMetricCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case "up":
        return "📈";
      case "down":
        return "📉";
      case "stable":
        return "➡️";
      default:
        return null;
    }
  };

  const getTrendColor = (trend?: string) => {
    switch (trend) {
      case "up":
        return "text-green-400";
      case "down":
        return "text-red-400";
      case "stable":
        return "text-slate-400";
      default:
        return "text-slate-400";
    }
  };

  return (
    <Card
      className={cn(
        "card-glass cursor-pointer transition-all duration-300",
        className
      )}
    >
      <CardContent className="p-6" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {icon && <span className="text-lg">{icon}</span>}
            <Tooltip
              content={`Click to ${isExpanded ? "collapse" : "expand"} details`}
            >
              <p className="text-sm text-slate-400 font-medium">{title}</p>
            </Tooltip>
          </div>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
            {isExpanded ? "−" : "+"}
          </Button>
        </div>

        <div className="flex items-baseline gap-3 mb-2">
          <p className="text-3xl font-bold text-white">{value}</p>
          {trend && trendValue && (
            <div
              className={cn(
                "flex items-center gap-1 text-sm",
                getTrendColor(trend)
              )}
            >
              <span>{getTrendIcon(trend)}</span>
              <span>{trendValue}</span>
            </div>
          )}
        </div>

        {subtitle && <p className="text-sm text-slate-500 mb-3">{subtitle}</p>}

        {/* Sparkline visualization */}
        {sparklineData && (
          <div className="h-8 mb-3">
            <svg width="100%" height="100%" className="text-blue-400">
              <polyline
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                points={sparklineData
                  .map((value, index) => {
                    const xDenom = sparklineData.length - 1;
                    const x = xDenom === 0 ? 50 : (index / xDenom) * 100;
                    const y = 100 - value * 100;
                    return `${x},${y}`;
                  })
                  .join(" ")}
              />
            </svg>
          </div>
        )}

        {/* Expandable details */}
        {isExpanded && details && (
          <div className="mt-4 pt-4 border-t border-slate-600 space-y-3 animate-slide-up">
            {details.map((detail, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300">{detail.label}</span>
                  {detail.description && (
                    <Tooltip content={detail.description}>
                      <span className="text-xs text-slate-500 cursor-help">
                        ℹ️
                      </span>
                    </Tooltip>
                  )}
                </div>
                <span className="text-sm font-medium text-white">
                  {detail.value}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Enhanced Performance Trends Component
interface PerformanceTrendsProps {
  metrics: Array<{
    name: string;
    current: number;
    baseline: number;
    unit: string;
    trend: number[];
    target?: number;
  }>;
  className?: string;
}

export function PerformanceTrends({
  metrics,
  className,
}: PerformanceTrendsProps) {
  return (
    <Card className={cn("card-glass", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          📊 Performance Trends
          <Tooltip content="Historical performance metrics showing improvement over time">
            <span className="text-sm text-slate-400 cursor-help">ℹ️</span>
          </Tooltip>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {metrics.map((metric, index) => {
            const improvement =
              ((metric.baseline - metric.current) / metric.baseline) * 100;
            const isImprovement = improvement > 0;

            return (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">
                    {metric.name}
                  </span>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={isImprovement ? "default" : "destructive"}
                      className="text-xs"
                    >
                      {isImprovement ? "📉" : "📈"}{" "}
                      {Math.abs(improvement).toFixed(1)}%
                    </Badge>
                    {metric.target && (
                      <Tooltip
                        content={`Target: ${metric.target}${metric.unit}`}
                      >
                        <span className="text-xs text-slate-400">🎯</span>
                      </Tooltip>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="text-lg font-mono font-bold text-white">
                      {metric.current}
                      {metric.unit}
                    </div>
                    <div className="text-xs text-slate-500">
                      Baseline: {metric.baseline}
                      {metric.unit}
                    </div>
                  </div>

                  {/* Mini trend chart */}
                  <div className="w-24 h-8">
                    <svg width="100%" height="100%" className="text-blue-400">
                      <polyline
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        points={metric.trend
                          .map((value, idx) => {
                            const min = Math.min(...metric.trend);
                            const max = Math.max(...metric.trend);
                            const denom = max - min;
                            const xDenom = metric.trend.length - 1;

                            // Handle division by zero cases
                            const x = xDenom === 0 ? 50 : (idx / xDenom) * 100;
                            const y =
                              denom === 0
                                ? 50
                                : 100 - ((value - min) / denom) * 100;

                            return `${x},${y}`;
                          })
                          .join(" ")}
                      />
                    </svg>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// Export Button Component
interface ExportButtonProps {
  onExport: (format: "pdf" | "csv" | "json") => void;
  className?: string;
}

export function ExportButton({ onExport, className }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={cn("relative", className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2"
      >
        📄 Export
        <span className={cn("transition-transform", isOpen && "rotate-180")}>
          ▼
        </span>
      </Button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 bg-slate-800 border border-slate-600 rounded-lg shadow-lg z-50 min-w-32">
          <div className="py-1">
            <button
              onClick={() => {
                onExport("pdf");
                setIsOpen(false);
              }}
              className="w-full px-3 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            >
              📄 PDF Report
            </button>
            <button
              onClick={() => {
                onExport("csv");
                setIsOpen(false);
              }}
              className="w-full px-3 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            >
              📊 CSV Data
            </button>
            <button
              onClick={() => {
                onExport("json");
                setIsOpen(false);
              }}
              className="w-full px-3 py-2 text-left text-sm text-white hover:bg-slate-700 flex items-center gap-2"
            >
              🔧 JSON Logs
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
