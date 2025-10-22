/**
 * Enhanced Operations Dashboard
 *
 * Production-ready dashboard with advanced UX features:
 * - Clickable agent cards that open transparency modals
 * - Byzantine consensus visualization
 * - Trust indicators showing security features
 * - RAG sources display
 */

"use client";

import React, { useState, useCallback } from "react";
import { RefinedDashboard } from "./RefinedDashboard";
import { AgentTransparencyModal } from "./AgentTransparencyModal";
import { ByzantineConsensusVisualization } from "./ByzantineConsensusVisualization";
import { TrustIndicatorsGroup } from "./TrustIndicators";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Example data types (should match your backend schema)
interface AgentConfidenceData {
  agent_name: string;
  agent_type: string;
  current_confidence: number;
  status: "idle" | "analyzing" | "complete" | "error";
  reasoning_summary?: string;
  reasoning_factors?: string[];
  evidence_sources?: string[];
  uncertainty_factors?: string[];
  risk_assessment?: string;
  confidence_components?: {
    data_quality: number;
    pattern_match: number;
    historical_accuracy: number;
    cross_validation: number;
  };
  rag_sources?: Array<{
    type: "incident" | "knowledge" | "runbook";
    id: string;
    title: string;
    similarity: number;
    summary: string;
    resolution_time?: number;
    success_rate?: number;
  }>;
  aws_services_used?: string[];
  guardrail_checks?: Array<{
    name: string;
    status: "passed" | "failed" | "warning";
    details: string;
  }>;
}

interface ConsensusData {
  agents: Array<{
    agent_type: string;
    agent_name: string;
    confidence: number;
    weight: number;
    status: "voting" | "agreed" | "abstained" | "error" | "informational";
    reasoning_summary?: string;
  }>;
  weighted_consensus: number;
  consensus_threshold: number;
  consensus_reached: boolean;
  decision: "pending" | "approved" | "rejected";
  timestamp: Date;
}

/**
 * Enhanced Agent Card Component
 * Shows agent confidence with click-to-view-details functionality
 */
interface EnhancedAgentCardProps {
  agent: {
    agent_name: string;
    agent_type: string;
    current_confidence: number;
    status: string;
  };
  onClick: () => void;
}

