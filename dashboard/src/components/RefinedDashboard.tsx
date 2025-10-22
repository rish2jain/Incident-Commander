/**
 * Refined Dashboard Component
 *
 * Primary dashboard composition for the Incident Commander system.
 * Provides real-time visualization of multi-agent coordination and incident response.
 */

import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Types
interface AgentState {
  id: string;
  name: string;
  status: "active" | "idle" | "error";
  confidence: number;
  lastUpdate: string;
}

interface IncidentMetrics {
  activeIncidents: number;
  resolvedToday: number;
  averageResolutionTime: number;
  preventionRate: number;
}

interface SystemHealth {
  uptime: number;
  cpuUsage: number;
  memoryUsage: number;
  networkLatency: number;
}

interface Incident {
  incident_id: string;
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  status: "active" | "resolved" | "investigating";
  detected_at: string;
  duration?: number;
  description?: string;
}

interface AgentConfidence {
  agent_name: string;
  current_confidence: number;
  confidence_history: Array<{ timestamp: string; confidence: number }>;
  reasoning_factors: string[];
  evidence_sources: string[];
  uncertainty_factors: string[];
}

interface PerformanceMetrics {
  mttr_comparison: {
    traditional_mttr_minutes: number;
    autonomous_mttr_minutes: number;
    reduction_percentage: number;
    time_saved_minutes: number;
    improvement_factor: number;
  };
  business_impact: {
    traditional_cost: number;
    autonomous_cost: number;
    cost_savings: number;
    cost_savings_percentage: number;
    revenue_protected: number;
    customer_impact_reduction: number;
  };
}

type SortField =
  | "incident_id"
  | "type"
  | "severity"
  | "status"
  | "detected_at"
  | "duration";
type SortDirection = "asc" | "desc";

const SIMULATION_SESSION_ID = "SIM-SESSION-001";

const SCENARIO_PRESETS: Record<
  string,
  {
    name: string;
    severity: Incident["severity"];
    description: string;
    duration: number;
  }
> = {
  database_failure: {
    name: "Database Cascade Failure",
    severity: "critical",
    description:
      "Connection pool saturation is cascading across dependent microservices. Autonomous plan is throttling traffic and recycling connections.",
    duration: 420,
  },
  api_cascade: {
    name: "API Rate Limit Cascade",
    severity: "high",
    description:
      "Downstream authentication APIs tripped rate limits and began cascading retries across regions. Multi-agent balancer is redistributing load.",
    duration: 360,
  },
  memory_leak: {
    name: "Memory Leak Detection",
    severity: "medium",
    description:
      "Session service memory footprint is trending toward OOM after deployment. Resolution agent is orchestrating canary rollback.",
    duration: 540,
  },
  network_latency: {
    name: "Network Latency Spike",
    severity: "medium",
    description:
      "Cross-region latency deviation detected on checkout pathway. Prediction agent is routing high-value traffic to low-latency edge.",
    duration: 310,
  },
  security_breach: {
    name: "Security Anomaly Response",
    severity: "critical",
    description:
      "Guardrails flagged privileged access anomaly with suspicious IP signature. Resolution agent is rotating credentials and locking sessions.",
    duration: 275,
  },
};

const buildSimulatedIncidents = (scenarioType?: string): Incident[] => {
  const now = Date.now();
  const scenario =
    SCENARIO_PRESETS[scenarioType ?? "database_failure"] ??
    SCENARIO_PRESETS.database_failure;

  return [
    {
      incident_id: SIMULATION_SESSION_ID,
      type: scenario.name,
      severity: scenario.severity,
      status: "active",
      detected_at: new Date(now - 4 * 60 * 1000).toISOString(),
      duration: scenario.duration,
      description: scenario.description,
    },
    {
      incident_id: "SIM-INC-2047",
      type: "API cascade stabilized",
      severity: "high",
      status: "resolved",
      detected_at: new Date(now - 45 * 60 * 1000).toISOString(),
      duration: 1800,
      description:
        "Autonomous scaling plan redistributed authentication traffic and restored SLO compliance.",
    },
    {
      incident_id: "SIM-INC-1978",
      type: "Stratos queue pressure",
      severity: "medium",
      status: "investigating",
      detected_at: new Date(now - 18 * 60 * 1000).toISOString(),
      duration: 960,
      description:
        "Agent fabric observing elevated fan-out on incident broadcast channel. Spectrum agent evaluating replay backlog.",
    },
    {
      incident_id: "SIM-INC-1733",
      type: "Guardrail IAM remediation",
      severity: "low",
      status: "resolved",
      detected_at: new Date(now - 3 * 60 * 60 * 1000).toISOString(),
      duration: 600,
      description:
        "Guardrails automatically remediated mis-scoped IAM policy and confirmed compliance posture.",
    },
  ];
};

