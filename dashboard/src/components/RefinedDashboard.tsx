import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Database,
  Shield,
  MemoryStick,
  Plug,
  HardDrive,
  Play,
  Pause,
  RotateCcw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import IncidentCommanderHeader from "./DashboardHeader";
import ActivityFeed from "./ActivityFeed";
import MetricsPanel, { incidentCommanderMetrics } from "./MetricsPanel";
import IncidentStatusPanel from "./IncidentStatusPanel";

interface Incident {
  id: string;
  title: string;
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "active" | "resolving" | "resolved";
  created_at: string;
  affected_services: string[];
  metrics: Record<string, any>;
  estimated_cost: number;
  resolution_time?: number;
}

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

interface DashboardState {
  currentIncident: Incident | null;
  agentActions: AgentAction[];
  metrics: typeof incidentCommanderMetrics;
  systemStatus: "autonomous" | "monitoring" | "incident" | "maintenance";
  isConnected: boolean;
}

const scenarioConfigs = {
  database: {
    icon: Database,
    title: "Database Cascade",
    description: "Connection pool exhaustion scenario",
    color: "from-red-500 to-red-600",
    bgColor: "from-red-500/10 to-red-600/10",
    borderColor: "border-red-500/20",
  },
  ddos: {
    icon: Shield,
    title: "DDoS Attack",
    description: "Traffic spike mitigation test",
    color: "from-orange-500 to-orange-600",
    bgColor: "from-orange-500/10 to-orange-600/10",
    borderColor: "border-orange-500/20",
  },
  memory: {
    icon: MemoryStick,
    title: "Memory Leak",
    description: "OOM error recovery simulation",
    color: "from-purple-500 to-purple-600",
    bgColor: "from-purple-500/10 to-purple-600/10",
    borderColor: "border-purple-500/20",
  },
  api: {
    icon: Plug,
    title: "API Overload",
    description: "Rate limit activation scenario",
    color: "from-blue-500 to-blue-600",
    bgColor: "from-blue-500/10 to-blue-600/10",
    borderColor: "border-blue-500/20",
  },
  storage: {
    icon: HardDrive,
    title: "Storage Failure",
    description: "Failover and replication test",
    color: "from-green-500 to-green-600",
    bgColor: "from-green-500/10 to-green-600/10",
    borderColor: "border-green-500/20",
  },
};

function ScenarioButton({
  scenario,
  config,
  onTrigger,
  disabled,
}: {
  scenario: string;
  config: typeof scenarioConfigs.database;
  onTrigger: (scenario: string) => void;
  disabled: boolean;
}) {
  const Icon = config.icon;

  return (
    <motion.div
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
    >
      <Button
        variant="outline"
        className={`w-full h-auto p-4 justify-start gap-3 bg-gradient-to-br ${config.bgColor} border ${config.borderColor} hover:bg-gradient-to-br hover:${config.bgColor} disabled:opacity-50`}
        onClick={() => onTrigger(scenario)}
        disabled={disabled}
      >
        <div
          className={`p-2 rounded-lg bg-gradient-to-br ${config.color} text-white`}
        >
          <Icon className="w-4 h-4" />
        </div>
        <div className="text-left">
          <div className="font-semibold text-sm">{config.title}</div>
          <div className="text-xs text-muted-foreground">
            {config.description}
          </div>
        </div>
      </Button>
    </motion.div>
  );
}

function EnhancedIncidentPanel({ incident }: { incident: Incident | null }) {
  if (!incident) return null;

  // Convert incident data to match IncidentStatusPanel props
  const affectedServices = incident.affected_services.map((service) => ({
    name: service,
    status: "degraded" as const,
    impact: "Service disruption",
  }));

  return (
    <div className="col-span-full">
      <IncidentStatusPanel
        incidentId={incident.id}
        title={incident.title}
        severity={incident.severity as "critical" | "high" | "medium" | "low"}
        startTime={new Date(incident.created_at)}
        affectedServices={affectedServices}
        description={incident.description}
      />
    </div>
  );
}