function EnhancedAgentCard({ agent, onClick }: EnhancedAgentCardProps) {
  const getAgentIcon = (type: string) => {
    const icons: Record<string, string> = {
      detection: "🔍",
      diagnosis: "🔬",
      prediction: "🔮",
      resolution: "⚙️",
      communication: "📢",
    };
    return icons[type.toLowerCase()] || "🤖";
  };

  return (
    <Card
      className="cursor-pointer hover:border-blue-500/50 transition-all hover:shadow-lg"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <span className="text-2xl">{getAgentIcon(agent.agent_type)}</span>
          <span>{agent.agent_name}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Confidence</span>
            <span className="text-lg font-bold text-green-500">
              {Math.round(agent.current_confidence * 100)}%
            </span>
          </div>
          <div className="text-xs text-muted-foreground hover:text-foreground transition-colors">
            Click for detailed reasoning →
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Main Enhanced Dashboard Component
 */
export function EnhancedOperationsDashboard() {
  const [selectedAgent, setSelectedAgent] = useState<AgentConfidenceData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Sample agent data (replace with real WebSocket data)
  const getSampleAgentData = useCallback((agentType: string): AgentConfidenceData => {
    const agentDataMap: Record<string, AgentConfidenceData> = {
      detection: {
        agent_name: "Detection Agent",
        agent_type: "detection",
        current_confidence: 0.93,
        status: "complete",
        reasoning_summary:
          "Identified anomaly correlation across 143 telemetry signals from CloudWatch, Datadog, and Prometheus. Pattern matches historical database connection pool exhaustion with 94% confidence.",
        reasoning_factors: [
          "Anomaly correlation across 143 telemetry signals",
          "Baseline drift within acceptable 0.6% threshold",
          "Pattern match: Database connection pool exhaustion (94% confidence)",
          "Historical matches: 12 similar incidents in past 90 days",
        ],
        evidence_sources: ["CloudWatch Metrics", "Datadog APM", "Prometheus", "Custom Telemetry"],
        uncertainty_factors: ["Synthetic monitors degraded in parallel region"],
        risk_assessment: "Low risk - pattern is well-established with high historical accuracy",
        confidence_components: {
          data_quality: 0.96,
          pattern_match: 0.94,
          historical_accuracy: 0.91,
          cross_validation: 0.89,
        },
        rag_sources: [
          {
            type: "incident",
            id: "INC-4512",
            title: "Database Connection Pool Exhaustion - Production",
            similarity: 0.94,
            summary: "Similar cascade failure in production. Root cause: Connection pool limit + retry storm",
            resolution_time: 2.1,
            success_rate: 1.0,
          },
          {
            type: "incident",
            id: "INC-3891",
            title: "API Gateway Timeout Cascade",
            similarity: 0.89,
            summary: "Connection pool exhaustion leading to timeout cascade. Resolved by scaling pool and circuit breakers",
            resolution_time: 1.8,
            success_rate: 1.0,
          },
          {
            type: "runbook",
            id: "RB-Database-007",
            title: "Database Cascade Failure Response v2.3",
            similarity: 0.86,
            summary: "Standard operating procedure for database connection issues",
            success_rate: 0.98,
          },
        ],
        aws_services_used: ["Claude 3.5 Sonnet", "Amazon CloudWatch", "Bedrock AgentCore"],
        guardrail_checks: [
          {
            name: "Command Safety Check",
            status: "passed",
            details: "No destructive commands detected in analysis",
          },
          {
            name: "Rate Limit Compliance",
            status: "passed",
            details: "API calls within configured limits",
          },
          {
            name: "Data Access Authorization",
            status: "passed",
            details: "All data sources authorized for this agent",
          },
        ],
      },
      diagnosis: {
        agent_name: "Diagnosis Agent",
        agent_type: "diagnosis",
        current_confidence: 0.97,
        status: "complete",
        reasoning_summary:
          "Root cause identified via Bedrock AgentCore analysis of 15,000 log entries. Query plan regression detected causing lock wait accumulation beyond latency SLO.",
        reasoning_factors: [
          "Query plan regression detected via Bedrock AgentCore",
          "Lock wait accumulation beyond latency SLO (500ms → 2.3s)",
          "N+1 query pattern in auth service endpoints",
          "Database connection pool at 98% utilization",
        ],
        evidence_sources: [
          "Application Logs (15,247 entries)",
          "Database Query Logs",
          "APM Traces",
          "Error Tracking System",
        ],
        uncertainty_factors: ["Pending guardrail confirmation on proposed query optimization"],
        risk_assessment: "Very low - diagnosis confirmed by multiple independent data sources",
        confidence_components: {
          data_quality: 0.98,
          pattern_match: 0.97,
          historical_accuracy: 0.96,
          cross_validation: 0.97,
        },
        rag_sources: [
          {
            type: "incident",
            id: "INC-4512",
            title: "Database Connection Pool Exhaustion",
            similarity: 0.94,
            summary: "Same root cause identified - query plan regression + connection pool limits",
            resolution_time: 2.1,
          },
          {
            type: "knowledge",
            id: "KB-SQL-042",
            title: "Query Plan Regression Patterns",
            similarity: 0.91,
            summary: "Common causes and detection methods for query plan degradation",
          },
        ],
        aws_services_used: ["Bedrock AgentCore", "Amazon Q Business", "OpenSearch"],
        guardrail_checks: [
          {
            name: "PII Detection",
            status: "passed",
            details: "No PII found in analyzed logs",
          },
          {
            name: "Data Retention Compliance",
            status: "passed",
            details: "All accessed data within retention policies",
          },
        ],
      },
      prediction: {
        agent_name: "Prediction Agent",
        agent_type: "prediction",
        current_confidence: 0.73,
        status: "complete",
        reasoning_summary:
          "Nova Act mitigation planner evaluating 3 rollout paths. Titan embeddings show 73% cascade probability if left unresolved for 15 minutes. Predicting impact on 25,000 concurrent users.",
        reasoning_factors: [
          "Nova Act mitigation planner evaluating 3 rollout paths",
          "Titan embeddings similarity: 73% cascade risk within 15 minutes",
          "Projected user impact: 25,000 concurrent users",
          "Revenue at risk: $168,000 based on historical downtime costs",
        ],
        evidence_sources: [
          "Historical Incident Database",
          "User Session Analytics",
          "Revenue Impact Models",
          "Cascade Simulation",
        ],
        uncertainty_factors: [
          "Pending customer impact projection",
          "External service dependencies not fully modeled",
          "Traffic patterns may vary from historical baseline",
        ],
        risk_assessment:
          "Moderate uncertainty - prediction based on historical patterns but current traffic differs from baseline",
        confidence_components: {
          data_quality: 0.82,
          pattern_match: 0.73,
          historical_accuracy: 0.78,
          cross_validation: 0.61,
        },
        rag_sources: [
          {
            type: "incident",
            id: "INC-2147",
            title: "Cascade Failure Prevention",
            similarity: 0.86,
            summary: "Circuit breakers prevented cascade. Lesson: Act within 15-minute window",
            resolution_time: 3.2,
            success_rate: 1.0,
          },
        ],
        aws_services_used: ["Nova Act", "Amazon Titan Embeddings", "Amazon Forecast"],
        guardrail_checks: [
          {
            name: "Prediction Bounds",
            status: "passed",
            details: "Predictions within validated confidence intervals",
          },
        ],
      },
      resolution: {
        agent_name: "Resolution Agent",
        agent_type: "resolution",
        current_confidence: 0.95,
        status: "complete",
        reasoning_summary:
          "Autonomous remediation plan validated with 5-step rollback capability. Circuit breaker thresholds validated. Canary rollback progressing within guardrails.",
        reasoning_factors: [
          "Circuit breaker thresholds validated",
          "Canary rollback progressing within guardrails",
          "5-step remediation plan with full rollback capability",
          "Similar actions successful in 12/12 historical incidents",
        ],
        evidence_sources: [
          "Remediation Playbooks",
          "Historical Success Rates",
          "Infrastructure State",
          "Safety Validations",
        ],
        uncertainty_factors: ["Awaiting full traffic restoration validation"],
        risk_assessment: "Very low - all safety checks passed, rollback plan verified",
        confidence_components: {
          data_quality: 0.97,
          pattern_match: 0.95,
          historical_accuracy: 1.0,
          cross_validation: 0.92,
        },
        aws_services_used: ["Strands SDK", "AWS Systems Manager", "Bedrock Guardrails"],
        guardrail_checks: [
          {
            name: "Backup Verification",
            status: "passed",
            details: "Database backup confirmed before changes",
          },
          {
            name: "Rollback Plan",
            status: "passed",
            details: "5-step rollback validated and ready",
          },
          {
            name: "Impact Assessment",
            status: "passed",
            details: "Predicted impact within acceptable bounds",
          },
        ],
      },
      communication: {
        agent_name: "Communication Agent",
        agent_type: "communication",
        current_confidence: 0.88,
        status: "complete",
        reasoning_summary:
          "Stakeholder updates synchronized across Slack and email. Executive briefing drafted via Amazon Q. All notifications comply with communication policies.",
        reasoning_factors: [
          "Stakeholder updates synchronized across Slack and email",
          "Executive briefing drafted via Amazon Q",
          "Communication timeline aligned with incident phases",
          "Notification recipients validated against on-call schedule",
        ],
        evidence_sources: [
          "On-Call Schedule",
          "Communication Templates",
          "Notification History",
          "Stakeholder Registry",
        ],
        uncertainty_factors: ["Pending executive acknowledgement"],
        risk_assessment: "Low - standard communication protocols followed",
        confidence_components: {
          data_quality: 0.91,
          pattern_match: 0.88,
          historical_accuracy: 0.85,
          cross_validation: 0.87,
        },
        aws_services_used: ["Amazon Q Business", "Amazon SNS", "Amazon SES"],
        guardrail_checks: [
          {
            name: "PII Redaction",
            status: "passed",
            details: "All PII removed from notifications",
          },
          {
            name: "Compliance Check",
            status: "passed",
            details: "Communications meet regulatory requirements",
          },
        ],
      },
    };

    return agentDataMap[agentType] || agentDataMap.detection;
  }, []);

  // Sample consensus data (replace with real WebSocket data)
  const sampleConsensus: ConsensusData = {
    agents: [
      {
        agent_type: "detection",
        agent_name: "Detection Agent",
        confidence: 0.93,
        weight: 0.2,
        status: "agreed",
        reasoning_summary: "Anomaly correlation across 143 telemetry signals",
      },
      {
        agent_type: "diagnosis",
        agent_name: "Diagnosis Agent",
        confidence: 0.97,
        weight: 0.4,
        status: "agreed",
        reasoning_summary: "Root cause identified via Bedrock AgentCore",
      },
      {
        agent_type: "prediction",
        agent_name: "Prediction Agent",
        confidence: 0.73,
        weight: 0.3,
        status: "voting",
        reasoning_summary: "Nova Act evaluating cascade probability",
      },
      {
        agent_type: "resolution",
        agent_name: "Resolution Agent",
        confidence: 0.95,
        weight: 0.1,
        status: "agreed",
        reasoning_summary: "Remediation plan validated",
      },
      {
        agent_type: "communication",
        agent_name: "Communication Agent",
        confidence: 0.88,
        weight: 0,
        status: "informational",
        reasoning_summary: "Stakeholder notifications ready (non-voting)",
      },
    ],
    weighted_consensus: 0.888,
    consensus_threshold: 0.85,
    consensus_reached: true,
    decision: "approved",
    timestamp: new Date(),
  };

  const handleAgentClick = useCallback((agentType: string) => {
    const agentData = getSampleAgentData(agentType);
    setSelectedAgent(agentData);
    setIsModalOpen(true);
  }, [getSampleAgentData]);

  return (
    <div className="space-y-6">
      {/* Trust Indicators Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">System Trust & Security</CardTitle>
            <Badge variant="default" className="bg-green-500">
              All Systems Verified
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <TrustIndicatorsGroup
            guardrails={[
              { name: "Safety Verification", status: "passed", details: "All operations within safety bounds" },
              { name: "Rate Limits", status: "passed", details: "API usage within limits" },
            ]}
            pii={["IP addresses", "User IDs", "Email addresses"]}
            circuitBreaker={{ status: "closed" }}
            rollback={{ available: true, steps: 5 }}
            rag={{ sourcesCount: 3, avgSimilarity: 0.89 }}
          />
        </CardContent>
      </Card>

      {/* Byzantine Consensus Visualization */}
      <ByzantineConsensusVisualization consensusState={sampleConsensus} showDetails={true} />

      {/* Enhanced Agent Cards (clickable) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">AI Agent Confidence Levels</CardTitle>
          <p className="text-sm text-muted-foreground">Click any agent to view detailed reasoning and evidence</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {sampleConsensus.agents.map((agent) => (
              <EnhancedAgentCard
                key={agent.agent_type}
                agent={{
                  agent_name: agent.agent_name,
                  agent_type: agent.agent_type,
                  current_confidence: agent.confidence,
                  status: "complete",
                }}
                onClick={() => handleAgentClick(agent.agent_type)}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Original RefinedDashboard (for other sections) */}
      <RefinedDashboard />

      {/* Agent Transparency Modal */}
      <AgentTransparencyModal open={isModalOpen} onOpenChange={setIsModalOpen} agentData={selectedAgent} />
    </div>
  );
}
