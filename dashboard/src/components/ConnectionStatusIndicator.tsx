import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Wifi,
  WifiOff,
  AlertCircle,
  RefreshCw,
  CheckCircle,
  Clock,
  Signal,
  Loader2,
} from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { Progress } from "./ui/progress";
import { useConnection } from "../lib/hooks/useConnection";
import { ConnectionState } from "../types";

interface ConnectionStatusIndicatorProps {
  showDetails?: boolean;
  showReconnectButton?: boolean;
  className?: string;
  onManualReconnect?: () => void;
}

export function ConnectionStatusIndicator({
  showDetails = false,
  showReconnectButton = true,
  className = "",
  onManualReconnect,
}: ConnectionStatusIndicatorProps) {
  const {
    connectionState,
    connectionMetrics,
    isConnected,
    reconnect,
    measureLatency,
  } = useConnection();

  const [isReconnecting, setIsReconnecting] = React.useState(false);

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      await reconnect();
      onManualReconnect?.();
    } catch (error) {
      console.error("Manual reconnect failed:", error);
    } finally {
      setIsReconnecting(false);
    }
  };

  const getStatusIcon = () => {
    switch (connectionState.status) {
      case "connected":
        return <Wifi className="h-4 w-4 text-green-500" />;
      case "connecting":
      case "reconnecting":
        return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />;
      case "disconnected":
        return <WifiOff className="h-4 w-4 text-gray-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <WifiOff className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (connectionState.status) {
      case "connected":
        return "bg-green-500";
      case "connecting":
      case "reconnecting":
        return "bg-yellow-500";
      case "disconnected":
        return "bg-gray-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusText = () => {
    switch (connectionState.status) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return `Reconnecting... (${connectionState.reconnectAttempts}/10)`;
      case "disconnected":
        return "Disconnected";
      case "error":
        return "Connection Error";
      default:
        return "Unknown";
    }
  };

  const getQualityColor = () => {
    switch (connectionState.connectionQuality) {
      case "excellent":
        return "text-green-500";
      case "good":
        return "text-yellow-500";
      case "poor":
        return "text-red-500";
      default:
        return "text-gray-500";
    }
  };

  const getQualityBars = () => {
    const bars = [];
    const quality = connectionState.connectionQuality;
    const barCount =
      quality === "excellent"
        ? 4
        : quality === "good"
        ? 3
        : quality === "poor"
        ? 2
        : 1;

    for (let i = 0; i < 4; i++) {
      bars.push(
        <motion.div
          key={i}
          className={`w-1 rounded-full ${
            i < barCount
              ? getQualityColor().replace("text-", "bg-")
              : "bg-gray-300"
          }`}
          style={{ height: `${(i + 1) * 3 + 2}px` }}
          initial={{ opacity: 0, scaleY: 0 }}
          animate={{ opacity: 1, scaleY: 1 }}
          transition={{ delay: i * 0.1 }}
        />
      );
    }
    return bars;
  };

  const formatLatency = (latency: number) => {
    if (latency <= 0) return "N/A";
    return `${latency}ms`;
  };

  const formatUptime = () => {
    if (!connectionState.lastConnected) return "N/A";
    const uptime = Date.now() - connectionState.lastConnected.getTime();
    const minutes = Math.floor(uptime / 60000);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m`;
    return "<1m";
  };

  const reconnectProgress =
    connectionState.status === "reconnecting"
      ? (connectionState.reconnectAttempts / 10) * 100
      : 0;

  return (
    <TooltipProvider>
      <div className={`flex items-center gap-2 ${className}`}>
        {/* Main Status Indicator */}
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-2 px-2 py-1 rounded-md bg-background/50 border border-border/50">
              <motion.div
                className="relative"
                animate={{ scale: isConnected ? [1, 1.1, 1] : 1 }}
                transition={{ duration: 2, repeat: isConnected ? Infinity : 0 }}
              >
                {getStatusIcon()}
                <motion.div
                  className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${getStatusColor()}`}
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              </motion.div>

              {showDetails && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">{getStatusText()}</span>

                  {/* Signal Quality Bars */}
                  {isConnected && (
                    <div className="flex items-end gap-0.5 h-3">
                      {getQualityBars()}
                    </div>
                  )}
                </div>
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-xs">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium">Connection Status</span>
                <Badge
                  variant={isConnected ? "default" : "destructive"}
                  className="text-xs"
                >
                  {getStatusText()}
                </Badge>
              </div>

              {isConnected && (
                <>
                  <div className="flex justify-between text-xs">
                    <span>Latency:</span>
                    <span className={getQualityColor()}>
                      {formatLatency(connectionState.latency)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Quality:</span>
                    <span className={getQualityColor()}>
                      {connectionState.connectionQuality}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Uptime:</span>
                    <span>{formatUptime()}</span>
                  </div>
                </>
              )}

              {connectionState.messageQueue.length > 0 && (
                <div className="flex justify-between text-xs">
                  <span>Queued Messages:</span>
                  <span className="text-yellow-500">
                    {connectionState.messageQueue.length}
                  </span>
                </div>
              )}

              {connectionState.status === "reconnecting" && (
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Reconnect Attempt:</span>
                    <span>{connectionState.reconnectAttempts}/10</span>
                  </div>
                  <Progress value={reconnectProgress} className="h-1" />
                </div>
              )}

              {!connectionState.isOnline && (
                <div className="text-xs text-red-500 flex items-center gap-1">
                  <WifiOff className="h-3 w-3" />
                  No internet connection
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>

        {/* Reconnect Button */}
        {showReconnectButton && !isConnected && connectionState.isOnline && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <Button
                variant="outline"
                size="sm"
                onClick={handleReconnect}
                disabled={
                  isReconnecting || connectionState.status === "connecting"
                }
                className="h-7 px-2 text-xs"
              >
                {isReconnecting ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <RefreshCw className="h-3 w-3" />
                )}
                <span className="ml-1">Reconnect</span>
              </Button>
            </motion.div>
          </AnimatePresence>
        )}

        {/* Connection Metrics (Extended Details) */}
        {showDetails && isConnected && (
          <div className="hidden lg:flex items-center gap-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Signal className="h-3 w-3" />
              <span>{formatLatency(connectionState.latency)}</span>
            </div>

            {connectionState.lastHeartbeat && (
              <div className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3 text-green-500" />
                <span>
                  Last ping:{" "}
                  {new Date(connectionState.lastHeartbeat).toLocaleTimeString()}
                </span>
              </div>
            )}

            {connectionMetrics.totalReconnections > 0 && (
              <div className="flex items-center gap-1">
                <RefreshCw className="h-3 w-3" />
                <span>{connectionMetrics.totalReconnections} reconnects</span>
              </div>
            )}
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}

// Compact version for header
export function CompactConnectionStatus({
  className = "",
}: {
  className?: string;
}) {
  return (
    <ConnectionStatusIndicator
      showDetails={false}
      showReconnectButton={false}
      className={className}
    />
  );
}

// Detailed version for settings or status pages
export function DetailedConnectionStatus({
  className = "",
}: {
  className?: string;
}) {
  return (
    <ConnectionStatusIndicator
      showDetails={true}
      showReconnectButton={true}
      className={className}
    />
  );
}
