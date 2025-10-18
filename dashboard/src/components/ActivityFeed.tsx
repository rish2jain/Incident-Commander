import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
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

function ActivityItem({
  action,
  index,
}: {
  action: AgentAction;
  index: number;
}) {
  const agentInfo = agentConfig[action.agent_type];
  const statusInfo = statusConfig[action.status];
  const AgentIcon = agentInfo.icon;
  const StatusIcon = statusInfo.icon;

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
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
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
                      className={`text-xs ${statusInfo.bgColor} ${statusInfo.color} border-current/20`}
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
                  {new Date(action.timestamp).toLocaleTimeString()}
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
}

export default function ActivityFeed({
  actions,
  maxItems = 15,
  showConfidence = true,
  className = "",
}: ActivityFeedProps) {
  const displayActions = actions.slice(0, maxItems);

  return (
    <Card className={`h-full ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/10 to-blue-600/10 border border-cyan-500/20 flex items-center justify-center">
            <MessageSquare className="w-4 h-4 text-cyan-500" />
          </div>
          Agent Activity Feed
          <Badge variant="outline" className="ml-auto">
            {actions.length} events
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[600px] px-6 pb-6">
          <AnimatePresence mode="popLayout">
            {displayActions.length > 0 ? (
              <div className="space-y-3">
                {displayActions.map((action, index) => (
                  <ActivityItem key={action.id} action={action} index={index} />
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
      </CardContent>
    </Card>
  );
}

// Demo component with sample data
export function ActivityFeedDemo() {
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

  // Simulate real-time updates
  React.useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() < 0.3) {
        const newAction: AgentAction = {
          id: Date.now().toString(),
          agent_type: [
            "detection",
            "diagnosis",
            "prediction",
            "resolution",
            "communication",
          ][Math.floor(Math.random() * 5)] as any,
          title: "Processing Incident",
          description:
            "Analyzing system metrics and determining appropriate response actions",
          timestamp: new Date().toISOString(),
          confidence: Math.random(),
          status: ["pending", "in_progress", "completed"][
            Math.floor(Math.random() * 3)
          ] as any,
          duration: Math.floor(Math.random() * 5000) + 500,
          details: {
            severity: "medium",
            affected_services: Math.floor(Math.random() * 5) + 1,
            estimated_impact: "$" + Math.floor(Math.random() * 10000),
          },
        };

        setActions((prev) => [newAction, ...prev].slice(0, 20));
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <ActivityFeed actions={actions} />
    </div>
  );
}
