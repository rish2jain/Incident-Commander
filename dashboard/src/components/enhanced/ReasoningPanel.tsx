/**
 * Enhanced Reasoning Panel Component
 *
 * Implements improved readability with collapsible sections, step-by-step flow,
 * and better visual hierarchy for agent reasoning processes.
 */

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { Tooltip } from "./InteractiveMetrics";

interface ReasoningStep {
  id: string;
  timestamp: string;
  agent: string;
  step: string;
  message: string;
  confidence: number;
  reasoning: string;
  explanation?: string;
  evidence?: string[];
  alternatives?: Array<{
    option: string;
    probability: number;
    chosen: boolean;
    reasoning?: string;
  }>;
  riskAssessment?: number;
  processingTime?: number;
  keyInsights?: string[];
  nextSteps?: string[];
}

interface ReasoningPanelProps {
  reasoningSteps: ReasoningStep[];
  onStepClick?: (step: ReasoningStep) => void;
  className?: string;
}

// Individual Reasoning Step Component
interface ReasoningStepComponentProps {
  step: ReasoningStep;
  stepNumber: number;
  isLast: boolean;
  onClick?: (step: ReasoningStep) => void;
}

function ReasoningStepComponent({
  step,
  stepNumber,
  isLast,
  onClick,
}: ReasoningStepComponentProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getAgentIcon = (agent: string) => {
    const icons: Record<string, string> = {
      Detection: "🔍",
      Diagnosis: "🔬",
      Prediction: "🔮",
      Resolution: "⚙️",
      Communication: "📢",
    };
    return icons[agent] || "🤖";
  };

  const getAgentColor = (agent: string) => {
    const colors: Record<string, string> = {
      Detection: "text-green-400 bg-green-500/10 border-green-500/30",
      Diagnosis: "text-blue-400 bg-blue-500/10 border-blue-500/30",
      Prediction: "text-purple-400 bg-purple-500/10 border-purple-500/30",
      Resolution: "text-orange-400 bg-orange-500/10 border-orange-500/30",
      Communication: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
    };
    return (
      colors[agent] || "text-slate-400 bg-slate-500/10 border-slate-500/30"
    );
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-400";
    if (confidence >= 0.6) return "text-yellow-400";
    if (confidence >= 0.4) return "text-orange-400";
    return "text-red-400";
  };

  const getRiskColor = (risk?: number) => {
    if (!risk) return "text-slate-400";
    if (risk >= 0.7) return "text-red-400";
    if (risk >= 0.4) return "text-yellow-400";
    return "text-green-400";
  };

  return (
    <div className="relative">
      {/* Timeline connector */}
      {!isLast && (
        <div className="absolute left-6 top-16 w-0.5 h-full bg-slate-600 z-0" />
      )}

      <div
        className={cn(
          "relative bg-slate-800/30 border border-slate-600 rounded-lg p-4 cursor-pointer transition-all duration-300",
          "hover:border-slate-500 hover:bg-slate-800/50",
          isExpanded && "ring-2 ring-blue-500/30 border-blue-500/50"
        )}
        onClick={() => {
          setIsExpanded(!isExpanded);
          onClick?.(step);
        }}
      >
        {/* Step Header */}
        <div className="flex items-start gap-4 mb-3">
          {/* Step Number & Agent Icon */}
          <div className="flex flex-col items-center gap-2 flex-shrink-0">
            <div
              className={cn(
                "w-12 h-12 rounded-full border-2 flex items-center justify-center text-lg font-bold z-10 bg-slate-800",
                getAgentColor(step.agent)
              )}
            >
              {getAgentIcon(step.agent)}
            </div>
            <Badge variant="outline" className="text-xs">
              Step {stepNumber}
            </Badge>
          </div>

          {/* Step Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-white text-lg mb-1">
                  {step.step}
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  {step.explanation || step.reasoning}
                </p>
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 ml-2 flex-shrink-0"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
              >
                {isExpanded ? "−" : "+"}
              </Button>
            </div>

            {/* Metrics Row */}
            <div className="flex items-center gap-4 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Confidence:</span>
                <div className="flex items-center gap-2">
                  <Progress
                    value={step.confidence * 100}
                    className="w-16 h-1.5"
                  />
                  <span
                    className={cn(
                      "text-sm font-mono font-bold",
                      getConfidenceColor(step.confidence)
                    )}
                  >
                    {(step.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {step.riskAssessment !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Risk:</span>
                  <span
                    className={cn(
                      "text-sm font-medium",
                      getRiskColor(step.riskAssessment)
                    )}
                  >
                    {(step.riskAssessment * 100).toFixed(1)}%
                  </span>
                </div>
              )}

              {step.processingTime && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Time:</span>
                  <span className="text-sm font-mono text-white">
                    {step.processingTime}ms
                  </span>
                </div>
              )}
            </div>

            {/* Timestamp */}
            <div className="text-xs text-slate-500">⏰ {step.timestamp}</div>
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="ml-16 space-y-4 animate-slide-up">
            {/* Detailed Reasoning */}
            <div className="bg-slate-700/30 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
                🧠 Detailed Reasoning
              </h4>
              <p className="text-sm text-slate-300 leading-relaxed">
                {step.reasoning}
              </p>
            </div>

            {/* Evidence */}
            {step.evidence && step.evidence.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  🔍 Supporting Evidence
                </h4>
                <div className="space-y-2">
                  {step.evidence.map((evidence, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg"
                    >
                      <span className="text-blue-400 mt-0.5 flex-shrink-0">
                        •
                      </span>
                      <span className="text-sm text-slate-200 leading-relaxed">
                        {evidence}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Alternatives Considered */}
            {step.alternatives && step.alternatives.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  🔀 Alternatives Considered
                </h4>
                <div className="space-y-2">
                  {step.alternatives.map((alt, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        "p-3 rounded-lg border transition-all",
                        alt.chosen
                          ? "bg-green-500/20 border-green-500/40 text-green-100"
                          : "bg-slate-700/30 border-slate-600 text-slate-300"
                      )}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-medium text-sm">
                          {alt.option}
                        </span>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={alt.chosen ? "default" : "secondary"}
                            className="text-xs"
                          >
                            {(alt.probability * 100).toFixed(0)}%
                          </Badge>
                          {alt.chosen && (
                            <span className="text-green-400 text-sm">
                              ✓ Selected
                            </span>
                          )}
                        </div>
                      </div>
                      {alt.reasoning && (
                        <p className="text-xs opacity-80 leading-relaxed">
                          {alt.reasoning}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Insights */}
            {step.keyInsights && step.keyInsights.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  💡 Key Insights
                </h4>
                <div className="space-y-2">
                  {step.keyInsights.map((insight, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg"
                    >
                      <span className="text-yellow-400 mt-0.5 flex-shrink-0">
                        💡
                      </span>
                      <span className="text-sm text-slate-200 leading-relaxed">
                        {insight}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Next Steps */}
            {step.nextSteps && step.nextSteps.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  ➡️ Next Steps
                </h4>
                <div className="space-y-2">
                  {step.nextSteps.map((nextStep, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg"
                    >
                      <span className="text-purple-400 mt-0.5 flex-shrink-0">
                        {idx + 1}.
                      </span>
                      <span className="text-sm text-slate-200 leading-relaxed">
                        {nextStep}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Main Reasoning Panel Component
export function ReasoningPanel({
  reasoningSteps,
  onStepClick,
  className,
}: ReasoningPanelProps) {
  const [expandAll, setExpandAll] = useState(false);
  const [filterAgent, setFilterAgent] = useState<string>("all");

  // Filter steps by agent
  const filteredSteps = reasoningSteps.filter(
    (step) => filterAgent === "all" || step.agent === filterAgent
  );

  // Get unique agents
  const uniqueAgents = Array.from(
    new Set(reasoningSteps.map((step) => step.agent))
  ).sort();

  // Calculate reasoning statistics
  const stats = {
    totalSteps: reasoningSteps.length,
    avgConfidence:
      reasoningSteps.length > 0
        ? reasoningSteps.reduce((sum, step) => sum + step.confidence, 0) /
          reasoningSteps.length
        : 0,
    highConfidenceSteps: reasoningSteps.filter((step) => step.confidence >= 0.8)
      .length,
    agentDistribution: uniqueAgents.map((agent) => ({
      agent,
      count: reasoningSteps.filter((step) => step.agent === agent).length,
    })),
  };

  return (
    <Card className={cn("card-glass", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            🧠 Agent Reasoning Process
            <Badge variant="secondary" className="text-xs">
              {filteredSteps.length} / {reasoningSteps.length} steps
            </Badge>
          </CardTitle>

          <div className="flex items-center gap-3">
            {/* Agent Filter */}
            <select
              value={filterAgent}
              onChange={(e) => setFilterAgent(e.target.value)}
              className="h-8 px-2 text-sm bg-slate-700 border border-slate-600 rounded"
            >
              <option value="all">All Agents</option>
              {uniqueAgents.map((agent) => (
                <option key={agent} value={agent}>
                  {agent}
                </option>
              ))}
            </select>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpandAll(!expandAll)}
              className="text-xs"
            >
              {expandAll ? "Collapse All" : "Expand All"}
            </Button>
          </div>
        </div>

        {/* Statistics */}
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
          <Tooltip content="Total reasoning steps completed">
            <span>📊 {stats.totalSteps} steps</span>
          </Tooltip>
          <Tooltip content="Average confidence across all reasoning steps">
            <span>
              🎯 {(stats.avgConfidence * 100).toFixed(1)}% avg confidence
            </span>
          </Tooltip>
          <Tooltip content="Steps with high confidence (≥80%)">
            <span>⭐ {stats.highConfidenceSteps} high confidence</span>
          </Tooltip>
          <Tooltip content="Number of different agents involved">
            <span>🤖 {uniqueAgents.length} agents</span>
          </Tooltip>
        </div>
      </CardHeader>

      <CardContent>
        {filteredSteps.length === 0 ? (
          <div className="text-center text-slate-400 py-12">
            <div className="text-4xl mb-3">🤔</div>
            <h3 className="text-lg font-medium mb-2">No Reasoning Steps Yet</h3>
            <p className="text-sm">
              Trigger an incident to see live AI reasoning processes
            </p>
            <p className="text-xs mt-2 text-slate-500">
              Agent reasoning will appear here with detailed step-by-step
              analysis
            </p>
          </div>
        ) : (
          <div className="space-y-6 max-h-96 overflow-y-auto pr-2">
            {filteredSteps.map((step, index) => (
              <ReasoningStepComponent
                key={step.id}
                step={step}
                stepNumber={index + 1}
                isLast={index === filteredSteps.length - 1}
                onClick={onStepClick}
              />
            ))}
          </div>
        )}

        {/* Agent Distribution Summary */}
        {reasoningSteps.length > 0 && (
          <div className="mt-6 pt-4 border-t border-slate-600">
            <h4 className="text-sm font-semibold text-slate-300 mb-3">
              Agent Participation
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {stats.agentDistribution.map(({ agent, count }) => (
                <div
                  key={agent}
                  className="text-center p-2 bg-slate-800/30 rounded-lg"
                >
                  <div className="text-lg mb-1">
                    {agent === "Detection" && "🔍"}
                    {agent === "Diagnosis" && "🔬"}
                    {agent === "Prediction" && "🔮"}
                    {agent === "Resolution" && "⚙️"}
                    {agent === "Communication" && "📢"}
                  </div>
                  <div className="text-xs text-slate-400">{agent}</div>
                  <div className="text-sm font-bold text-white">
                    {count} steps
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
