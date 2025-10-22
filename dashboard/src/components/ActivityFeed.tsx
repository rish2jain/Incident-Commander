import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  useClientSideTimestamp,
  formatTimeSafe,
} from "@/hooks/useClientSideTimestamp";
import {
  Search,
  Stethoscope,
  Sparkles,
  Wrench,
  MessageSquare,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Loader2,
  TrendingUp,
  Zap,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { FloatingScrollIndicator } from "./ui/scroll-indicator";
import { useAutoScroll } from "../lib/hooks/useAutoScroll";
import { cn } from "../lib/utils";

interface AgentAction {
  id: string;
  agent_type:
    | "detection"
    | "diagnosis"
    | "prediction"
    | "resolution"
    | "communication";
  title: string;
  description: string;
  timestamp: string;
  confidence?: number;
  status: "pending" | "in_progress" | "completed" | "failed";
  details?: Record<string, any>;
  duration?: number;
  impact?: string;
}

interface ActivityFeedProps {
  actions: AgentAction[];
  maxItems?: number;
  showConfidence?: boolean;
  className?: string;
  autoScrollEnabled?: boolean;
  onActionClick?: (action: AgentAction) => void;
}

const agentConfig = {
  detection: {
    icon: Search,
    color: "from-red-500 to-red-600",
    bgColor: "from-red-500/10 to-red-600/10",
    borderColor: "border-red-500/20",
    textColor: "text-red-500",
    name: "Detection",
  },
  diagnosis: {
    icon: Stethoscope,
    color: "from-teal-500 to-teal-600",
    bgColor: "from-teal-500/10 to-teal-600/10",
    borderColor: "border-teal-500/20",
    textColor: "text-teal-500",
    name: "Diagnosis",
  },
  prediction: {
    icon: Sparkles,
    color: "from-blue-500 to-blue-600",
    bgColor: "from-blue-500/10 to-blue-600/10",
    borderColor: "border-blue-500/20",
    textColor: "text-blue-500",
    name: "Prediction",
  },
  resolution: {
    icon: Wrench,
    color: "from-amber-500 to-amber-600",
    bgColor: "from-amber-500/10 to-amber-600/10",
    borderColor: "border-amber-500/20",
    textColor: "text-amber-500",
    name: "Resolution",
  },
  communication: {
    icon: MessageSquare,
    color: "from-purple-500 to-purple-600",
    bgColor: "from-purple-500/10 to-purple-600/10",
    borderColor: "border-purple-500/20",
    textColor: "text-purple-500",
    name: "Communication",
  },
};

const statusConfig: Record<
  string,
  {
    icon: React.ElementType;
    color: string;
    bgColor: string;
    label: string;
    animate?: boolean;
  }
> = {
  pending: {
    icon: Clock,
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
    label: "Pending",
  },
  in_progress: {
    icon: Loader2,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    label: "In Progress",
    animate: true,
  },
  completed: {
    icon: CheckCircle,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    label: "Completed",
  },
  failed: {
    icon: XCircle,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    label: "Failed",
  },
};

function ConfidenceBar({ confidence }: { confidence: number }) {
  return (
    <div className="w-full h-1.5 bg-muted/50 rounded-full overflow-hidden mt-2">
      <motion.div
        className="h-full bg-gradient-to-r from-red-500 via-amber-500 to-green-500 rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${confidence * 100}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </div>
  );
}

const ActivityItem = React.memo(function ActivityItem({
  action,
  index,
  onClick,
}: {
  action: AgentAction;
  index: number;
  onClick?: (action: AgentAction) => void;
}) {
  const agentInfo = agentConfig[action.agent_type];
  const statusInfo = statusConfig[action.status];
  const AgentIcon = agentInfo.icon;
  const StatusIcon = statusInfo.icon;

  // Memoize click handler to prevent unnecessary re-renders
  const handleClick = React.useCallback(() => {
    onClick?.(action);
  }, [onClick, action]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{
        duration: 0.4,
        delay: index * 0.05,
        type: "spring",
        stiffness: 400,
        damping: 25,
      }}
      className="group relative"
    >
      <Card
        className={cn(
          "border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5",
          onClick && "cursor-pointer"
        )}
        onClick={handleClick}
      >
        <CardContent className="p-4">
          <div className="flex gap-3">
            {/* Agent Avatar */}
            <motion.div
              className={`flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br ${agentInfo.bgColor} border ${agentInfo.borderColor} flex items-center justify-center`}
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              <AgentIcon className={`w-5 h-5 ${agentInfo.textColor}`} />
            </motion.div>

            <div className="flex-1 min-w-0">
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-sm text-foreground truncate">
                      {agentInfo.name} Agent
                    </h4>
                    <Badge
                      variant="outline"
                      className={cn(
                        `text-xs ${statusInfo.bgColor} ${statusInfo.color} border-current/20`
                      )}
                    >
                      <StatusIcon
                        className={`w-3 h-3 mr-1 ${
                          statusInfo.animate ? "animate-spin" : ""
                        }`}
                      />
                      {statusInfo.label}
                    </Badge>
                  </div>
                  <h5 className="font-medium text-sm text-foreground/90 mb-1">
                    {action.title}
                  </h5>
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  {formatTimeSafe(action.timestamp, isClient)}
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-muted-foreground leading-relaxed mb-3">
                {action.description}
              </p>

              {/* Details */}
              {action.details && (
                <div className="bg-muted/30 rounded-lg p-3 mb-3 border border-border/30">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(action.details).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground capitalize">
                          {key.replace(/_/g, " ")}:
                        </span>
                        <span className="font-medium text-foreground">
                          {typeof value === "object"
                            ? JSON.stringify(value)
                            : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {action.duration && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Zap className="w-3 h-3" />
                      {action.duration}ms
                    </div>
                  )}
                  {action.impact && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <TrendingUp className="w-3 h-3" />
                      {action.impact}
                    </div>
                  )}
                </div>

                {action.confidence !== undefined && (
                  <div className="text-xs text-muted-foreground">
                    Confidence: {Math.round(action.confidence * 100)}%
                  </div>
                )}
              </div>

              {/* Confidence Bar */}
              {action.confidence !== undefined && (
                <ConfidenceBar confidence={action.confidence} />
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
});

export default function ActivityFeed({
  actions,
  maxItems = 15,
  showConfidence = true,
  className = "",
  autoScrollEnabled = true,
  onActionClick,
}: ActivityFeedProps) {
  const isClient = useClientSideTimestamp();

  // Memoize display actions to prevent unnecessary re-renders
  const displayActions = React.useMemo(
    () => actions.slice(0, maxItems),
    [actions, maxItems]
  );

  // Track new messages for scroll indicator
  const [previousActionCount, setPreviousActionCount] = React.useState(
    actions.length
  );
  const [newMessageCount, setNewMessageCount] = React.useState(0);

  // Track resume countdown for visual feedback
  const [resumeCountdown, setResumeCountdown] = React.useState<number | null>(
    null
  );

  // Performance optimization: detect high-frequency updates
  const isHighFrequency = React.useMemo(() => {
    const now = Date.now();
    const recentActions = actions.filter(
      (action) => now - new Date(action.timestamp).getTime() < 5000 // Last 5 seconds
    );
    return recentActions.length > 10; // More than 10 messages in 5 seconds
  }, [actions]);

  // Auto-scroll functionality with performance optimizations
  const {
    scrollRef,
    scrollState,
    isNearBottom,
    isPaused,
    scrollToBottom,
    pauseAutoScroll,
    resumeAutoScroll,
    shouldShowScrollToBottom,
  } = useAutoScroll({
    enabled: autoScrollEnabled,
    dependencies: [actions.length],
    threshold: 100,
    resumeDelay: 1500, // 1.5 seconds delay before resuming after user scroll
    smoothScroll: !isHighFrequency, // Disable smooth scroll during high frequency updates
    maxScrollSpeed: isHighFrequency ? 10 : 2, // Faster scrolling for high frequency
    debounceDelay: isHighFrequency ? 50 : 100, // Lower debounce for high frequency
  });

  // Track new messages with throttling for performance
  const batchTimerRef = React.useRef<number | null>(null);

  React.useEffect(() => {
    if (actions.length > previousActionCount) {
      const newMessages = actions.length - previousActionCount;

      // Clear any existing timer before scheduling a new one
      if (batchTimerRef.current !== null) {
        clearTimeout(batchTimerRef.current);
        batchTimerRef.current = null;
      }

      // Throttle updates during high-frequency scenarios
      if (isHighFrequency) {
        // Batch updates every 500ms during high frequency
        batchTimerRef.current = window.setTimeout(() => {
          setNewMessageCount((prev) => prev + newMessages);
          setPreviousActionCount(actions.length);
          batchTimerRef.current = null;
        }, 500);
      } else {
        setNewMessageCount((prev) => prev + newMessages);
        setPreviousActionCount(actions.length);
      }
    } else if (!isHighFrequency) {
      setPreviousActionCount(actions.length);
    }

    // Cleanup function to clear pending timer
    return () => {
      if (batchTimerRef.current !== null) {
        clearTimeout(batchTimerRef.current);
        batchTimerRef.current = null;
      }
    };
  }, [actions.length, previousActionCount, isHighFrequency]);

  // Clear new message count when user scrolls to bottom
  React.useEffect(() => {
    if (isNearBottom) {
      setNewMessageCount(0);
    }
  }, [isNearBottom]);

  // Handle resume countdown when paused
  React.useEffect(() => {
    let countdownInterval: NodeJS.Timeout | null = null;

    if (isPaused && scrollState.isUserScrolling) {
      // Start countdown from resume delay (1.5 seconds)
      setResumeCountdown(1.5);

      countdownInterval = setInterval(() => {
        setResumeCountdown((prev) => {
          if (prev === null || prev <= 0.1) {
            return null;
          }
          return prev - 0.1;
        });
      }, 100);
    } else {
      setResumeCountdown(null);
    }

    return () => {
      if (countdownInterval) {
        clearInterval(countdownInterval);
      }
    };
  }, [isPaused, scrollState.isUserScrolling]);

  // Memoize callback handlers for performance
  const handleScrollToBottom = React.useCallback(() => {
    scrollToBottom();
    setNewMessageCount(0);
  }, [scrollToBottom]);

  const handleActionClick = React.useCallback(
    (action: AgentAction) => {
      onActionClick?.(action);
    },
    [onActionClick]
  );

  return (
    <Card className={cn("h-full relative", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/10 to-blue-600/10 border border-cyan-500/20 flex items-center justify-center">
            <MessageSquare className="w-4 h-4 text-cyan-500" />
          </div>
          Agent Activity Feed
          <Badge variant="outline" className={cn("ml-auto")}>
            {actions.length} events
          </Badge>
          {isPaused && (
            <Badge
              variant="outline"
              className={cn(
                "bg-amber-500/10 text-amber-500 border-amber-500/20 animate-pulse"
              )}
            >
              Auto-scroll Paused
              {resumeCountdown && resumeCountdown > 0 && (
                <span className="ml-1 text-xs opacity-75">
                  ({Math.ceil(resumeCountdown)}s)
                </span>
              )}
            </Badge>
          )}
          {isHighFrequency && (
            <Badge
              variant="outline"
              className={cn("bg-blue-500/10 text-blue-500 border-blue-500/20")}
            >
              High Performance Mode
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 relative">
        <ScrollArea
          className="h-[600px] px-6 pb-6"
          ref={scrollRef as React.RefObject<HTMLDivElement>}
        >
          <AnimatePresence mode="popLayout">
            {displayActions.length > 0 ? (
              <div className="space-y-3">
                {displayActions.map((action, index) => (
                  <ActivityItem
                    key={action.id}
                    action={action}
                    index={index}
                    onClick={handleActionClick}
                  />
                ))}
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-12 text-center"
              >
                <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
                  <MessageSquare className="w-8 h-8 text-muted-foreground" />
                </div>
                <h3 className="font-medium text-foreground mb-2">
                  No Activity Yet
                </h3>
                <p className="text-sm text-muted-foreground max-w-sm">
                  Agent activities will appear here as the system processes
                  incidents and performs autonomous actions.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </ScrollArea>

        {/* Floating Scroll Indicator with Resume Functionality */}
        <FloatingScrollIndicator
          isVisible={shouldShowScrollToBottom}
          isPaused={isPaused}
          isNearBottom={isNearBottom}
          messageCount={newMessageCount}
          onScrollToBottom={handleScrollToBottom}
          hasNewMessages={newMessageCount > 0}
        />

        {/* Resume Auto-scroll Button when paused and not near bottom */}
        {isPaused && !isNearBottom && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute top-4 right-4 z-10"
          >
            <div className="bg-background/95 backdrop-blur-sm border border-border/50 rounded-lg p-2 shadow-lg">
              <div className="flex items-center gap-2 text-sm">
                <div className="flex items-center gap-1 text-amber-500">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    <Clock className="w-3 h-3" />
                  </motion.div>
                  <span className="text-xs">
                    Auto-scroll paused
                    {resumeCountdown && resumeCountdown > 0 && (
                      <span className="ml-1 text-muted-foreground">
                        (resuming in {resumeCountdown.toFixed(1)}s)
                      </span>
                    )}
                  </span>
                </div>
                <button
                  onClick={resumeAutoScroll}
                  className="text-xs px-2 py-1 bg-primary/90 hover:bg-primary text-primary-foreground rounded transition-colors"
                >
                  Resume
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}

// Demo component with sample data and auto-scroll functionality
export function ActivityFeedDemo() {
  const isClient = useClientSideTimestamp();
  const [actions, setActions] = React.useState<AgentAction[]>([
    {
      id: "1",
      agent_type: "detection",
      title: "System Initialized",
      description: "Multi-agent system ready for autonomous incident response",
      timestamp: new Date().toISOString(),
      confidence: 1.0,
      status: "completed",
      duration: 1200,
      impact: "System Ready",
    },
  ]);

  // Simulate real-time updates with higher frequency for demo
  React.useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() < 0.4) {
        // 40% chance of new message
        const newAction: AgentAction = {
          id: Date.now().toString(),
          agent_type: [
            "detection",
            "diagnosis",
            "prediction",
            "resolution",
            "communication",
          ][Math.floor(Math.random() * 5)] as any,
          title: [
            "Processing Incident",
            "Analyzing Metrics",
            "Executing Resolution",
            "Updating Status",
            "Monitoring Recovery",
          ][Math.floor(Math.random() * 5)],
          description: [
            "Analyzing system metrics and determining appropriate response actions",
            "Processing log data to identify root cause patterns",
            "Executing automated remediation procedures",
            "Coordinating with other agents for consensus",
            "Monitoring system recovery and validation",
          ][Math.floor(Math.random() * 5)],
          timestamp: new Date().toISOString(),
          confidence: Math.random(),
          status: ["pending", "in_progress", "completed", "failed"][
            Math.floor(Math.random() * 4)
          ] as unknown,
          duration: Math.floor(Math.random() * 5000) + 500,
          details: {
            severity: ["low", "medium", "high"][Math.floor(Math.random() * 3)],
            affected_services: Math.floor(Math.random() * 5) + 1,
            estimated_impact: "$" + Math.floor(Math.random() * 10000),
          },
        };

        setActions((prev) => [newAction, ...prev].slice(0, 50)); // Keep last 50 messages
      }
    }, 2000); // Check every 2 seconds

    return () => clearInterval(interval);
  }, []);

  const handleActionClick = (action: AgentAction) => {
    console.log("Action clicked:", action);
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <ActivityFeed
        actions={actions}
        autoScrollEnabled={true}
        onActionClick={handleActionClick}
      />
    </div>
  );
}
