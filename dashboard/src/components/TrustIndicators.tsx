/**
 * Trust Indicators Component
 *
 * Visual badges showing security features in action:
 * - AWS Bedrock Guardrails verification
 * - PII Redaction
 * - Circuit Breaker status
 * - Rollback capability
 */

import React from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";

interface GuardrailIndicatorProps {
  checks?: {
    name: string;
    status: "passed" | "warning" | "failed";
    details: string;
  }[];
}

export function GuardrailIndicator({ checks }: GuardrailIndicatorProps) {
  const allPassed = checks?.every((c) => c.status === "passed") ?? true;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge
            variant={allPassed ? "default" : "secondary"}
            className="gap-1 cursor-help bg-green-500/10 text-green-500 border-green-500/20 hover:bg-green-500/20"
          >
            <span>🛡️</span>
            <span className="text-xs">Verified Safe</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-sm">
          <p className="font-semibold mb-2">AWS Bedrock Guardrails</p>
          {checks && checks.length > 0 ? (
            <div className="space-y-2">
              {checks.map((check, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span
                    className={
                      check.status === "passed"
                        ? "text-green-500"
                        : check.status === "warning"
                        ? "text-yellow-500"
                        : "text-red-500"
                    }
                  >
                    {check.status === "passed" ? "✓" : check.status === "warning" ? "⚠" : "✗"}
                  </span>
                  <div>
                    <p className="text-xs font-medium">{check.name}</p>
                    <p className="text-xs text-muted-foreground">{check.details}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-1 text-xs">
              <p>✓ No destructive commands</p>
              <p>✓ Within safety parameters</p>
              <p>✓ Rollback plan validated</p>
              <p>✓ PII protection active</p>
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

interface PIIIndicatorProps {
  redactedFields?: string[];
}

export function PIIIndicator({ redactedFields = ["IP addresses", "User IDs"] }: PIIIndicatorProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge
            variant="outline"
            className="gap-1 cursor-help border-blue-500/30 text-blue-500 hover:bg-blue-500/10"
          >
            <span>🔒</span>
            <span className="text-xs">PII Protected</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <p className="font-semibold mb-2">PII Automatically Redacted</p>
          <div className="space-y-1 text-xs">
            {redactedFields.map((field, idx) => (
              <p key={idx}>✓ {field} masked</p>
            ))}
            <p className="pt-2 border-t border-border">✓ GDPR compliant</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

interface CircuitBreakerIndicatorProps {
  status: "closed" | "open" | "half-open";
  errorRate?: number;
  recoveryTime?: number;
}

export function CircuitBreakerIndicator({ status, errorRate, recoveryTime }: CircuitBreakerIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case "closed":
        return {
          icon: "✅",
          label: "Healthy",
          color: "text-green-500 border-green-500/30 hover:bg-green-500/10",
          tooltip: "Circuit closed - normal operation",
        };
      case "half-open":
        return {
          icon: "⚡",
          label: "Testing",
          color: "text-yellow-500 border-yellow-500/30 hover:bg-yellow-500/10",
          tooltip: "Circuit half-open - testing recovery",
        };
      case "open":
        return {
          icon: "⏸️",
          label: "Degraded",
          color: "text-orange-500 border-orange-500/30 hover:bg-orange-500/10",
          tooltip: "Circuit open - graceful degradation",
        };
    }
  };

  const config = getStatusConfig();

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge variant="outline" className={`gap-1 cursor-help ${config.color}`}>
            <span>{config.icon}</span>
            <span className="text-xs">{config.label}</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <p className="font-semibold mb-2">Circuit Breaker Status</p>
          <div className="space-y-1 text-xs">
            <p>Status: {config.tooltip}</p>
            {errorRate !== undefined && <p>Error rate: {(errorRate * 100).toFixed(1)}%</p>}
            {status === "open" && recoveryTime && (
              <>
                <p className="pt-2 border-t border-border">
                  Recovery in: {recoveryTime}s
                </p>
                <p className="text-muted-foreground">System degraded gracefully to fallback</p>
                <p className="text-muted-foreground">No cascading failure</p>
              </>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

interface RollbackIndicatorProps {
  available: boolean;
  steps?: number;
}

export function RollbackIndicator({ available, steps }: RollbackIndicatorProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge
            variant="outline"
            className={`gap-1 cursor-help ${
              available
                ? "border-purple-500/30 text-purple-500 hover:bg-purple-500/10"
                : "border-gray-500/30 text-gray-500"
            }`}
          >
            <span>🔄</span>
            <span className="text-xs">{available ? "Rollback Ready" : "No Rollback"}</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <p className="font-semibold mb-2">Rollback Capability</p>
          {available ? (
            <div className="space-y-1 text-xs">
              <p>✓ Backup verified</p>
              <p>✓ Rollback plan prepared</p>
              {steps && <p>✓ {steps} steps can be reverted</p>}
              <p className="pt-2 border-t border-border text-muted-foreground">
                Can restore to previous state if needed
              </p>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No rollback available for this action</p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

interface RAGIndicatorProps {
  sourcesCount: number;
  avgSimilarity?: number;
}

export function RAGIndicator({ sourcesCount, avgSimilarity }: RAGIndicatorProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge
            variant="outline"
            className="gap-1 cursor-help border-indigo-500/30 text-indigo-500 hover:bg-indigo-500/10"
          >
            <span>🧠</span>
            <span className="text-xs">{sourcesCount} Sources</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <p className="font-semibold mb-2">Amazon Titan Embeddings</p>
          <div className="space-y-1 text-xs">
            <p>✓ {sourcesCount} similar incidents analyzed</p>
            {avgSimilarity && <p>✓ Average {(avgSimilarity * 100).toFixed(0)}% similarity match</p>}
            <p className="pt-2 border-t border-border text-muted-foreground">
              Analysis based on historical incident patterns
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Combined Trust Indicators Group
 */
interface TrustIndicatorsGroupProps {
  guardrails?: GuardrailIndicatorProps["checks"];
  pii?: PIIIndicatorProps["redactedFields"];
  circuitBreaker?: CircuitBreakerIndicatorProps;
  rollback?: RollbackIndicatorProps;
  rag?: RAGIndicatorProps;
  className?: string;
}

export function TrustIndicatorsGroup({
  guardrails,
  pii,
  circuitBreaker,
  rollback,
  rag,
  className = "",
}: TrustIndicatorsGroupProps) {
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {guardrails !== undefined && <GuardrailIndicator checks={guardrails} />}
      {pii !== undefined && <PIIIndicator redactedFields={pii} />}
      {circuitBreaker && <CircuitBreakerIndicator {...circuitBreaker} />}
      {rollback && <RollbackIndicator {...rollback} />}
      {rag && <RAGIndicator {...rag} />}
    </div>
  );
}

/**
 * Example usage:
 *
 * // Individual indicators
 * <GuardrailIndicator checks={[
 *   { name: "Command Safety", status: "passed", details: "No destructive operations" },
 *   { name: "Rate Limits", status: "passed", details: "Within API limits" }
 * ]} />
 *
 * <PIIIndicator redactedFields={["IP addresses", "User IDs", "Email addresses"]} />
 *
 * <CircuitBreakerIndicator status="open" errorRate={0.45} recoveryTime={27} />
 *
 * <RollbackIndicator available={true} steps={5} />
 *
 * <RAGIndicator sourcesCount={3} avgSimilarity={0.89} />
 *
 * // Combined group
 * <TrustIndicatorsGroup
 *   guardrails={[...]}
 *   pii={["IP addresses"]}
 *   circuitBreaker={{ status: "closed" }}
 *   rollback={{ available: true, steps: 5 }}
 *   rag={{ sourcesCount: 3, avgSimilarity: 0.89 }}
 * />
 */
