import * as React from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Clock,
  Target,
  Users,
  AlertTriangle,
  CheckCircle,
  Activity,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import EnhancedMetricCard from "./EnhancedMetricCard";

interface MetricData {
  id: string;
  label: string;
  value: string | number;
  previousValue?: string | number;
  change?: number;
  changeType?: "increase" | "decrease";
  trend?: "up" | "down" | "stable";
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
  format?: "currency" | "percentage" | "time" | "number";
  description?: string;
}

interface MetricsPanelProps {
  metrics: MetricData[];
  title?: string;
  className?: string;
  animated?: boolean;
}

function formatValue(value: string | number, format?: string): string {
  if (typeof value === "string") return value;

  switch (format) {
    case "currency":
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }).format(value);
    case "percentage":
      return `${value}%`;
    case "time":
      return `${value}s`;
    case "number":
      return new Intl.NumberFormat("en-US").format(value);
    default:
      return String(value);
  }
}

function MetricCard({
  metric,
  index,
  animated = true,
}: {
  metric: MetricData;
  index: number;
  animated?: boolean;
}) {
  const Icon = metric.icon;
  const [displayValue, setDisplayValue] = React.useState(0);
  const targetValue = typeof metric.value === "number" ? metric.value : 0;

  // Animate number counting
  React.useEffect(() => {
    if (!animated || typeof metric.value !== "number") return;

    const duration = 1000;
    const steps = 60;
    const stepValue = targetValue / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      setDisplayValue(Math.min(stepValue * currentStep, targetValue));

      if (currentStep >= steps) {
        clearInterval(timer);
        setDisplayValue(targetValue);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [targetValue, animated]);

  const getTrendIcon = () => {
    if (!metric.trend) return null;

    switch (metric.trend) {
      case "up":
        return <TrendingUp className="w-3 h-3 text-green-500" />;
      case "down":
        return <TrendingDown className="w-3 h-3 text-red-500" />;
      default:
        return null;
    }
  };

  const getChangeColor = () => {
    if (!metric.change) return "text-muted-foreground";
    return metric.changeType === "increase" ? "text-green-500" : "text-red-500";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay: index * 0.1,
        type: "spring",
        stiffness: 400,
        damping: 25,
      }}
      whileHover={{ y: -2 }}
      className="group"
    >
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div
              className={`p-2.5 rounded-xl bg-gradient-to-br ${metric.bgColor} border ${metric.borderColor} group-hover:scale-105 transition-transform duration-200`}
            >
              <Icon className={`w-5 h-5 ${metric.color}`} />
            </div>

            <div className="flex items-center gap-1">
              {getTrendIcon()}
              {metric.change && (
                <span className={`text-xs font-medium ${getChangeColor()}`}>
                  {metric.changeType === "increase" ? "+" : ""}
                  {metric.change}%
                </span>
              )}
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              {metric.label}
            </p>

            <div className="flex items-baseline gap-2">
              <motion.p
                className="text-2xl font-bold text-foreground"
                key={displayValue}
                initial={{ scale: 1.1 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.2 }}
              >
                {animated && typeof metric.value === "number"
                  ? formatValue(displayValue, metric.format)
                  : formatValue(metric.value, metric.format)}
              </motion.p>

              {metric.previousValue && (
                <span className="text-xs text-muted-foreground">
                  from {formatValue(metric.previousValue, metric.format)}
                </span>
              )}
            </div>

            {metric.description && (
              <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                {metric.description}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function MetricsPanel({
  metrics,
  title = "Performance Metrics",
  className = "",
  animated = true,
}: MetricsPanelProps) {
  return (
    <Card className={`h-full ${className}`}>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500/10 to-emerald-600/10 border border-green-500/20 flex items-center justify-center">
            <Activity className="w-4 h-4 text-green-500" />
          </div>
          {title}
          <Badge variant="outline" className="ml-auto">
            Live
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {metrics.map((metric, index) => (
          <MetricCard
            key={metric.id}
            metric={metric}
            index={index}
            animated={animated}
          />
        ))}
      </CardContent>
    </Card>
  );
}

// Predefined metric configurations for Incident Commander
export const incidentCommanderMetrics: MetricData[] = [
  {
    id: "active-incidents",
    label: "Active Incidents",
    value: 0,
    previousValue: 3,
    change: -100,
    changeType: "decrease",
    trend: "down",
    icon: AlertTriangle,
    color: "text-red-500",
    bgColor: "from-red-500/10 to-red-600/10",
    borderColor: "border-red-500/20",
    format: "number",
    description: "Currently active incidents requiring attention",
  },
  {
    id: "resolved-today",
    label: "Resolved Today",
    value: 12,
    previousValue: 8,
    change: 50,
    changeType: "increase",
    trend: "up",
    icon: CheckCircle,
    color: "text-green-500",
    bgColor: "from-green-500/10 to-green-600/10",
    borderColor: "border-green-500/20",
    format: "number",
    description: "Incidents resolved autonomously today",
  },
  {
    id: "mttr-reduction",
    label: "MTTR Reduction",
    value: 95,
    previousValue: 87,
    change: 8,
    changeType: "increase",
    trend: "up",
    icon: Zap,
    color: "text-cyan-500",
    bgColor: "from-cyan-500/10 to-cyan-600/10",
    borderColor: "border-cyan-500/20",
    format: "percentage",
    description: "Mean Time To Resolution improvement",
  },
  {
    id: "cost-savings",
    label: "Cost Savings",
    value: 1240000,
    previousValue: 980000,
    change: 26.5,
    changeType: "increase",
    trend: "up",
    icon: DollarSign,
    color: "text-emerald-500",
    bgColor: "from-emerald-500/10 to-emerald-600/10",
    borderColor: "border-emerald-500/20",
    format: "currency",
    description: "Total cost savings from automation",
  },
  {
    id: "avg-resolution-time",
    label: "Avg Resolution Time",
    value: 167,
    previousValue: 1800,
    change: -90.7,
    changeType: "decrease",
    trend: "down",
    icon: Clock,
    color: "text-blue-500",
    bgColor: "from-blue-500/10 to-blue-600/10",
    borderColor: "border-blue-500/20",
    format: "time",
    description: "Average time to resolve incidents",
  },
  {
    id: "success-rate",
    label: "Success Rate",
    value: 92.5,
    previousValue: 89.2,
    change: 3.3,
    changeType: "increase",
    trend: "up",
    icon: Target,
    color: "text-purple-500",
    bgColor: "from-purple-500/10 to-purple-600/10",
    borderColor: "border-purple-500/20",
    format: "percentage",
    description: "Autonomous resolution success rate",
  },
  {
    id: "active-agents",
    label: "Active Agents",
    value: 5,
    previousValue: 5,
    trend: "stable",
    icon: Users,
    color: "text-indigo-500",
    bgColor: "from-indigo-500/10 to-indigo-600/10",
    borderColor: "border-indigo-500/20",
    format: "number",
    description: "AI agents currently online and active",
  },
];

// Demo component
export function MetricsPanelDemo() {
  const [metrics, setMetrics] = React.useState(incidentCommanderMetrics);

  // Simulate real-time updates
  React.useEffect(() => {
    const interval = setInterval(() => {
      setMetrics((prev) =>
        prev.map((metric) => {
          if (Math.random() < 0.2) {
            const currentValue =
              typeof metric.value === "number" ? metric.value : 0;
            const variation = Math.random() * 0.1 - 0.05; // ±5% variation
            const newValue = Math.max(
              0,
              Math.round(currentValue * (1 + variation))
            );

            return {
              ...metric,
              previousValue: metric.value,
              value: newValue,
              change:
                currentValue > 0
                  ? Math.round(
                      ((newValue - currentValue) / currentValue) * 100 * 10
                    ) / 10
                  : 0,
              changeType:
                newValue > currentValue
                  ? ("increase" as const)
                  : ("decrease" as const),
              trend:
                newValue > currentValue
                  ? ("up" as const)
                  : newValue < currentValue
                  ? ("down" as const)
                  : ("stable" as const),
            };
          }
          return metric;
        })
      );
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 max-w-md mx-auto">
      <MetricsPanel
        metrics={metrics}
        title="Live System Metrics"
        animated={true}
      />
    </div>
  );
}