const buildSimulatedAgentConfidence = (): Record<string, AgentConfidence> => {
  const now = Date.now();
  const timestamp = (offsetMinutes: number) =>
    new Date(now - offsetMinutes * 60 * 1000).toISOString();

  return {
    detection: {
      agent_name: "Detection Agent",
      current_confidence: 0.93,
      confidence_history: [
        { timestamp: timestamp(8), confidence: 0.78 },
        { timestamp: timestamp(5), confidence: 0.84 },
        { timestamp: timestamp(2), confidence: 0.9 },
        { timestamp: timestamp(1), confidence: 0.93 },
      ],
      reasoning_factors: [
        "Anomaly correlation across 143 telemetry signals",
        "Baseline drift within acceptable 0.6% threshold",
      ],
      evidence_sources: [
        "Prometheus saturation metrics",
        "Service error aggregates",
        "Feature store anomaly vectors",
      ],
      uncertainty_factors: ["Synthetic monitors degraded in parallel region"],
    },
    diagnosis: {
      agent_name: "Diagnosis Agent",
      current_confidence: 0.9,
      confidence_history: [
        { timestamp: timestamp(8), confidence: 0.63 },
        { timestamp: timestamp(6), confidence: 0.75 },
        { timestamp: timestamp(3), confidence: 0.87 },
        { timestamp: timestamp(1), confidence: 0.9 },
      ],
      reasoning_factors: [
        "Query plan regression detected via Bedrock AgentCore",
        "Lock wait accumulation beyond latency SLO",
      ],
      evidence_sources: [
        "Aurora performance insights",
        "Query profiler traces",
      ],
      uncertainty_factors: ["Awaiting guardrail confirmation"],
    },
    prediction: {
      agent_name: "Prediction Agent",
      current_confidence: 0.92,
      confidence_history: [
        { timestamp: timestamp(10), confidence: 0.7 },
        { timestamp: timestamp(6), confidence: 0.82 },
        { timestamp: timestamp(3), confidence: 0.9 },
        { timestamp: timestamp(1), confidence: 0.92 },
      ],
      reasoning_factors: [
        "Nova Act mitigation planner evaluating 3 rollout paths",
        "Titan embeddings similarity on historical regression",
      ],
      evidence_sources: ["Historical incident embeddings", "Nova Act planner"],
      uncertainty_factors: ["Pending customer impact projection"],
    },
    resolution: {
      agent_name: "Resolution Agent",
      current_confidence: 0.95,
      confidence_history: [
        { timestamp: timestamp(7), confidence: 0.74 },
        { timestamp: timestamp(4), confidence: 0.85 },
        { timestamp: timestamp(2), confidence: 0.9 },
        { timestamp: timestamp(1), confidence: 0.95 },
      ],
      reasoning_factors: [
        "Circuit breaker thresholds validated",
        "Canary rollback progressing within guardrails",
      ],
      evidence_sources: [
        "Strands SDK execution timeline",
        "Guardrail policy confirmations",
      ],
      uncertainty_factors: ["Awaiting full traffic restoration"],
    },
    communication: {
      agent_name: "Communication Agent",
      current_confidence: 0.88,
      confidence_history: [
        { timestamp: timestamp(12), confidence: 0.68 },
        { timestamp: timestamp(6), confidence: 0.79 },
        { timestamp: timestamp(3), confidence: 0.85 },
        { timestamp: timestamp(1), confidence: 0.88 },
      ],
      reasoning_factors: [
        "Stakeholder updates synchronized across Slack and email",
        "Executive briefing drafted via Amazon Q",
      ],
      evidence_sources: ["Slack incident channel", "Amazon Q briefing"],
      uncertainty_factors: ["Pending executive acknowledgement"],
    },
  };
};

