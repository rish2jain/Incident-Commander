import * as React from "react";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Clock,
  Cpu,
  MemoryStick,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Progress } from "./ui/progress";
import { cn } from "../lib/utils";
import {
  useMemoryLeakPrevention,
  MemoryStats,
  DEFAULT_MEMORY_CONFIG,
} from "../lib/memory-leak-prevention";

interface MemoryMonitorProps {
  className?: string;
  showDetails?: boolean;
  enableAlerts?: boolean;
  updateInterval?: number;
}

const MemoryMonitor = React.memo(function MemoryMonitor({
  className = "",
  showDetails = false,
  enableAlerts = true,
  updateInterval = 5000,
}: MemoryMonitorProps) {
  const [memoryStats, setMemoryStats] = React.useState<MemoryStats>({
    usedJSHeapSize: 0,
    totalJSHeapSize: 0,
    jsHeapSizeLimit: 0,
    memoryUsageMB: 0,
    isMemoryAvailable: false,
    trend: "stable",
    leakSuspected: false,
  });

  const [resourceSummary, setResourceSummary] = React.useState({
    eventListeners: 0,
    timers: 0,
    observers: 0,
    subscriptions: 0,
    total: 0,
  });

  const [alerts, setAlerts] = React.useState<string[]>([]);

  // Memory leak prevention hook
  const {
    getMemoryStats,
    getResourceSummary,
    onMemoryWarning,
    onLeakDetected,
    setTimeout: safeSetTimeout,
  } = useMemoryLeakPrevention("MemoryMonitor");

  // Update memory stats periodically
  React.useEffect(() => {
    const updateStats = () => {
      const stats = getMemoryStats();
      const resources = getResourceSummary();

      setMemoryStats(stats);
      setResourceSummary(resources);
    };

    // Initial update
    updateStats();

    // Set up interval for periodic updates
    const intervalId = window.setInterval(() => {
      updateStats();
    }, updateInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [getMemoryStats, getResourceSummary, updateInterval, safeSetTimeout]);

  // Set up memory warning alerts
  React.useEffect(() => {
    if (!enableAlerts) return;

    const unsubscribeWarning = onMemoryWarning((stats) => {
      const message = `High memory usage: ${stats.memoryUsageMB.toFixed(1)}MB`;
      setAlerts((prev) => [...prev.slice(-4), message]); // Keep last 5 alerts
    });

    const unsubscribeLeak = onLeakDetected((stats) => {
      const message = `Memory leak suspected: ${stats.memoryUsageMB.toFixed(
        1
      )}MB`;
      setAlerts((prev) => [...prev.slice(-4), message]);
    });

    return () => {
      unsubscribeWarning();
      unsubscribeLeak();
    };
  }, [enableAlerts, onMemoryWarning, onLeakDetected]);

  // Calculate memory usage percentage
  const memoryUsagePercent = React.useMemo(() => {
    if (!memoryStats.isMemoryAvailable || memoryStats.jsHeapSizeLimit === 0) {
      return 0;
    }
    return (memoryStats.usedJSHeapSize / memoryStats.jsHeapSizeLimit) * 100;
  }, [memoryStats]);

  // Get trend icon and color
  const getTrendInfo = React.useMemo(() => {
    switch (memoryStats.trend) {
      case "increasing":
        return {
          icon: TrendingUp,
          color: "text-red-500",
          bgColor: "bg-red-500/10",
          label: "Increasing",
        };
      case "decreasing":
        return {
          icon: TrendingDown,
          color: "text-green-500",
          bgColor: "bg-green-500/10",
          label: "Decreasing",
        };
      default:
        return {
          icon: Minus,
          color: "text-blue-500",
          bgColor: "bg-blue-500/10",
          label: "Stable",
        };
    }
  }, [memoryStats.trend]);

  const TrendIcon = getTrendInfo.icon;

  if (!memoryStats.isMemoryAvailable) {
    return (
      <Card className={cn("", className)}>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-muted-foreground">
            <MemoryStick className="w-4 h-4" />
            <span className="text-sm">Memory monitoring not available</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20 flex items-center justify-center">
            <MemoryStick className="w-4 h-4 text-purple-500" />
          </div>
          <span className="text-sm">Memory Monitor</span>

          <div className="flex items-center gap-2 ml-auto">
            <Badge
              variant="outline"
              className={cn(
                "text-xs",
                getTrendInfo.bgColor,
                getTrendInfo.color,
                "border-current/20"
              )}
            >
              <TrendIcon className="w-3 h-3 mr-1" />
              {getTrendInfo.label}
            </Badge>

            {memoryStats.leakSuspected && (
              <Badge
                variant="outline"
                className="text-xs bg-red-500/10 text-red-500 border-red-500/20 animate-pulse"
              >
                <AlertTriangle className="w-3 h-3 mr-1" />
                Leak Suspected
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Memory Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Memory Usage</span>
            <span className="font-medium">
              {memoryStats.memoryUsageMB.toFixed(1)} MB
            </span>
          </div>
          <Progress value={memoryUsagePercent} className="h-2" />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>0 MB</span>
            <span>
              {(memoryStats.jsHeapSizeLimit / (1024 * 1024)).toFixed(0)} MB
              limit
            </span>
          </div>
        </div>

        {/* Resource Summary */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Activity className="w-3 h-3" />
              <span>Event Listeners</span>
            </div>
            <div className="text-sm font-medium">
              {resourceSummary.eventListeners}
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>Timers</span>
            </div>
            <div className="text-sm font-medium">{resourceSummary.timers}</div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <BarChart3 className="w-3 h-3" />
              <span>Observers</span>
            </div>
            <div className="text-sm font-medium">
              {resourceSummary.observers}
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Cpu className="w-3 h-3" />
              <span>Subscriptions</span>
            </div>
            <div className="text-sm font-medium">
              {resourceSummary.subscriptions}
            </div>
          </div>
        </div>

        {/* Detailed Stats */}
        {showDetails && (
          <div className="pt-3 border-t border-border/50 space-y-2">
            <div className="text-xs text-muted-foreground">
              Detailed Statistics
            </div>
            <div className="grid grid-cols-1 gap-1 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Used Heap:</span>
                <span>
                  {(memoryStats.usedJSHeapSize / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Heap:</span>
                <span>
                  {(memoryStats.totalJSHeapSize / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Heap Limit:</span>
                <span>
                  {(memoryStats.jsHeapSizeLimit / (1024 * 1024)).toFixed(0)} MB
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Resources:</span>
                <span>{resourceSummary.total}</span>
              </div>
            </div>
          </div>
        )}

        {/* Recent Alerts */}
        {enableAlerts && alerts.length > 0 && (
          <div className="pt-3 border-t border-border/50 space-y-2">
            <div className="text-xs text-muted-foreground">Recent Alerts</div>
            <div className="space-y-1">
              {alerts.slice(-3).map((alert, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-2 text-xs"
                >
                  <AlertTriangle className="w-3 h-3 text-amber-500 flex-shrink-0" />
                  <span className="text-muted-foreground truncate">
                    {alert}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

export default MemoryMonitor;