export default function RefinedDashboard() {
  const [dashboardState, setDashboardState] = React.useState<DashboardState>({
    currentIncident: null,
    agentActions: [
      {
        id: "init",
        agent_type: "detection",
        title: "System Initialized",
        description:
          "Multi-agent system ready for autonomous incident response",
        timestamp: new Date().toISOString(),
        confidence: 1.0,
        status: "completed",
        duration: 1200,
        impact: "System Ready",
      },
    ],
    metrics: incidentCommanderMetrics,
    systemStatus: "autonomous",
    isConnected: true,
  });

  const [scenarioInProgress, setScenarioInProgress] = React.useState(false);

  // WebSocket connection
  React.useEffect(() => {
    // Try to connect to WebSocket, but don't fail if backend is not running
    const connectWebSocket = async () => {
      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//localhost:8000/ws`;

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log("✅ WebSocket connected to backend");
          setDashboardState((prev) => ({ ...prev, isConnected: true }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("📡 Received WebSocket message:", data);

            // Handle different message types
            switch (data.type) {
              case "incident_started":
                if (data.data?.incident) {
                  const incident = data.data.incident;
                  setDashboardState((prev) => ({
                    ...prev,
                    currentIncident: incident,
                    systemStatus: "incident",
                  }));
                }
                break;
              case "agent_action":
                if (data.data?.action) {
                  const action = data.data.action;
                  setDashboardState((prev) => ({
                    ...prev,
                    agentActions: [action, ...prev.agentActions.slice(0, 14)],
                  }));
                }
                break;
              case "incident_resolved":
                setDashboardState((prev) => ({
                  ...prev,
                  currentIncident: null,
                  systemStatus: "autonomous",
                }));
                break;
            }
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        ws.onclose = () => {
          console.log("❌ WebSocket disconnected");
          setDashboardState((prev) => ({ ...prev, isConnected: false }));
        };

        ws.onerror = (error) => {
          console.log(
            "⚠️ WebSocket connection failed (backend may not be running)"
          );
          setDashboardState((prev) => ({ ...prev, isConnected: false }));
        };

        return ws;
      } catch (error) {
        console.log("⚠️ WebSocket not available (backend may not be running)");
        setDashboardState((prev) => ({ ...prev, isConnected: false }));
        return null;
      }
    };

    connectWebSocket();

    // Simulate periodic metric updates
    const metricsInterval = setInterval(() => {
      setDashboardState((prev) => ({
        ...prev,
        metrics: prev.metrics.map((metric) => {
          if (Math.random() < 0.1 && typeof metric.value === "number") {
            const variation = Math.random() * 0.05 - 0.025; // ±2.5% variation
            const newValue = Math.max(
              0,
              Math.round(metric.value * (1 + variation))
            );
            return {
              ...metric,
              previousValue: metric.value,
              value: newValue,
            };
          }
          return metric;
        }),
      }));
    }, 5000);

    return () => clearInterval(metricsInterval);
  }, []);

  const triggerScenario = async (scenarioType: string) => {
    if (scenarioInProgress) return;

    setScenarioInProgress(true);

    try {
      // Create mock incident
      const incident: Incident = {
        id: Date.now().toString(),
        title: `${
          scenarioConfigs[scenarioType as keyof typeof scenarioConfigs].title
        } Detected`,
        description: `Autonomous system detected ${scenarioType} incident and initiating response`,
        severity: "high",
        status: "active",
        created_at: new Date().toISOString(),
        affected_services: ["web-api", "database", "cache"],
        metrics: {
          cpu_usage: "85%",
          memory_usage: "92%",
          error_rate: "12%",
          response_time: "2.3s",
        },
        estimated_cost: 15000,
      };

      // Update system status
      setDashboardState((prev) => ({
        ...prev,
        currentIncident: incident,
        systemStatus: "incident",
      }));

      // Add detection action
      const detectionAction: AgentAction = {
        id: `detection-${Date.now()}`,
        agent_type: "detection",
        title: "Incident Detected",
        description: `Critical ${scenarioType} incident detected through anomaly analysis`,
        timestamp: new Date().toISOString(),
        confidence: 0.95,
        status: "completed",
        duration: 850,
        details: {
          severity: incident.severity,
          affected_services: incident.affected_services.length,
          detection_method: "ML Anomaly Detection",
        },
      };

      setDashboardState((prev) => ({
        ...prev,
        agentActions: [detectionAction, ...prev.agentActions],
      }));

      // Simulate agent workflow
      const agentSequence = [
        {
          type: "diagnosis",
          title: "Root Cause Analysis",
          description: "Analyzing logs and traces to identify root cause",
          delay: 2000,
          duration: 1200,
        },
        {
          type: "prediction",
          title: "Impact Prediction",
          description: "Forecasting incident escalation and business impact",
          delay: 1000,
          duration: 800,
        },
        {
          type: "resolution",
          title: "Automated Resolution",
          description: "Executing automated remediation actions",
          delay: 1500,
          duration: 2000,
        },
        {
          type: "communication",
          title: "Stakeholder Notification",
          description: "Notifying relevant teams and updating status",
          delay: 500,
          duration: 300,
        },
      ];

      let totalDelay = 1000;

      for (const step of agentSequence) {
        setTimeout(() => {
          const action: AgentAction = {
            id: `${step.type}-${Date.now()}`,
            agent_type: step.type as any,
            title: step.title,
            description: step.description,
            timestamp: new Date().toISOString(),
            confidence: 0.85 + Math.random() * 0.1,
            status: "in_progress",
            duration: step.duration,
          };

          setDashboardState((prev) => ({
            ...prev,
            agentActions: [action, ...prev.agentActions],
          }));

          // Complete the action after duration
          setTimeout(() => {
            setDashboardState((prev) => ({
              ...prev,
              agentActions: prev.agentActions.map((a) =>
                a.id === action.id ? { ...a, status: "completed" as const } : a
              ),
            }));
          }, step.duration);
        }, totalDelay);

        totalDelay += step.delay + step.duration;
      }

      // Resolve incident
      setTimeout(() => {
        setDashboardState((prev) => ({
          ...prev,
          currentIncident: prev.currentIncident
            ? {
                ...prev.currentIncident,
                status: "resolved",
                resolution_time: totalDelay / 1000,
              }
            : null,
          systemStatus: "autonomous",
        }));

        // Hide incident after celebration
        setTimeout(() => {
          setDashboardState((prev) => ({
            ...prev,
            currentIncident: null,
          }));
          setScenarioInProgress(false);
        }, 3000);
      }, totalDelay + 1000);
    } catch (error) {
      console.error("Error triggering scenario:", error);
      setScenarioInProgress(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <IncidentCommanderHeader
        systemStatus={dashboardState.systemStatus}
        stats={{
          activeIncidents: dashboardState.currentIncident ? 1 : 0,
          resolvedToday: 12,
          mttrReduction: 95,
          agentsActive: 5,
        }}
        onTriggerScenario={triggerScenario}
      />

      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Activity Feed - Takes up 2 columns */}
            <div className="lg:col-span-2">
              <ActivityFeed
                actions={dashboardState.agentActions}
                maxItems={15}
              />
            </div>

            {/* Right Sidebar */}
            <div className="lg:col-span-2 space-y-6">
              {/* Scenario Controls */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20 flex items-center justify-center">
                      <Play className="w-4 h-4 text-purple-500" />
                    </div>
                    Demo Scenarios
                    {scenarioInProgress && (
                      <Badge variant="outline" className="ml-auto">
                        <Pause className="w-3 h-3 mr-1" />
                        Running
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {Object.entries(scenarioConfigs).map(([scenario, config]) => (
                    <ScenarioButton
                      key={scenario}
                      scenario={scenario}
                      config={config}
                      onTrigger={triggerScenario}
                      disabled={scenarioInProgress}
                    />
                  ))}
                </CardContent>
              </Card>

              {/* Metrics Panel */}
              <MetricsPanel
                metrics={dashboardState.metrics}
                title="Live System Metrics"
                animated={true}
              />
            </div>

            {/* Incident Panel - Full width when active */}
            <AnimatePresence>
              {dashboardState.currentIncident && (
                <EnhancedIncidentPanel
                  incident={dashboardState.currentIncident}
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
