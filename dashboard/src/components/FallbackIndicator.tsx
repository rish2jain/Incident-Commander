import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RefreshCw,
  Wifi,
  WifiOff,
  AlertTriangle,
  Clock,
  Database,
  Globe,
  Loader2,
} from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";
import { useFallback } from "../lib/hooks/useFallback";

interface FallbackIndicatorProps {
  showDetails?: boolean;
  className?: string;
}

export function FallbackIndicator({
  showDetails = false,
  className = "",
}: FallbackIndicatorProps) {
  const { fallbackState, isInFallbackMode, currentMode, manualRefresh } =
    useFallback();

  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    try {
      await manualRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  const getModeIcon = () => {
    switch (currentMode) {
      case "websocket":
        return <Wifi className="h-4 w-4 text-green-500" />;
      case "polling":
        return <RefreshCw className="h-4 w-4 text-yellow-500" />;
      case "offline":
        return <Database className="h-4 w-4 text-orange-500" />;
      case "manual":
        return <WifiOff className="h-4 w-4 text-red-500" />;
      default:
        return <Globe className="h-4 w-4 text-gray-500" />;
    }
  };

  const getModeText = () => {
    switch (currentMode) {
      case "websocket":
        return "Real-time";
      case "polling":
        return "Polling Mode";
      case "offline":
        return "Offline Mode";
      case "manual":
        return "Manual Mode";
      default:
        return "Unknown";
    }
  };

  const getModeDescription = () => {
    switch (currentMode) {
      case "websocket":
        return "Connected via WebSocket for real-time updates";
      case "polling":
        return "Fetching updates periodically due to connection issues";
      case "offline":
        return "Using cached data - no network connection";
      case "manual":
        return "Manual refresh required - connection unavailable";
      default:
        return "Connection status unknown";
    }
  };

  const getBadgeVariant = () => {
    switch (currentMode) {
      case "websocket":
        return "default";
      case "polling":
        return "secondary";
      case "offline":
        return "outline";
      case "manual":
        return "destructive";
      default:
        return "outline";
    }
  };

  if (!isInFallbackMode && currentMode === "websocket") {
    return null; // Don't show indicator when everything is working normally
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className={`${className}`}
      >
        {showDetails ? (
          <Card className="border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <motion.div
                    animate={{ rotate: currentMode === "polling" ? 360 : 0 }}
                    transition={{
                      duration: 2,
                      repeat: currentMode === "polling" ? Infinity : 0,
                    }}
                  >
                    {getModeIcon()}
                  </motion.div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-sm">{getModeText()}</h4>
                      <Badge variant={getBadgeVariant()} className="text-xs">
                        {isInFallbackMode ? "Fallback Active" : "Normal"}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {getModeDescription()}
                    </p>

                    {fallbackState.lastSuccessfulUpdate && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Last update:{" "}
                        {fallbackState.lastSuccessfulUpdate.toLocaleTimeString()}
                      </p>
                    )}

                    {fallbackState.lastError && (
                      <p className="text-xs text-red-600 mt-1">
                        Error: {fallbackState.lastError}
                      </p>
                    )}
                  </div>
                </div>

                {(currentMode === "manual" || currentMode === "offline") && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleManualRefresh}
                    disabled={isRefreshing}
                    className="h-8"
                  >
                    {isRefreshing ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <RefreshCw className="h-3 w-3" />
                    )}
                    <span className="ml-1">Refresh</span>
                  </Button>
                )}
              </div>

              {currentMode === "polling" && (
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>Polling attempts:</span>
                    <span>{fallbackState.pollingAttempts}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1">
                    <motion.div
                      className="bg-yellow-500 h-1 rounded-full"
                      initial={{ width: 0 }}
                      animate={{
                        width: `${(fallbackState.pollingAttempts / 20) * 100}%`,
                      }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          // Compact indicator
          <div className="flex items-center gap-2 px-2 py-1 rounded-md bg-yellow-100 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-800">
            <motion.div
              animate={{ rotate: currentMode === "polling" ? 360 : 0 }}
              transition={{
                duration: 2,
                repeat: currentMode === "polling" ? Infinity : 0,
              }}
            >
              {getModeIcon()}
            </motion.div>

            <span className="text-xs font-medium text-yellow-800 dark:text-yellow-200">
              {getModeText()}
            </span>

            {(currentMode === "manual" || currentMode === "offline") && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleManualRefresh}
                disabled={isRefreshing}
                className="h-6 w-6 p-0 hover:bg-yellow-200 dark:hover:bg-yellow-800"
              >
                {isRefreshing ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <RefreshCw className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
