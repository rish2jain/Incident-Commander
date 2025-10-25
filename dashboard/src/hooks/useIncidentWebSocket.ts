/**
 * WebSocket Hook for Dashboard 3 (Production Operations Dashboard)
 *
 * Provides real-time incident updates, agent status, and system metrics
 * via WebSocket connection to the backend.
 *
 * Features:
 * - Automatic connection management
 * - Exponential backoff reconnection
 * - Message type routing
 * - Connection status monitoring
 * - Latency tracking
 *
 * IMPORTANT: This hook should ONLY be used in Dashboard 3 (/ops).
 * Dashboard 1 and Dashboard 2 do NOT use WebSocket.
 */

import { useEffect, useRef, useState, useCallback } from "react";

export interface AgentState {
  name: string;
  state: string;
  confidence?: number;
  metadata?: Record<string, any>;
}

export interface IncidentUpdate {
  id: string;
  title: string;
  severity: string;
  phase: string;
  current_state?: string;
  priority?: number;
  processing_duration?: number;
  state_transitions?: any[];
  assigned_agents?: string[];
  is_escalated?: boolean;
  timestamp: string;
  affected_services?: string[];
  estimated_impact?: Record<string, any>;
  workflow_id?: string;
}

export interface BusinessMetrics {
  mttr_seconds: number;
  incidents_handled: number;
  incidents_prevented: number;
  cost_savings_usd: number;
  efficiency_score: number;
  timestamp: string;
}

export interface SystemHealthMetrics {
  cpu_percent: number;
  memory_percent: number;
  active_agents: number;
  websocket_connections: number;
  avg_latency_ms: number;
  timestamp: string;
}

export interface ConsensusUpdate {
  incident_id: string;
  decision: string;
  confidence: number;
  voting_results: Record<string, any>;
  timestamp: string;
}

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: any;
}

export interface WebSocketHookState {
  // Connection status
  connected: boolean;
  connecting: boolean;
  connectionError: string | null;
  latency: number | null;

  // Real-time data
  agentStates: Record<string, AgentState>;
  activeIncidents: IncidentUpdate[];
  businessMetrics: BusinessMetrics | null;
  systemHealth: SystemHealthMetrics | null;

  // Actions
  sendMessage: (action: string, data?: any) => void;
  triggerDemo: () => void;
  resetAgents: () => void;
  reconnect: () => void;
}

