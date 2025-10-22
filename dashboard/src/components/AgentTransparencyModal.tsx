/**
 * Agent Transparency Modal Component
 *
 * Displays detailed agent reasoning, confidence breakdown, and RAG sources
 * when an agent card is clicked on the operations dashboard.
 */

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared";
import { Progress } from "@/components/shared";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface RagSource {
  type: "incident" | "knowledge" | "runbook";
  id: string;
  title: string;
  similarity: number;
  summary: string;
  resolution_time?: number;
  success_rate?: number;
  last_updated?: string;
}

interface AgentTransparencyData {
  agent_name: string;
  agent_type: string;
  current_confidence: number;
  status: "idle" | "analyzing" | "complete" | "error";

  // Reasoning
  reasoning_summary?: string;
  reasoning_factors?: string[];
  evidence_sources?: string[];

  // Confidence breakdown
  confidence_components?: {
    data_quality: number;
    pattern_match: number;
    historical_accuracy: number;
    cross_validation: number;
  };

  // Uncertainties
  uncertainty_factors?: string[];
  risk_assessment?: string;

  // RAG Sources (Amazon Titan Embeddings)
  rag_sources?: RagSource[];

  // AWS Service Integration
  aws_services_used?: string[];

  // Guardrails
  guardrail_checks?: {
    name: string;
    status: "passed" | "failed" | "warning";
    details: string;
  }[];
}

interface AgentTransparencyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentData: AgentTransparencyData | null;
}

