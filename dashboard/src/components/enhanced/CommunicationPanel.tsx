/**
 * Enhanced Communication Panel Component
 *
 * Implements improved inter-agent communication display with better
 * message categorization, timestamps, and user-friendly descriptions.
 */

import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { cn } from "../../lib/utils";
import { Tooltip } from "./InteractiveMetrics";

interface AgentMessage {
  id: string;
  timestamp: string;
  from: string;
  to: string;
  message: string;
  messageType: string;
  confidence?: number;
  priority?: "low" | "medium" | "high" | "critical";
  metadata?: {
    correlationId?: string;
    retryCount?: number;
    processingTime?: number;
    payload?: any;
  };
}

interface CommunicationPanelProps {
  messages: AgentMessage[];
  onMessageClick?: (message: AgentMessage) => void;
  className?: string;
}

// Message Type Definitions with User-Friendly Descriptions
const MESSAGE_TYPES = {
  status_update: {
    icon: "📊",
    label: "Status Update",
    description: "Agent reporting current operational status",
    color: "text-blue-400 bg-blue-500/10",
  },
  capability_sync: {
    icon: "🔄",
    label: "Capability Sync",
    description: "Agents synchronizing available capabilities",
    color: "text-green-400 bg-green-500/10",
  },
  evidence_sharing: {
    icon: "🔍",
    label: "Evidence Sharing",
    description: "Sharing analysis results and findings",
    color: "text-purple-400 bg-purple-500/10",
  },
  consensus_building: {
    icon: "🤝",
    label: "Consensus Building",
    description: "Collaborative decision-making process",
    color: "text-yellow-400 bg-yellow-500/10",
  },
  action_request: {
    icon: "⚡",
    label: "Action Request",
    description: "Requesting specific action from another agent",
    color: "text-orange-400 bg-orange-500/10",
  },
  error_report: {
    icon: "❌",
    label: "Error Report",
    description: "Reporting errors or failures",
    color: "text-red-400 bg-red-500/10",
  },
  heartbeat: {
    icon: "💓",
    label: "Heartbeat",
    description: "Regular health check signal",
    color: "text-slate-400 bg-slate-500/10",
  },
  coordination: {
    icon: "🎯",
    label: "Coordination",
    description: "Coordinating parallel activities",
    color: "text-cyan-400 bg-cyan-500/10",
  },
};

// Agent Color Mapping
const AGENT_COLORS = {
  Detection: "text-green-400 bg-green-500/10",
  Diagnosis: "text-blue-400 bg-blue-500/10",
  Prediction: "text-purple-400 bg-purple-500/10",
  Resolution: "text-orange-400 bg-orange-500/10",
  Communication: "text-cyan-400 bg-cyan-500/10",
};

// Individual Message Component
interface MessageItemProps {
  message: AgentMessage;
  onClick?: (message: AgentMessage) => void;
  isExpanded?: boolean;
}

