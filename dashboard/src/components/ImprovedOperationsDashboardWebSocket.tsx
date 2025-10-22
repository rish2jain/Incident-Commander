/**
 * Improved Operations Dashboard with WebSocket Integration
 *
 * Production-ready Dashboard 3 with real-time data streaming.
 * Integrates useIncidentWebSocket hook for live updates.
 *
 * Features:
 * - Real-time agent state updates
 * - Live incident monitoring
 * - Business metrics streaming
 * - System health monitoring
 * - Connection status indicators
 */

"use client";

import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Zap,
  Eye,
  Settings,
  BarChart3,
  Brain,
  MessageSquare,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Play,
  Sparkles,
  Lock,
  Cpu,
  Wifi,
  WifiOff,
  RefreshCw,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
  Progress,
} from "@/components/shared";
import {
  useClientSideTimestamp,
  formatTimeSafe,
} from "@/hooks/useClientSideTimestamp";
import { useIncidentWebSocket } from "@/hooks/useIncidentWebSocket";

// Connection Status Component
function ConnectionStatus({
  connected,
  connecting,
  error,
  latency,
  onReconnect,
}: {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  latency: number | null;
  onReconnect: () => void;
}) {
  return (
    <Card className="mb-4 border-l-4 border-l-blue-500">
      <CardContent className="py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {connected ? (
              <>
                <Wifi className="w-5 h-5 text-green-500" />
                <div>
                  <div className="font-semibold text-green-400">
                    Connected to Live System
                  </div>
                  <div className="text-xs text-slate-400">
                    {latency !== null
                      ? `Latency: ${latency.toFixed(0)}ms`
                      : "Monitoring..."}
                  </div>
                </div>
              </>
            ) : connecting ? (
              <>
                <RefreshCw className="w-5 h-5 text-yellow-500 animate-spin" />
                <div>
                  <div className="font-semibold text-yellow-400">
                    Connecting...
                  </div>
                  <div className="text-xs text-slate-400">
                    Establishing WebSocket connection
                  </div>
                </div>
              </>
            ) : (
              <>
                <WifiOff className="w-5 h-5 text-red-500" />
                <div>
                  <div className="font-semibold text-red-400">Disconnected</div>
                  <div className="text-xs text-slate-400">
                    {error || "Connection lost"}
                  </div>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!connected && !connecting && (
              <Button
                size="sm"
                onClick={onReconnect}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Reconnect
              </Button>
            )}
            <Badge
              variant={connected ? "default" : "destructive"}
              className={connected ? "bg-green-600" : ""}
            >
              {connected ? "LIVE" : "OFFLINE"}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Agent Card Component
function LiveAgentCard({
  name,
  state,
  confidence,
  metadata,
}: {
  name: string;
  state: string;
  confidence?: number;
  metadata?: Record<string, any>;
}) {
  const getAgentIcon = (name: string) => {
    const icons: Record<string, React.ReactNode> = {
      Detection: <AlertCircle className="w-5 h-5" />,
      Diagnosis: <Brain className="w-5 h-5" />,
      Prediction: <Sparkles className="w-5 h-5" />,
      Resolution: <Settings className="w-5 h-5" />,
      Communication: <MessageSquare className="w-5 h-5" />,
    };
    return icons[name] || <Cpu className="w-5 h-5" />;
  };

  const getStatusBadge = (state: string) => {
    const stateUpper = state.toUpperCase();
    if (stateUpper.includes("COMPLETE") || stateUpper.includes("SUCCESS"))
      return (
        <Badge variant="default" className="bg-green-600">
          ✓ Complete
        </Badge>
      );
    if (
      stateUpper.includes("ANALYZING") ||
      stateUpper.includes("PROCESSING") ||
      stateUpper.includes("ACTIVE")
    )
      return (
        <Badge variant="secondary" className="bg-yellow-500 text-white">
          ⏳ Active
        </Badge>
      );
    if (stateUpper.includes("ERROR") || stateUpper.includes("FAIL"))
      return <Badge variant="destructive">✗ Error</Badge>;
    return <Badge variant="outline">Idle</Badge>;
  };

  const getStatusColor = (state: string, confidence?: number) => {
    const stateUpper = state.toUpperCase();
    if (stateUpper.includes("ERROR")) return "border-red-500 bg-red-900/20";
    if (stateUpper.includes("ANALYZING") || stateUpper.includes("ACTIVE"))
      return "border-yellow-500 bg-yellow-900/20";
    if (confidence && confidence >= 0.9)
      return "border-green-500 bg-green-900/20";
    if (confidence && confidence >= 0.7)
      return "border-blue-500 bg-blue-900/20";
    return "border-slate-600 bg-slate-800/50";
  };

  const isActive =
    state.toUpperCase().includes("ANALYZING") ||
    state.toUpperCase().includes("ACTIVE") ||
    state.toUpperCase().includes("PROCESSING");

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={`transition-all duration-200 hover:shadow-lg ${getStatusColor(state, confidence)}`}
      >
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <motion.div
                className="text-blue-600"
                animate={isActive ? { rotate: [0, 10, -10, 0] } : {}}
                transition={{
                  duration: 2,
                  repeat: isActive ? Infinity : 0,
                }}
              >
                {getAgentIcon(name)}
              </motion.div>
              <div>
                <CardTitle className="text-sm font-semibold">{name}</CardTitle>
                <div className="mt-1">{getStatusBadge(state)}</div>
              </div>
            </div>
            {isActive && (
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-2 h-2 bg-blue-500 rounded-full"
              />
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-slate-400 mb-2">{state}</div>
          {confidence !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Confidence:</span>
              <span
                className={`text-sm font-semibold ${
                  confidence >= 0.9
                    ? "text-green-400"
                    : confidence >= 0.7
                      ? "text-blue-400"
                      : "text-orange-400"
                }`}
              >
                {(confidence * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Business Metrics Card
function BusinessMetricsCard({
  metrics,
}: {
  metrics: {
    mttr_seconds: number;
    incidents_handled: number;
    incidents_prevented: number;
    cost_savings_usd: number;
    efficiency_score: number;
  } | null;
}) {
  if (!metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>📊 Business Impact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-slate-400 py-8">
            <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>Waiting for live metrics...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-l-4 border-l-green-500">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>📊 Business Impact</span>
          <Badge variant="default" className="bg-green-600">
            LIVE DATA
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-slate-400">MTTR</div>
            <div className="text-2xl font-bold text-green-400">
              {Math.floor(metrics.mttr_seconds / 60)}m {metrics.mttr_seconds % 60}s
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-slate-400">Cost Savings</div>
            <div className="text-2xl font-bold text-green-400">
              ${(metrics.cost_savings_usd / 1000).toFixed(0)}K
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-slate-400">Incidents Handled</div>
            <div className="text-2xl font-bold text-blue-400">
              {metrics.incidents_handled}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-slate-400">Prevented</div>
            <div className="text-2xl font-bold text-purple-400">
              {metrics.incidents_prevented}
            </div>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Efficiency Score</span>
            <span className="text-sm font-semibold text-green-400">
              {(metrics.efficiency_score * 100).toFixed(1)}%
            </span>
          </div>
          <Progress
            value={metrics.efficiency_score * 100}
            className="mt-2 h-2"
          />
        </div>
      </CardContent>
    </Card>
  );
}

// Incident Card
function IncidentCard({ incident }: { incident: any }) {
  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case "CRITICAL":
        return "border-red-500 bg-red-900/20";
      case "HIGH":
        return "border-orange-500 bg-orange-900/20";
      case "MEDIUM":
        return "border-yellow-500 bg-yellow-900/20";
      default:
        return "border-blue-500 bg-blue-900/20";
    }
  };

  return (
    <Card className={`border-l-4 ${getSeverityColor(incident.severity)}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">{incident.title}</CardTitle>
          <Badge
            variant={
              incident.severity === "CRITICAL" ? "destructive" : "secondary"
            }
          >
            {incident.severity}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-xs text-slate-400 space-y-1">
          <div>Phase: {incident.phase}</div>
          <div>ID: {incident.id}</div>
          {incident.processing_duration && (
            <div>Duration: {incident.processing_duration}s</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Main Dashboard Component
export function ImprovedOperationsDashboardWebSocket() {
  const timestamp = useClientSideTimestamp();

  // WebSocket integration
  const {
    connected,
    connecting,
    connectionError,
    latency,
    agentStates,
    activeIncidents,
    businessMetrics,
    systemHealth,
    triggerDemo,
    resetAgents,
    reconnect,
  } = useIncidentWebSocket({ autoConnect: true });

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">
              🚀 Operations Dashboard
            </h1>
            <p className="text-slate-400 mt-1">
              Production Incident Response System - Live Monitoring
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-400">
              {formatTimeSafe(timestamp)}
            </div>
          </div>
        </div>

        {/* Connection Status */}
        <ConnectionStatus
          connected={connected}
          connecting={connecting}
          error={connectionError}
          latency={latency}
          onReconnect={reconnect}
        />

        {/* Controls */}
        <Card>
          <CardHeader>
            <CardTitle>System Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Button
                onClick={triggerDemo}
                disabled={!connected}
                className="bg-red-600 hover:bg-red-700"
              >
                <Play className="w-4 h-4 mr-2" />
                Trigger Demo Incident
              </Button>
              <Button
                onClick={resetAgents}
                disabled={!connected}
                variant="outline"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reset Agents
              </Button>
              {!connected && (
                <Badge variant="secondary" className="ml-2">
                  Connect to enable controls
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Business Metrics */}
        <BusinessMetricsCard metrics={businessMetrics} />

        {/* Agent Status Grid */}
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-6 h-6 text-blue-400" />
            AI Agent Status
            <Badge variant="outline" className="ml-2">
              {Object.keys(agentStates).length} Agents
            </Badge>
          </h2>
          {Object.keys(agentStates).length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="text-slate-400">
                  <Cpu className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Waiting for agent status updates...</p>
                  <p className="text-sm mt-2">
                    {connected
                      ? "Connected - agents will appear when active"
                      : "Connect to WebSocket to see live agents"}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.values(agentStates).map((agent) => (
                <LiveAgentCard
                  key={agent.name}
                  name={agent.name}
                  state={agent.state}
                  confidence={agent.confidence}
                  metadata={agent.metadata}
                />
              ))}
            </div>
          )}
        </div>

        {/* Active Incidents */}
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-orange-400" />
            Active Incidents
            <Badge variant="outline" className="ml-2">
              {activeIncidents.length}
            </Badge>
          </h2>
          {activeIncidents.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="text-slate-400">
                  <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500 opacity-50" />
                  <p className="text-lg font-semibold text-green-400">
                    All Systems Operational
                  </p>
                  <p className="text-sm mt-2">No active incidents</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {activeIncidents.map((incident) => (
                <IncidentCard key={incident.id} incident={incident} />
              ))}
            </div>
          )}
        </div>

        {/* System Health */}
        {systemHealth && (
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-1">
                  <div className="text-xs text-slate-400">CPU Usage</div>
                  <div className="text-xl font-bold">
                    {systemHealth.cpu_percent.toFixed(1)}%
                  </div>
                  <Progress value={systemHealth.cpu_percent} className="h-1" />
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-slate-400">Memory</div>
                  <div className="text-xl font-bold">
                    {systemHealth.memory_percent.toFixed(1)}%
                  </div>
                  <Progress
                    value={systemHealth.memory_percent}
                    className="h-1"
                  />
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-slate-400">Active Agents</div>
                  <div className="text-xl font-bold text-blue-400">
                    {systemHealth.active_agents}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-slate-400">Avg Latency</div>
                  <div className="text-xl font-bold text-green-400">
                    {systemHealth.avg_latency_ms.toFixed(0)}ms
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-slate-500 pt-6 border-t border-slate-800">
          <p>
            Dashboard 3: Production Operations • Real-time WebSocket
            Integration
          </p>
          <p className="mt-1">
            {connected ? (
              <span className="text-green-400">● Live System</span>
            ) : (
              <span className="text-red-400">● Disconnected</span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