interface UseIncidentWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export function useIncidentWebSocket(
  options: UseIncidentWebSocketOptions = {}
): WebSocketHookState {
  const {
    url =
      process.env.NEXT_PUBLIC_WEBSOCKET_URL ||
      process.env.NEXT_PUBLIC_WS_URL ||
      "ws://localhost:8000/dashboard/ws",
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatInterval: heartbeatIntervalMs = 30000,
  } = options;

  // State
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>(
    {}
  );
  const [activeIncidents, setActiveIncidents] = useState<IncidentUpdate[]>([]);
  const [businessMetrics, setBusinessMetrics] =
    useState<BusinessMetrics | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealthMetrics | null>(
    null
  );

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const connectionId = useRef<string>(
    `dashboard-3-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  );

  // Single message handler (defined first)
  const handleSingleMessage = useCallback((message: WebSocketMessage) => {
    const { type, data: messageData } = message;

    switch (type) {
      case "initial_state":
        // Initial state on connection
        if (messageData.agent_states) {
          const states: Record<string, AgentState> = {};
          Object.entries(messageData.agent_states).forEach(([name, state]) => {
            states[name] = {
              name,
              state: state as string,
            };
          });
          setAgentStates(states);
        }
        if (messageData.active_incidents) {
          setActiveIncidents(messageData.active_incidents);
        }
        break;

      case "agent_state_update":
        // Update specific agent state
        if (messageData.agent_name && messageData.state) {
          setAgentStates((prev) => ({
            ...prev,
            [messageData.agent_name]: {
              name: messageData.agent_name,
              state: messageData.state,
              confidence: messageData.metadata?.confidence,
              metadata: messageData.metadata,
            },
          }));
        }
        // Update all agent states if provided
        if (messageData.all_states) {
          const states: Record<string, AgentState> = {};
          Object.entries(messageData.all_states).forEach(([name, state]) => {
            states[name] = {
              name,
              state: state as string,
            };
          });
          setAgentStates(states);
        }
        break;

      case "incident_update":
        // Update incident and incident list
        if (messageData.incident) {
          setActiveIncidents((prev) => {
            const filtered = prev.filter(
              (inc) => inc.id !== messageData.incident.id
            );
            return [messageData.incident, ...filtered];
          });
        }
        if (messageData.active_incidents) {
          setActiveIncidents(messageData.active_incidents);
        }
        break;

      case "business_metrics_update":
        // Update business metrics
        setBusinessMetrics(messageData);
        break;

      case "system_health_update":
        // Update system health metrics
        setSystemHealth(messageData);
        break;

      case "consensus_update":
        // Log consensus decisions
        console.log("Consensus decision:", messageData);
        break;

      case "pong":
        // Update latency from ping/pong
        if (messageData.latency_ms) {
          setLatency(messageData.latency_ms);
        }
        break;

      case "demo_triggered":
      case "demo_scenario_started":
      case "agent_reset_complete":
        // Log demo/reset events
        console.log(`WebSocket event: ${type}`, messageData);
        break;

      case "error":
        console.error("WebSocket error message:", messageData);
        setConnectionError(messageData.message || "Unknown error");
        break;

      default:
        console.log("Unknown message type:", type, messageData);
    }
  }, []);

  // Message handler (defined after handleSingleMessage)
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Handle batched messages
        if (data.type === "message_batch") {
          data.messages?.forEach((msg: WebSocketMessage) => {
            handleSingleMessage(msg);
          });
          return;
        }

        // Handle single message
        handleSingleMessage(data);
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    },
    [handleSingleMessage]
  );

  // Connection management
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || connecting) {
      return;
    }

    setConnecting(true);
    setConnectionError(null);

    try {
      const wsUrl = `${url}?client_id=${connectionId.current}&dashboard_type=ops`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("✓ WebSocket connected");
        setConnected(true);
        setConnecting(false);
        setConnectionError(null);
        reconnectAttempts.current = 0;

        // Start heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(
              JSON.stringify({
                action: "ping",
                timestamp: new Date().toISOString(),
              })
            );
          }
        }, heartbeatIntervalMs);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnectionError("Connection error");
      };

      ws.onclose = (event) => {
        console.log("WebSocket closed:", event.code, event.reason);
        setConnected(false);
        setConnecting(false);

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Attempt reconnection
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay =
            reconnectInterval * Math.pow(1.5, reconnectAttempts.current);
          console.log(
            `Reconnecting in ${delay}ms... (attempt ${
              reconnectAttempts.current + 1
            }/${maxReconnectAttempts})`
          );

          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else {
          setConnectionError("Max reconnection attempts reached");
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      setConnecting(false);
      setConnectionError("Failed to create WebSocket connection");
    }
  }, [
    url,
    connecting,
    handleMessage,
    reconnectInterval,
    maxReconnectAttempts,
    heartbeatIntervalMs,
  ]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
    setConnecting(false);
  }, []);

  const sendMessage = useCallback(
    (action: string, data: Record<string, unknown> = {}) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            action,
            ...data,
            timestamp: new Date().toISOString(),
          })
        );
      } else {
        console.warn("WebSocket not connected, cannot send message");
      }
    },
    []
  );

  const triggerDemo = useCallback(() => {
    sendMessage("trigger_demo_incident");
  }, [sendMessage]);

  const resetAgents = useCallback(() => {
    sendMessage("reset_agents");
  }, [sendMessage]);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    setTimeout(connect, 100);
  }, [connect, disconnect]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]); // Only depend on autoConnect to prevent reconnection loops

  return {
    connected,
    connecting,
    connectionError,
    latency,
    agentStates,
    activeIncidents,
    businessMetrics,
    systemHealth,
    sendMessage,
    triggerDemo,
    resetAgents,
    reconnect,
  };
}
