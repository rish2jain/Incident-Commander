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

// Auto-scroll related types
export interface AutoScrollConfig {
  threshold: number;
  resumeDelay: number;
  smoothScroll: boolean;
  maxScrollSpeed: number;
  debounceDelay: number;
}

export interface ScrollState {
  isAutoScrollEnabled: boolean;
  isUserScrolling: boolean;
  isNearBottom: boolean;
  lastScrollPosition: number;
  messageCount: number;
  isPaused: boolean;
  lastUserInteraction: number;
}

export interface ScrollMetrics {
  scrollTop: number;
  scrollHeight: number;
  clientHeight: number;
  distanceFromBottom: number;
}

// Incident Status Tracking types
export interface IncidentStatus {
  id: string;
  phase:
    | "detection"
    | "diagnosis"
    | "prediction"
    | "resolution"
    | "communication"
    | "resolved";
  progress: number; // 0-100
  startTime: Date;
  estimatedCompletion?: Date;
  isComplete: boolean;
  resolutionTime?: number;
  severity?: "low" | "medium" | "high" | "critical";
  title?: string;
  description?: string;
}

export interface StatusTransition {
  from: string;
  to: string;
  timestamp: Date;
  duration: number;
}

export interface IncidentResolution {
  incidentId: string;
  isResolved: boolean;
  resolutionTime: number; // in seconds
  totalPhases: number;
  completedPhases: number;
  currentPhase?: string;
  resolutionSummary?: string;
  actionsPerformed: string[];
  businessImpact: {
    costSaved: number;
    downtime: number;
    affectedUsers: number;
  };
  showCelebration: boolean;
  celebrationDuration: number;
  fadeOutDelay: number;
}

// Connection Management types
export interface ConnectionConfig {
  wsUrl: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  connectionTimeout: number;
  exponentialBackoff: boolean;
  maxReconnectDelay: number;
}

export interface ConnectionState {
  status:
    | "connecting"
    | "connected"
    | "disconnected"
    | "error"
    | "reconnecting";
  lastConnected: Date | null;
  reconnectAttempts: number;
  latency: number;
  messageQueue: QueuedMessage[];
  connectionQuality: "excellent" | "good" | "poor" | "unknown";
  lastHeartbeat: Date | null;
  isOnline: boolean;
}

export interface QueuedMessage {
  id: string;
  type: string;
  data: any;
  timestamp: Date;
  retryCount: number;
  maxRetries: number;
}

export interface ConnectionMetrics {
  totalConnections: number;
  totalDisconnections: number;
  totalReconnections: number;
  averageLatency: number;
  uptime: number;
  lastConnectionTime: Date | null;
  messagesQueued: number;
  messagesReplayed: number;
}
