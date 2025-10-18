export interface AgentAction {
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

export interface Incident {
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

export interface MetricData {
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

export interface UserInfo {
  name: string;
  email: string;
  avatar: string;
  role: string;
}

export interface SystemStats {
  activeIncidents: number;
  resolvedToday: number;
  mttrReduction: number;
  agentsActive: number;
}

export interface DashboardState {
  currentIncident: Incident | null;
  agentActions: AgentAction[];
  metrics: MetricData[];
  systemStatus: "autonomous" | "monitoring" | "incident" | "maintenance";
  isConnected: boolean;
}