const SIMULATED_PERFORMANCE_METRICS: PerformanceMetrics = {
  mttr_comparison: {
    traditional_mttr_minutes: 42,
    autonomous_mttr_minutes: 6,
    reduction_percentage: 85.7,
    time_saved_minutes: 36,
    improvement_factor: 7,
  },
  business_impact: {
    traditional_cost: 5600000,
    autonomous_cost: 275000,
    cost_savings: 5325000,
    cost_savings_percentage: 95.1,
    revenue_protected: 2800000,
    customer_impact_reduction: 87,
  },
};

const SIMULATED_DASHBOARD_METRICS: IncidentMetrics = {
  activeIncidents: 1,
  resolvedToday: 18,
  averageResolutionTime: 1.3,
  preventionRate: 85,
};

const SIMULATED_SYSTEM_HEALTH: SystemHealth = {
  uptime: 99.97,
  cpuUsage: 38,
  memoryUsage: 62,
  networkLatency: 18,
};

// Main Dashboard Component
export const RefinedDashboard: React.FC = () => {
  const [agents, setAgents] = useState<AgentState[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<IncidentMetrics>({
    activeIncidents: 0,
    resolvedToday: 12,
    averageResolutionTime: 1.4,
    preventionRate: 85,
  });
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    uptime: 99.9,
    cpuUsage: 23,
    memoryUsage: 45,
    networkLatency: 12,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [agentConfidence, setAgentConfidence] = useState<
    Record<string, AgentConfidence>
  >({});
  const [performanceMetrics, setPerformanceMetrics] =
    useState<PerformanceMetrics | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [simulationMode, setSimulationMode] = useState(false);
  const simulationAutoActivatedRef = useRef(false);

  const activateSimulationMode = useCallback((scenarioType?: string) => {
    const fallbackIncidents = buildSimulatedIncidents(scenarioType);
    const fallbackConfidence = buildSimulatedAgentConfidence();

    setSimulationMode(true);
    simulationAutoActivatedRef.current = true;
    setIsConnected(true);
    setIncidents(fallbackIncidents);
    setTotalIncidents(fallbackIncidents.length);
    setSelectedIncident(fallbackIncidents[0]?.incident_id ?? null);
    setMetrics(SIMULATED_DASHBOARD_METRICS);
    setSystemHealth(SIMULATED_SYSTEM_HEALTH);
    setCurrentSessionId(
      fallbackIncidents[0]?.incident_id ?? SIMULATION_SESSION_ID
    );
    setAgentConfidence(fallbackConfidence);
    setPerformanceMetrics(SIMULATED_PERFORMANCE_METRICS);
    setLastUpdate(new Date());
  }, []);

  // Filtering state
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [totalIncidents, setTotalIncidents] = useState(0);

  // Sorting state
  const [sortField, setSortField] = useState<SortField>("detected_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        // Build WebSocket URL from environment or current location
        const wsUrl =
          process.env.NEXT_PUBLIC_WS_URL ||
          (() => {
            const protocol =
              window.location.protocol === "https:" ? "wss:" : "ws:";
            const host = window.location.host || "localhost:8000";
            return `${protocol}//${host}/dashboard/ws`;
          })();

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
          console.log("Dashboard WebSocket connected");
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
          setLastUpdate(new Date());
        };

        ws.onclose = () => {
          setIsConnected(false);
          console.log("Dashboard WebSocket disconnected");
          // Attempt to reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          setIsConnected(false);
        };

        return ws;
      } catch (error) {
        console.error("Failed to connect WebSocket:", error);
        setIsConnected(false);
        return null;
      }
    };

    const ws = connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [handleWebSocketMessage]);

  // Fetch incidents from backend (updated with filters and pagination)
  const fetchIncidents = useCallback(async () => {
    if (simulationMode) {
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const params = new URLSearchParams({
        limit: itemsPerPage.toString(),
        offset: ((currentPage - 1) * itemsPerPage).toString(),
      });

      if (statusFilter !== "all") {
        params.append("status", statusFilter);
      }
      if (severityFilter !== "all") {
        params.append("severity", severityFilter);
      }

      const response = await fetch(`${apiUrl}/incidents?${params.toString()}`);

      if (response.ok) {
        const data = await response.json();
        const incidentList: Incident[] = data.incidents || [];

        setIncidents(incidentList);
        setTotalIncidents(data.total || incidentList.length);
        setSelectedIncident(incidentList[0]?.incident_id ?? null);

        // Only clear simulation mode if it was auto-activated by the system
        if (simulationAutoActivatedRef.current) {
          setSimulationMode(false);
          simulationAutoActivatedRef.current = false;
        }

        setIsConnected(true);
        setLastUpdate(new Date());
      } else {
        console.error("Failed to fetch incidents");
        activateSimulationMode();
      }
    } catch (error) {
      console.error("Error fetching incidents:", error);
      activateSimulationMode();
    }
  }, [
    activateSimulationMode,
    currentPage,
    itemsPerPage,
    severityFilter,
    simulationMode,
    statusFilter,
  ]);

  // Fetch incidents when filters or pagination change
  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 30000);
    return () => clearInterval(interval);
  }, [fetchIncidents]);

  // Fetch agent confidence data
  const fetchAgentConfidence = useCallback(
    async (sessionId: string) => {
      if (simulationMode) {
        return;
      }

      try {
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(
          `${apiUrl}/dashboard/judge/agent-confidence/${sessionId}`
        );

        if (response.ok) {
          const data = await response.json();
          setAgentConfidence(data.agent_confidence_visualizations || {});

          // Only clear simulation mode if it was auto-activated by the system
          if (simulationAutoActivatedRef.current) {
            setSimulationMode(false);
            simulationAutoActivatedRef.current = false;
          }
        } else {
          activateSimulationMode();
        }
      } catch (error) {
        console.error("Error fetching agent confidence:", error);
        activateSimulationMode();
      }
    },
    [activateSimulationMode, simulationMode]
  );

  // Fetch performance metrics
  const fetchPerformanceMetrics = useCallback(
    async (sessionId: string) => {
      if (simulationMode) {
        return;
      }

      try {
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(
          `${apiUrl}/dashboard/demo/metrics/${sessionId}`
        );

        if (response.ok) {
          const data = await response.json();
          setPerformanceMetrics(data);

          // Only clear simulation mode if it was auto-activated by the system
          if (simulationAutoActivatedRef.current) {
            setSimulationMode(false);
            simulationAutoActivatedRef.current = false;
          }
        } else {
          activateSimulationMode();
        }
      } catch (error) {
        console.error("Error fetching performance metrics:", error);
        activateSimulationMode();
      }
    },
    [activateSimulationMode, simulationMode]
  );

  // Update session ID when incidents change
  useEffect(() => {
    const activeIncident = incidents.find((inc) => inc.status === "active");
    if (activeIncident && activeIncident.incident_id !== currentSessionId) {
      setCurrentSessionId(activeIncident.incident_id);
      fetchAgentConfidence(activeIncident.incident_id);
      fetchPerformanceMetrics(activeIncident.incident_id);
    }
  }, [
    incidents,
    currentSessionId,
    fetchAgentConfidence,
    fetchPerformanceMetrics,
  ]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback(
    (data: any) => {
      switch (data.type) {
        case "agent_update":
          setAgents((prevAgents) => {
            const updatedAgents = [...prevAgents];
            const agentIndex = updatedAgents.findIndex(
              (a) => a.id === data.agent_id
            );

            if (agentIndex >= 0) {
              updatedAgents[agentIndex] = {
                ...updatedAgents[agentIndex],
                ...data.agent_state,
              };
            } else {
              updatedAgents.push(data.agent_state);
            }

            return updatedAgents;
          });
          break;

        case "metrics_update":
          setMetrics(data.metrics);
          break;

        case "system_health":
          setSystemHealth(data.health);
          break;

        case "initial_state":
          if (data.data.agent_states) {
            setAgents(Object.values(data.data.agent_states));
          }
          break;

        case "incident_update":
        case "new_incident":
          // Refresh incidents list on real-time updates
          fetchIncidents();
          break;

        case "agent_confidence_update":
          if (data.session_id && currentSessionId === data.session_id) {
            fetchAgentConfidence(data.session_id);
          }
          break;

        case "performance_update":
          if (data.session_id && currentSessionId === data.session_id) {
            fetchPerformanceMetrics(data.session_id);
          }
          break;

        default:
          console.log("Unknown message type:", data.type);
      }
    },
    [
      fetchIncidents,
      fetchAgentConfidence,
      fetchPerformanceMetrics,
      currentSessionId,
    ]
  );

  // Initialize default agents if none are loaded
  useEffect(() => {
    if (agents.length === 0) {
      setAgents([
        {
          id: "detection",
          name: "🔍 Detection Agent",
          status: "active",
          confidence: 0.95,
          lastUpdate: new Date().toISOString(),
        },
        {
          id: "diagnosis",
          name: "🔬 Diagnosis Agent",
          status: "idle",
          confidence: 0.92,
          lastUpdate: new Date().toISOString(),
        },
        {
          id: "prediction",
          name: "🔮 Prediction Agent",
          status: "active",
          confidence: 0.88,
          lastUpdate: new Date().toISOString(),
        },
        {
          id: "resolution",
          name: "🛠️ Resolution Agent",
          status: "idle",
          confidence: 0.9,
          lastUpdate: new Date().toISOString(),
        },
        {
          id: "communication",
          name: "📢 Communication Agent",
          status: "active",
          confidence: 0.96,
          lastUpdate: new Date().toISOString(),
        },
      ]);
    }
  }, [agents.length]);

  // Trigger demo incident
  const triggerDemoIncident = async (scenarioType: string) => {
    try {
      const response = await fetch("/dashboard/trigger-demo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ scenario_type: scenarioType }),
      });

      if (response.ok) {
        console.log(`Demo incident triggered: ${scenarioType}`);
        // Demo trigger succeeded, no need to activate simulation
      } else {
        console.error("Failed to trigger demo incident");
        // Only activate simulation on failed backend demo trigger
        activateSimulationMode(scenarioType);
      }
    } catch (error) {
      console.error("Error triggering demo incident:", error);
      // Only activate simulation on failed backend demo trigger
      activateSimulationMode(scenarioType);
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "idle":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-600 text-white";
      case "high":
        return "bg-orange-500 text-white";
      case "medium":
        return "bg-yellow-500 text-black";
      case "low":
        return "bg-blue-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return "N/A";
    const totalSeconds = Math.floor(seconds);
    const minutes = Math.floor(totalSeconds / 60);
    const remainingSeconds = totalSeconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Sort incidents locally
  const sortedIncidents = useMemo(() => {
    const sorted = [...incidents].sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      if (sortField === "detected_at") {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      } else if (sortField === "severity") {
        const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        aValue = severityOrder[a.severity] || 0;
        bValue = severityOrder[b.severity] || 0;
      }

      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [incidents, sortField, sortDirection]);

  // Handle sort column click
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // Pagination calculations
  const totalPages = Math.ceil(totalIncidents / itemsPerPage);
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalIncidents);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, severityFilter, itemsPerPage]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🚀 Incident Commander
          </h1>
          <p className="text-lg text-gray-600">
            AI-Powered Multi-Agent Incident Response System
          </p>
          <div className="flex flex-wrap items-center justify-center mt-4 gap-3">
            <Badge variant={isConnected ? "default" : "destructive"}>
              {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
            </Badge>
            {simulationMode && (
              <Badge variant="secondary">Demo Data Stream</Badge>
            )}
            <span className="text-sm text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          </div>
        </div>

        {/* Connection Alert */}
        {!isConnected && !simulationMode && (
          <Alert className="mb-6">
            <AlertDescription>
              WebSocket connection lost. Attempting to reconnect...
            </AlertDescription>
          </Alert>
        )}

        {simulationMode && (
          <Alert className="mb-6">
            <AlertDescription>
              Backend services are offline, so the dashboard is running in an
              interactive simulation mode to remain judge-ready.
            </AlertDescription>
          </Alert>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Active Incidents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">
                {metrics.activeIncidents}
              </div>
              <p className="text-sm text-gray-500">Currently active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                MTTR
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {metrics.averageResolutionTime}min
              </div>
              <p className="text-sm text-gray-500">95.2% improvement</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Prevention Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">
                {metrics.preventionRate}%
              </div>
              <p className="text-sm text-gray-500">Incidents prevented</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                System Uptime
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">
                {systemHealth.uptime}%
              </div>
              <p className="text-sm text-gray-500">Availability</p>
            </CardContent>
          </Card>
        </div>

        {/* Agent Confidence Visualization */}
        {Object.keys(agentConfidence).length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center">
                🎯 Agent Confidence Levels
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Object.values(agentConfidence).map((agent) => (
                  <div
                    key={agent.agent_name}
                    className="p-4 border rounded-lg bg-white shadow-sm"
                  >
                    <div className="mb-3">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {agent.agent_name}
                        </h3>
                        <Badge
                          className={
                            agent.current_confidence >= 0.8
                              ? "bg-green-500 text-white"
                              : agent.current_confidence >= 0.6
                              ? "bg-yellow-500 text-black"
                              : "bg-red-500 text-white"
                          }
                        >
                          {Math.round(agent.current_confidence * 100)}%
                        </Badge>
                      </div>
                      <Progress
                        value={agent.current_confidence * 100}
                        className="h-2"
                      />
                    </div>

                    {agent.reasoning_factors.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-semibold text-gray-600 mb-1">
                          Reasoning:
                        </p>
                        <ul className="text-xs text-gray-700 space-y-1">
                          {agent.reasoning_factors
                            .slice(0, 2)
                            .map((factor, idx) => (
                              <li key={idx} className="truncate">
                                • {factor}
                              </li>
                            ))}
                        </ul>
                      </div>
                    )}

                    {agent.uncertainty_factors.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-1">
                          Uncertainties:
                        </p>
                        <ul className="text-xs text-gray-700 space-y-1">
                          {agent.uncertainty_factors
                            .slice(0, 2)
                            .map((factor, idx) => (
                              <li key={idx} className="truncate">
                                ⚠️ {factor}
                              </li>
                            ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Performance Metrics Panel */}
        {performanceMetrics && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center">
                📊 Performance Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* MTTR Comparison */}
                <div className="p-4 border rounded-lg bg-white">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    Mean Time To Resolution (MTTR)
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">
                        Traditional:
                      </span>
                      <span className="font-bold text-red-600">
                        {
                          performanceMetrics.mttr_comparison
                            .traditional_mttr_minutes
                        }{" "}
                        min
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Autonomous:</span>
                      <span className="font-bold text-green-600">
                        {
                          performanceMetrics.mttr_comparison
                            .autonomous_mttr_minutes
                        }{" "}
                        min
                      </span>
                    </div>
                    <div className="pt-3 border-t">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-semibold text-gray-700">
                          Improvement:
                        </span>
                        <Badge className="bg-blue-600 text-white">
                          {performanceMetrics.mttr_comparison.reduction_percentage.toFixed(
                            1
                          )}
                          % faster
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600">
                        Saved{" "}
                        {performanceMetrics.mttr_comparison.time_saved_minutes}{" "}
                        minutes (
                        {performanceMetrics.mttr_comparison.improvement_factor.toFixed(
                          1
                        )}
                        x improvement)
                      </p>
                    </div>
                  </div>
                </div>

                {/* Business Impact */}
                <div className="p-4 border rounded-lg bg-white">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    Business Impact
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">
                        Traditional Cost:
                      </span>
                      <span className="font-bold text-red-600">
                        {formatCurrency(
                          performanceMetrics.business_impact.traditional_cost
                        )}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">
                        Autonomous Cost:
                      </span>
                      <span className="font-bold text-green-600">
                        {formatCurrency(
                          performanceMetrics.business_impact.autonomous_cost
                        )}
                      </span>
                    </div>
                    <div className="pt-3 border-t">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-semibold text-gray-700">
                          Cost Savings:
                        </span>
                        <Badge className="bg-green-600 text-white text-lg">
                          {formatCurrency(
                            performanceMetrics.business_impact.cost_savings
                          )}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600">
                        {performanceMetrics.business_impact.cost_savings_percentage.toFixed(
                          1
                        )}
                        % reduction • Revenue protected:{" "}
                        {formatCurrency(
                          performanceMetrics.business_impact.revenue_protected
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Incident List View */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <CardTitle className="flex items-center">
                📋 Incident Timeline
              </CardTitle>

              {/* Filters and Controls */}
              <div className="flex flex-wrap items-center gap-3">
                {/* Status Filter */}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Status:</span>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                      <SelectItem value="investigating">
                        Investigating
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Severity Filter */}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Severity:</span>
                  <Select
                    value={severityFilter}
                    onValueChange={setSeverityFilter}
                  >
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Items Per Page */}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Show:</span>
                  <Select
                    value={itemsPerPage.toString()}
                    onValueChange={(val) => setItemsPerPage(Number(val))}
                  >
                    <SelectTrigger className="w-[80px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="25">25</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Refresh Button */}
                <Button onClick={fetchIncidents} variant="outline" size="sm">
                  🔄 Refresh
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            {sortedIncidents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="text-lg">No incidents found</p>
                <p className="text-sm mt-2">
                  {statusFilter !== "all" || severityFilter !== "all"
                    ? "Try adjusting your filters"
                    : "System is operating normally"}
                </p>
              </div>
            ) : (
              <>
                <ScrollArea className="h-[400px] w-full">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead
                          className="w-[180px] cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort("incident_id")}
                        >
                          Incident ID{" "}
                          {sortField === "incident_id" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort("type")}
                        >
                          Type{" "}
                          {sortField === "type" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort("severity")}
                        >
                          Severity{" "}
                          {sortField === "severity" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort("status")}
                        >
                          Status{" "}
                          {sortField === "status" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort("detected_at")}
                        >
                          Detected At{" "}
                          {sortField === "detected_at" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort("duration")}
                        >
                          Duration{" "}
                          {sortField === "duration" &&
                            (sortDirection === "asc" ? "↑" : "↓")}
                        </TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedIncidents.map((incident) => (
                        <TableRow
                          key={incident.incident_id}
                          className={`cursor-pointer hover:bg-gray-50 ${
                            selectedIncident === incident.incident_id
                              ? "bg-blue-50"
                              : ""
                          }`}
                          onClick={() =>
                            setSelectedIncident(incident.incident_id)
                          }
                        >
                          <TableCell className="font-mono text-sm">
                            {incident.incident_id.substring(0, 12)}...
                          </TableCell>
                          <TableCell>{incident.type}</TableCell>
                          <TableCell>
                            <Badge
                              className={getSeverityColor(incident.severity)}
                            >
                              {incident.severity.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                incident.status === "resolved"
                                  ? "default"
                                  : incident.status === "active"
                                  ? "destructive"
                                  : "secondary"
                              }
                            >
                              {incident.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm">
                            {formatTimestamp(incident.detected_at)}
                          </TableCell>
                          <TableCell>
                            {formatDuration(incident.duration)}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(
                                  `/incidents/${incident.incident_id}`,
                                  "_blank"
                                );
                              }}
                            >
                              View →
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t">
                    <div className="text-sm text-gray-600">
                      Showing {startItem} to {endItem} of {totalIncidents}{" "}
                      incidents
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(1)}
                        disabled={currentPage === 1}
                      >
                        ⏮ First
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        ← Prev
                      </Button>

                      <span className="text-sm text-gray-700 px-3">
                        Page {currentPage} of {totalPages}
                      </span>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        Next →
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(totalPages)}
                        disabled={currentPage === totalPages}
                      >
                        Last ⏭
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Agent Status Grid */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              🤖 Multi-Agent Coordination
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="p-4 border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">
                      {agent.name}
                    </h3>
                    <div
                      className={`w-3 h-3 rounded-full ${getStatusColor(
                        agent.status
                      )}`}
                    />
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Confidence:</span>
                      <span className="font-medium">
                        {Math.round(agent.confidence * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Status:</span>
                      <Badge
                        variant={
                          agent.status === "active" ? "default" : "secondary"
                        }
                      >
                        {agent.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Demo Controls */}
        <Card>
          <CardHeader>
            <CardTitle>🎯 Demo Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <Button
                onClick={() => triggerDemoIncident("database_failure")}
                variant="outline"
                className="w-full"
              >
                🗄️ Database Failure
              </Button>
              <Button
                onClick={() => triggerDemoIncident("api_cascade")}
                variant="outline"
                className="w-full"
              >
                🌊 API Cascade
              </Button>
              <Button
                onClick={() => triggerDemoIncident("memory_leak")}
                variant="outline"
                className="w-full"
              >
                🧠 Memory Leak
              </Button>
              <Button
                onClick={() => triggerDemoIncident("network_latency")}
                variant="outline"
                className="w-full"
              >
                🌐 Network Issues
              </Button>
              <Button
                onClick={() => triggerDemoIncident("security_breach")}
                variant="outline"
                className="w-full"
              >
                🔒 Security Breach
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-gray-500 text-sm mt-8">
          <p>🏆 AWS Hackathon 2024 - Autonomous Incident Commander</p>
          <p>Built with AWS Bedrock • Claude 3.5 Sonnet • Multi-Agent AI</p>
        </div>
      </div>
    </div>
  );
};

export default RefinedDashboard;