export function AgentTransparencyModal({
  open,
  onOpenChange,
  agentData,
}: AgentTransparencyModalProps) {
  if (!agentData) return null;

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

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      idle: { variant: "secondary", label: "Idle" },
      analyzing: { variant: "default", label: "Analyzing" },
      complete: { variant: "default", label: "Complete" },
      error: { variant: "destructive", label: "Error" },
    };
    const config = variants[status] || variants.idle;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-2xl">
            <span className="text-3xl">{getAgentIcon(agentData.agent_type)}</span>
            <span>{agentData.agent_name}</span>
            {getStatusBadge(agentData.status)}
          </DialogTitle>
          <DialogDescription>
            Complete AI transparency with explainable reasoning, confidence breakdown, and evidence sources
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-between py-4">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Confidence</p>
              <p className="text-3xl font-semibold text-green-500">
                {Math.round(agentData.current_confidence * 100)}%
              </p>
            </div>
            <Separator orientation="vertical" className="h-12" />
            <div>
              <p className="text-sm text-muted-foreground">AWS Services</p>
              <div className="flex gap-2 mt-1">
                {agentData.aws_services_used?.slice(0, 3).map((service) => (
                  <Badge key={service} variant="outline" className="text-xs">
                    {service}
                  </Badge>
                )) || <span className="text-xs text-muted-foreground">N/A</span>}
              </div>
            </div>
          </div>

          {/* Bedrock Guardrails Trust Indicator */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <span className="text-green-500">🛡️</span>
                  <span className="text-sm font-medium">Verified Safe</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="left" className="max-w-xs">
                <p className="font-semibold mb-2">AWS Bedrock Guardrails</p>
                {agentData.guardrail_checks?.map((check) => (
                  <div key={check.name} className="flex items-start gap-2 mb-1">
                    <span className={check.status === "passed" ? "text-green-500" : "text-yellow-500"}>
                      {check.status === "passed" ? "✓" : "⚠"}
                    </span>
                    <div>
                      <p className="text-xs font-medium">{check.name}</p>
                      <p className="text-xs text-muted-foreground">{check.details}</p>
                    </div>
                  </div>
                )) || <p className="text-xs">No guardrail data</p>}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <Tabs defaultValue="reasoning" className="flex-1 overflow-hidden flex flex-col">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="reasoning">🧠 Reasoning</TabsTrigger>
            <TabsTrigger value="confidence">📊 Confidence</TabsTrigger>
            <TabsTrigger value="evidence">🔬 Evidence</TabsTrigger>
            <TabsTrigger value="guardrails">🛡️ Safety</TabsTrigger>
          </TabsList>

          <ScrollArea className="flex-1 mt-4">
            <TabsContent value="reasoning" className="mt-0 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Analysis Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground leading-relaxed">
                    {agentData.reasoning_summary || "No reasoning summary available"}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Key Reasoning Factors</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {agentData.reasoning_factors?.map((factor, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <span className="text-blue-500 mt-1">•</span>
                      <span className="text-sm">{factor}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {(agentData.uncertainty_factors?.length || 0) > 0 && (
                <Card className="border-yellow-500/20 bg-yellow-500/5">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <span>⚠️</span> Uncertainties & Risks
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-sm font-medium mb-2">Risk Assessment:</p>
                      <p className="text-sm text-muted-foreground">{agentData.risk_assessment || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-2">Uncertainty Factors:</p>
                      <ul className="space-y-1">
                        {agentData.uncertainty_factors?.map((factor, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm">
                            <span className="text-yellow-500">▸</span>
                            <span>{factor}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="confidence" className="mt-0 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Confidence Breakdown</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    How we calculated {Math.round(agentData.current_confidence * 100)}% confidence
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  {agentData.confidence_components ? Object.entries(agentData.confidence_components).map(([key, value]) => (
                    <div key={key}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium capitalize">
                          {key.replace(/_/g, " ")}
                        </span>
                        <span className="text-sm font-bold">{Math.round(value * 100)}%</span>
                      </div>
                      <Progress value={value * 100} className="h-2" />
                    </div>
                  )) : <p className="text-sm text-muted-foreground">No confidence breakdown available</p>}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Overall Confidence</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Progress value={agentData.current_confidence * 100} className="h-4" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Low</span>
                      <span>Medium</span>
                      <span>High</span>
                    </div>
                  </div>
                  <div className="mt-4 p-3 bg-muted rounded-lg">
                    <p className="text-sm">
                      {agentData.current_confidence >= 0.9
                        ? "🟢 Very high confidence - Strong evidence and agreement across all factors"
                        : agentData.current_confidence >= 0.75
                        ? "🟡 Good confidence - Sufficient evidence with minor uncertainties"
                        : "🔴 Moderate confidence - Requires additional validation"}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="evidence" className="mt-0 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <span>🧠</span> Evidence Sources (Amazon Titan Embeddings)
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Analysis based on {agentData.rag_sources?.length || 0} similar cases from historical data
                  </p>
                </CardHeader>
                <CardContent>
                  {agentData.rag_sources && agentData.rag_sources.length > 0 ? (
                    <div className="space-y-3">
                      {agentData.rag_sources.map((source) => (
                        <div
                          key={source.id}
                          className="spacing-md border rounded-lg hover:border-blue-500/50 transition-colors"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">
                                {source.type === "incident" ? "📊" : source.type === "runbook" ? "📚" : "💡"}
                              </span>
                              <div>
                                <p className="font-medium text-sm">{source.title}</p>
                                <p className="text-xs text-muted-foreground">{source.id}</p>
                              </div>
                            </div>
                            <Badge variant="secondary" className="ml-2">
                              {Math.round(source.similarity * 100)}% match
                            </Badge>
                          </div>

                          <p className="text-sm text-muted-foreground mb-2">{source.summary}</p>

                          {source.resolution_time && (
                            <div className="flex gap-4 text-xs">
                              <span className="text-green-500">
                                ✓ Resolved in {source.resolution_time}min
                              </span>
                              {source.success_rate && (
                                <span className="text-blue-500">
                                  {Math.round(source.success_rate * 100)}% success rate
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>🤔 No similar historical incidents found</p>
                      <p className="text-sm mt-2">This appears to be a novel incident pattern</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Data Sources Analyzed</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {agentData.evidence_sources?.map((source, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <span className="text-blue-500">▸</span>
                      <span className="text-sm">{source}</span>
                    </div>
                  )) || <p className="text-sm text-muted-foreground">No evidence sources available</p>}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="guardrails" className="mt-0 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <span>🛡️</span> AWS Bedrock Guardrails
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    All agent actions verified for safety and compliance
                  </p>
                </CardHeader>
                <CardContent className="space-y-3">
                  {agentData.guardrail_checks?.map((check, index) => (
                    <div
                      key={index}
                      className={`p-3 border rounded-lg ${
                        check.status === "passed"
                          ? "border-green-500/20 bg-green-500/5"
                          : check.status === "warning"
                          ? "border-yellow-500/20 bg-yellow-500/5"
                          : "border-red-500/20 bg-red-500/5"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-xl">
                          {check.status === "passed" ? "✅" : check.status === "warning" ? "⚠️" : "❌"}
                        </span>
                        <div className="flex-1">
                          <p className="font-medium text-sm">{check.name}</p>
                          <p className="text-sm text-muted-foreground mt-1">{check.details}</p>
                        </div>
                      </div>
                    </div>
                  )) || <p className="text-sm text-muted-foreground">No guardrail checks available</p>}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">AWS Services Integration</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2">
                    {agentData.aws_services_used?.map((service) => (
                      <div key={service} className="flex items-center gap-2 p-2 border rounded">
                        <span className="text-orange-500">🔶</span>
                        <span className="text-sm font-medium">{service}</span>
                      </div>
                    )) || <p className="text-sm text-muted-foreground">No AWS services data available</p>}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </ScrollArea>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