function MessageItem({
  message,
  onClick,
  isExpanded = false,
}: MessageItemProps) {
  const [showDetails, setShowDetails] = useState(isExpanded);

  const messageTypeInfo = MESSAGE_TYPES[
    message.messageType as keyof typeof MESSAGE_TYPES
  ] || {
    icon: "📝",
    label: message.messageType,
    description: "Unknown message type",
    color: "text-slate-400 bg-slate-500/10",
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case "critical":
        return "text-red-400 bg-red-500/20";
      case "high":
        return "text-orange-400 bg-orange-500/20";
      case "medium":
        return "text-yellow-400 bg-yellow-500/20";
      case "low":
        return "text-green-400 bg-green-500/20";
      default:
        return "text-slate-400 bg-slate-500/20";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString("en-US", {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div
      className={cn(
        "p-3 border border-slate-600 rounded-lg transition-all duration-200 cursor-pointer",
        "hover:border-slate-500 hover:bg-slate-800/30",
        showDetails && "ring-1 ring-blue-500/30"
      )}
      onClick={() => {
        setShowDetails(!showDetails);
        onClick?.(message);
      }}
    >
      {/* Message Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3 flex-1">
          {/* Message Type Icon */}
          <Tooltip content={messageTypeInfo.description}>
            <div
              className={cn(
                "flex items-center justify-center w-8 h-8 rounded-full text-sm",
                messageTypeInfo.color
              )}
            >
              {messageTypeInfo.icon}
            </div>
          </Tooltip>

          {/* Agent Flow */}
          <div className="flex items-center gap-2 flex-1">
            <Badge
              variant="outline"
              className={cn(
                "text-xs",
                AGENT_COLORS[message.from as keyof typeof AGENT_COLORS] ||
                  "text-slate-400"
              )}
            >
              {message.from}
            </Badge>
            <span className="text-slate-500 text-xs">→</span>
            <Badge
              variant="outline"
              className={cn(
                "text-xs",
                AGENT_COLORS[message.to as keyof typeof AGENT_COLORS] ||
                  "text-slate-400"
              )}
            >
              {message.to}
            </Badge>
          </div>
        </div>

        {/* Message Metadata */}
        <div className="flex items-center gap-2">
          {message.priority && (
            <Badge
              variant="secondary"
              className={cn("text-xs", getPriorityColor(message.priority))}
            >
              {message.priority}
            </Badge>
          )}

          <Badge
            variant="outline"
            className={cn("text-xs", messageTypeInfo.color)}
          >
            {messageTypeInfo.label}
          </Badge>

          <Button
            variant="ghost"
            size="sm"
            className="h-5 w-5 p-0 text-slate-400"
            onClick={(e) => {
              e.stopPropagation();
              setShowDetails(!showDetails);
            }}
          >
            {showDetails ? "−" : "+"}
          </Button>
        </div>
      </div>

      {/* Message Content */}
      <div className="mb-2">
        <p className="text-sm text-slate-200 leading-relaxed">
          {message.message}
        </p>
      </div>

      {/* Message Footer */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-3">
          <span>⏰ {formatTimestamp(message.timestamp)}</span>
          {message.confidence && (
            <span>🎯 {(message.confidence * 100).toFixed(0)}%</span>
          )}
          {message.metadata?.processingTime && (
            <span>⚡ {message.metadata.processingTime}ms</span>
          )}
        </div>

        {message.metadata?.correlationId && (
          <Tooltip
            content={`Correlation ID: ${message.metadata.correlationId}`}
          >
            <span className="font-mono text-xs">
              #{message.metadata.correlationId.slice(-6)}
            </span>
          </Tooltip>
        )}
      </div>

      {/* Expanded Details */}
      {showDetails && message.metadata && (
        <div className="mt-3 pt-3 border-t border-slate-600 space-y-2 animate-slide-up">
          <h5 className="text-xs font-semibold text-slate-300">
            Message Details
          </h5>

          <div className="grid grid-cols-2 gap-3 text-xs">
            {message.metadata.correlationId && (
              <div>
                <span className="text-slate-400">Correlation ID:</span>
                <div className="font-mono text-slate-200 mt-1">
                  {message.metadata.correlationId}
                </div>
              </div>
            )}

            {message.metadata.retryCount !== undefined && (
              <div>
                <span className="text-slate-400">Retry Count:</span>
                <div className="text-slate-200 mt-1">
                  {message.metadata.retryCount}
                </div>
              </div>
            )}

            {message.metadata.processingTime && (
              <div>
                <span className="text-slate-400">Processing Time:</span>
                <div className="text-slate-200 mt-1">
                  {message.metadata.processingTime}ms
                </div>
              </div>
            )}
          </div>

          {message.metadata.payload && (
            <div>
              <span className="text-slate-400 text-xs">Payload:</span>
              <pre className="text-xs bg-slate-800 p-2 rounded mt-1 overflow-x-auto">
                {JSON.stringify(message.metadata.payload, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Main Communication Panel Component
export function CommunicationPanel({
  messages,
  onMessageClick,
  className,
}: CommunicationPanelProps) {
  const [filter, setFilter] = useState("");
  const [selectedAgent, setSelectedAgent] = useState<string>("all");
  const [selectedMessageType, setSelectedMessageType] = useState<string>("all");
  const [autoScroll, setAutoScroll] = useState(true);

  // Filter messages based on current filters
  const filteredMessages = messages.filter((message) => {
    const matchesFilter =
      filter === "" ||
      message.message.toLowerCase().includes(filter.toLowerCase()) ||
      message.from.toLowerCase().includes(filter.toLowerCase()) ||
      message.to.toLowerCase().includes(filter.toLowerCase());

    const matchesAgent =
      selectedAgent === "all" ||
      message.from === selectedAgent ||
      message.to === selectedAgent;

    const matchesType =
      selectedMessageType === "all" ||
      message.messageType === selectedMessageType;

    return matchesFilter && matchesAgent && matchesType;
  });

  // Get unique agents and message types for filters
  const uniqueAgents = Array.from(
    new Set([...messages.map((m) => m.from), ...messages.map((m) => m.to)])
  ).sort();

  const uniqueMessageTypes = Array.from(
    new Set(messages.map((m) => m.messageType))
  ).sort();

  const messagesRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages, autoScroll]);

  // Message statistics
  const messageStats = {
    total: messages.length,
    byType: Object.entries(
      messages.reduce((acc, msg) => {
        acc[msg.messageType] = (acc[msg.messageType] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    ).sort(([, a], [, b]) => b - a),
    avgConfidence:
      messages.filter((m) => m.confidence).length > 0
        ? messages
            .filter((m) => m.confidence)
            .reduce((sum, m) => sum + (m.confidence || 0), 0) /
          messages.filter((m) => m.confidence).length
        : 0,
  };

  return (
    <Card className={cn("card-glass", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            💬 Inter-Agent Communication
            <Badge variant="secondary" className="text-xs">
              {filteredMessages.length} / {messages.length} messages
            </Badge>
          </CardTitle>

          <div className="flex items-center gap-2">
            <Tooltip content="Auto-scroll to latest messages">
              <Button
                variant={autoScroll ? "default" : "outline"}
                size="sm"
                onClick={() => setAutoScroll(!autoScroll)}
                className="text-xs"
              >
                📜 Auto-scroll
              </Button>
            </Tooltip>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mt-4">
          <Input
            placeholder="Filter messages..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="flex-1 h-8 text-sm"
          />

          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="h-8 px-2 text-sm bg-slate-700 border border-slate-600 rounded"
          >
            <option value="all">All Agents</option>
            {uniqueAgents.map((agent) => (
              <option key={agent} value={agent}>
                {agent}
              </option>
            ))}
          </select>

          <select
            value={selectedMessageType}
            onChange={(e) => setSelectedMessageType(e.target.value)}
            className="h-8 px-2 text-sm bg-slate-700 border border-slate-600 rounded"
          >
            <option value="all">All Types</option>
            {uniqueMessageTypes.map((type) => (
              <option key={type} value={type}>
                {MESSAGE_TYPES[type as keyof typeof MESSAGE_TYPES]?.label ||
                  type}
              </option>
            ))}
          </select>
        </div>

        {/* Statistics */}
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
          <span>📊 {messageStats.total} total</span>
          {messageStats.avgConfidence > 0 && (
            <span>
              🎯 {(messageStats.avgConfidence * 100).toFixed(1)}% avg confidence
            </span>
          )}
          <span>🔄 {messageStats.byType.length} message types</span>
        </div>
      </CardHeader>

      <CardContent>
        {filteredMessages.length === 0 ? (
          <div className="text-center text-slate-400 py-8">
            <div className="text-3xl mb-2">💬</div>
            <p>No messages match current filters</p>
            <p className="text-xs mt-2">
              Adjust filters or wait for agent communications
            </p>
          </div>
        ) : (
          <div
            ref={messagesRef}
            className="space-y-3 max-h-96 overflow-y-auto pr-2"
          >
            {filteredMessages.map((message) => (
              <MessageItem
                key={message.id}
                message={message}
                onClick={onMessageClick}
              />
            ))}
          </div>
        )}

        {/* Message Type Legend */}
        {messages.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-600">
            <h5 className="text-xs font-semibold text-slate-300 mb-2">
              Message Types
            </h5>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {Object.entries(MESSAGE_TYPES).map(([type, info]) => (
                <Tooltip key={type} content={info.description}>
                  <div className="flex items-center gap-2 text-xs p-2 rounded bg-slate-800/30">
                    <span>{info.icon}</span>
                    <span className="text-slate-300">{info.label}</span>
                  </div>
                </Tooltip>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
