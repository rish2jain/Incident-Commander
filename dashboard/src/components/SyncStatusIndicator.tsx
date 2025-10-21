import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Clock,
  Loader2,
  GitMerge,
} from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { useStateSync } from "../lib/hooks/useStateSync";

interface SyncStatusIndicatorProps {
  showProgress?: boolean;
  showDetails?: boolean;
  className?: string;
}

export function SyncStatusIndicator({
  showProgress = false,
  showDetails = false,
  className = "",
}: SyncStatusIndicatorProps) {
  const { syncState, performSync, isSyncing, hasConflicts, lastSyncTime } =
    useStateSync();

  const [isManualSyncing, setIsManualSyncing] = React.useState(false);

  const [syncError, setSyncError] = React.useState<string | null>(null);

  const handleManualSync = async () => {
    setIsManualSyncing(true);
    setSyncError(null);
    try {
      await performSync();
      // Clear syncError on successful sync
      setSyncError(null);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Sync failed";
      console.error("Manual sync failed:", error);
      setSyncError(errorMessage);
      // Optionally show a toast notification here
      // toast.error(`Sync failed: ${errorMessage}`);
    } finally {
      setIsManualSyncing(false);
    }
  };

  const getSyncIcon = () => {
    if (isSyncing || isManualSyncing) {
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    }

    if (hasConflicts) {
      return <GitMerge className="h-4 w-4 text-yellow-500" />;
    }

    if (syncState.lastError) {
      return <AlertTriangle className="h-4 w-4 text-red-500" />;
    }

    if (lastSyncTime) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }

    return <Clock className="h-4 w-4 text-gray-500" />;
  };

  const getSyncStatus = () => {
    if (isSyncing || isManualSyncing) {
      return "Syncing...";
    }

    if (hasConflicts) {
      return `${syncState.conflictsDetected} conflicts`;
    }

    if (syncState.lastError) {
      return "Sync failed";
    }

    if (lastSyncTime) {
      const timeDiff = Date.now() - lastSyncTime.getTime();
      const minutes = Math.floor(timeDiff / 60000);

      if (minutes < 1) return "Just synced";
      if (minutes < 60) return `${minutes}m ago`;

      const hours = Math.floor(minutes / 60);
      return `${hours}h ago`;
    }

    return "Not synced";
  };

  const getStatusColor = () => {
    if (isSyncing || isManualSyncing) return "text-blue-600";
    if (hasConflicts) return "text-yellow-600";
    if (syncState.lastError) return "text-red-600";
    if (lastSyncTime) return "text-green-600";
    return "text-gray-600";
  };

  const formatLastSync = () => {
    if (!lastSyncTime) return "Never";
    return lastSyncTime.toLocaleTimeString();
  };

  return (
    <TooltipProvider>
      <div className={`flex items-center gap-2 ${className}`}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-2 px-2 py-1 rounded-md bg-background/50 border border-border/50">
              <motion.div
                animate={{
                  scale: isSyncing ? [1, 1.1, 1] : 1,
                  rotate: isSyncing ? 360 : 0,
                }}
                transition={{
                  scale: { duration: 1, repeat: isSyncing ? Infinity : 0 },
                  rotate: {
                    duration: 2,
                    repeat: isSyncing ? Infinity : 0,
                    ease: "linear",
                  },
                }}
              >
                {getSyncIcon()}
              </motion.div>

              {showDetails && (
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${getStatusColor()}`}>
                    {getSyncStatus()}
                  </span>

                  {syncState.pendingChanges > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {syncState.pendingChanges} pending
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-xs">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium">Sync Status</span>
                <Badge
                  variant={
                    isSyncing
                      ? "default"
                      : hasConflicts
                      ? "secondary"
                      : syncState.lastError
                      ? "destructive"
                      : "outline"
                  }
                  className="text-xs"
                >
                  {getSyncStatus()}
                </Badge>
              </div>

              <div className="flex justify-between text-xs">
                <span>Last sync:</span>
                <span>{formatLastSync()}</span>
              </div>

              {syncState.pendingChanges > 0 && (
                <div className="flex justify-between text-xs">
                  <span>Pending changes:</span>
                  <span className="text-yellow-500">
                    {syncState.pendingChanges}
                  </span>
                </div>
              )}

              {hasConflicts && (
                <div className="flex justify-between text-xs">
                  <span>Conflicts:</span>
                  <span className="text-yellow-500">
                    {syncState.conflictsDetected}
                  </span>
                </div>
              )}

              {(syncError || syncState.lastError) && (
                <div className="text-xs text-red-600">
                  Error: {syncError || syncState.lastError}
                </div>
              )}

              {syncState.syncAttempts > 0 && (
                <div className="flex justify-between text-xs">
                  <span>Attempts:</span>
                  <span>{syncState.syncAttempts}/5</span>
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>

        {/* Progress bar for syncing */}
        {showProgress && (isSyncing || isManualSyncing) && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 60 }}
              exit={{ opacity: 0, width: 0 }}
              className="flex items-center"
            >
              <Progress value={syncState.syncProgress} className="h-1 w-full" />
            </motion.div>
          </AnimatePresence>
        )}

        {/* Manual sync button */}
        {!isSyncing && !isManualSyncing && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleManualSync}
            className="h-7 px-2 text-xs"
          >
            <RefreshCw className="h-3 w-3" />
            <span className="ml-1 hidden sm:inline">Sync</span>
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}

// Compact version for header
export function CompactSyncStatus({ className = "" }: { className?: string }) {
  return (
    <SyncStatusIndicator
      showProgress={false}
      showDetails={false}
      className={className}
    />
  );
}

// Detailed version with progress
export function DetailedSyncStatus({ className = "" }: { className?: string }) {
  return (
    <SyncStatusIndicator
      showProgress={true}
      showDetails={true}
      className={className}
    />
  );
}
