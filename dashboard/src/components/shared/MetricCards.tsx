/**
 * Shared Metric Card Components
 *
 * Provides consistent metric display cards for all dashboards.
 * Uses centralized design tokens and shared styling patterns.
 */

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

// Basic Metric Card
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
  variant?: "default" | "glass" | "success" | "warning" | "error";
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  variant = "default",
  className,
}: MetricCardProps) {
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

  const getVariantClasses = (variant: string) => {
    switch (variant) {
      case "glass":
        return "card-glass";
      case "success":
        return "bg-green-500/10 border-green-500/30";
      case "warning":
        return "bg-yellow-500/10 border-yellow-500/30";
      case "error":
        return "bg-red-500/10 border-red-500/30";
      default:
        return "bg-slate-800/50 border-slate-700";
    }
  };

  return (
    <Card className={cn(getVariantClasses(variant), className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {icon && <span className="text-lg">{icon}</span>}
              <p className="text-sm text-slate-400">{title}</p>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-bold text-white">{value}</p>
              {trend && trendValue && (
                <div
                  className={cn(
                    "flex items-center gap-1 text-xs",
                    getTrendColor(trend)
                  )}
                >
                  <span>{getTrendIcon(trend)}</span>
                  <span>{trendValue}</span>
                </div>
              )}
            </div>
            {subtitle && (
              <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Progress Metric Card
interface ProgressMetricCardProps {
  title: string;
  value: number;
  maxValue: number;
  unit?: string;
  icon?: string;
  color?: "blue" | "green" | "yellow" | "red" | "purple";
  showPercentage?: boolean;
  className?: string;
}

export function ProgressMetricCard({
  title,
  value,
  maxValue,
  unit,
  icon,
  color = "blue",
  showPercentage = true,
  className,
}: ProgressMetricCardProps) {
  const percentage = (value / maxValue) * 100;

  const colorClasses = {
    blue: "text-blue-400",
    green: "text-green-400",
    yellow: "text-yellow-400",
    red: "text-red-400",
    purple: "text-purple-400",
  };

  return (
    <Card className={cn("bg-slate-800/50 border-slate-700", className)}>
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-4">
          {icon && <span className="text-lg">{icon}</span>}
          <p className="text-sm text-slate-400">{title}</p>
        </div>

        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <span className={cn("text-2xl font-bold", colorClasses[color])}>
              {value}
              {unit}
            </span>
            {showPercentage && (
              <span className="text-sm text-slate-400">
                {percentage.toFixed(1)}%
              </span>
            )}
          </div>

          <Progress value={percentage} className="h-2" />

          <div className="flex justify-between text-xs text-slate-500">
            <span>0{unit}</span>
            <span>
              {maxValue}
              {unit}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Comparison Metric Card
interface ComparisonMetricCardProps {
  title: string;
  currentValue: number;
  previousValue: number;
  unit?: string;
  icon?: string;
  format?: "number" | "percentage" | "currency" | "time";
  className?: string;
}

export function ComparisonMetricCard({
  title,
  currentValue,
  previousValue,
  unit = "",
  icon,
  format = "number",
  className,
}: ComparisonMetricCardProps) {
  const difference = currentValue - previousValue;
  const percentageChange =
    previousValue !== 0 ? (difference / previousValue) * 100 : 0;
  const isImprovement = difference < 0; // For MTTR, lower is better

  const formatValue = (value: number, format: string) => {
    switch (format) {
      case "percentage":
        return `${value.toFixed(1)}%`;
      case "currency":
        return `$${value.toLocaleString()}`;
      case "time":
        return `${value}s`;
      default:
        return `${value}${unit}`;
    }
  };

  return (
    <Card className={cn("bg-slate-800/50 border-slate-700", className)}>
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-4">
          {icon && <span className="text-lg">{icon}</span>}
          <p className="text-sm text-slate-400">{title}</p>
        </div>

        <div className="space-y-2">
          <div className="text-2xl font-bold text-white">
            {formatValue(currentValue, format)}
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant={isImprovement ? "default" : "destructive"}
              className="text-xs"
            >
              {isImprovement ? "📉" : "📈"}{" "}
              {Math.abs(percentageChange).toFixed(1)}%
            </Badge>
            <span className="text-xs text-slate-500">
              vs {formatValue(previousValue, format)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Status Grid Card
interface StatusGridCardProps {
  title: string;
  items: Array<{
    label: string;
    value: string | number;
    status: "success" | "warning" | "error" | "info";
    icon?: string;
  }>;
  className?: string;
}

export function StatusGridCard({
  title,
  items,
  className,
}: StatusGridCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "text-green-400";
      case "warning":
        return "text-yellow-400";
      case "error":
        return "text-red-400";
      case "info":
        return "text-blue-400";
      default:
        return "text-slate-400";
    }
  };

  return (
    <Card className={cn("bg-slate-800/50 border-slate-700", className)}>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {items.map((item, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {item.icon && <span className="text-sm">{item.icon}</span>}
                <span className="text-sm text-slate-400">{item.label}</span>
              </div>
              <span
                className={cn(
                  "text-sm font-medium",
                  getStatusColor(item.status)
                )}
              >
                {item.value}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Business Impact Card
interface BusinessImpactCardProps {
  title: string;
  savings: number;
  roi: number;
  paybackPeriod: number;
  className?: string;
}

export function BusinessImpactCard({
  title,
  savings,
  roi,
  paybackPeriod,
  className,
}: BusinessImpactCardProps) {
  return (
    <Card
      className={cn(
        "bg-gradient-to-br from-green-500/10 to-blue-500/10 border-green-500/30",
        className
      )}
    >
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          💰 {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                ${savings.toLocaleString()}
              </div>
              <div className="text-xs text-slate-400">Annual Savings</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{roi}%</div>
              <div className="text-xs text-slate-400">ROI</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">
                {paybackPeriod}mo
              </div>
              <div className="text-xs text-slate-400">Payback</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
