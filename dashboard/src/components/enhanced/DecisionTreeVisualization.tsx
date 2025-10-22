/**
 * Enhanced Decision Tree Visualization Component
 *
 * Implements interactive, collapsible decision tree with improved UX
 * based on user feedback for better decision flow understanding.
 */

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { Tooltip } from "./InteractiveMetrics";

interface DecisionNode {
  id: string;
  nodeType: "analysis" | "action" | "execution" | "condition";
  label: string;
  confidence: number;
  description?: string;
  evidence?: string[];
  alternatives?: Array<{
    option: string;
    probability: number;
    chosen: boolean;
    reasoning?: string;
  }>;
  children?: DecisionNode[];
  metadata?: {
    executionTime?: number;
    riskLevel?: "low" | "medium" | "high";
    impact?: string;
  };
}

interface DecisionTreeProps {
  rootNode: DecisionNode;
  onNodeClick?: (node: DecisionNode) => void;
  className?: string;
}

// Individual Decision Node Component
interface DecisionNodeComponentProps {
  node: DecisionNode;
  level: number;
  onNodeClick?: (node: DecisionNode) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

function DecisionNodeComponent({
  node,
  level,
  onNodeClick,
  isExpanded = false,
  onToggleExpand,
}: DecisionNodeComponentProps) {
  const [showDetails, setShowDetails] = useState(false);

  const getNodeIcon = (nodeType: string) => {
    const icons = {
      analysis: "🔍",
      action: "⚡",
      execution: "⚙️",
      condition: "❓",
    };
    return icons[nodeType as keyof typeof icons] || "📋";
  };

  const getNodeColor = (nodeType: string) => {
    const colors = {
      analysis: "border-blue-500/50 bg-blue-500/10",
      action: "border-green-500/50 bg-green-500/10",
      execution: "border-orange-500/50 bg-orange-500/10",
      condition: "border-purple-500/50 bg-purple-500/10",
    };
    return (
      colors[nodeType as keyof typeof colors] ||
      "border-slate-500/50 bg-slate-500/10"
    );
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case "high":
        return "text-red-400";
      case "medium":
        return "text-yellow-400";
      case "low":
        return "text-green-400";
      default:
        return "text-slate-400";
    }
  };

  const indentLevel = level * 24;

  return (
    <div className="space-y-3">
      {/* Main Node */}
      <div
        className={cn(
          "relative border rounded-lg p-4 cursor-pointer transition-all duration-300 hover:shadow-lg",
          getNodeColor(node.nodeType),
          showDetails && "ring-2 ring-blue-500/30"
        )}
        style={{ marginLeft: `${indentLevel}px` }}
        onClick={() => {
          setShowDetails(!showDetails);
          onNodeClick?.(node);
        }}
      >
        {/* Connection line to parent */}
        {level > 0 && (
          <div
            className="absolute top-1/2 border-t border-slate-600"
            style={{
              left: `-${indentLevel}px`,
              width: `${indentLevel - 8}px`,
              transform: "translateY(-50%)",
            }}
          />
        )}

        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-lg">{getNodeIcon(node.nodeType)}</span>
              <div className="flex-1">
                <h4 className="font-semibold text-white text-sm leading-tight">
                  {node.label}
                </h4>
                {node.description && (
                  <p className="text-xs text-slate-400 mt-1">
                    {node.description}
                  </p>
                )}
              </div>
            </div>

            {/* Confidence and metadata */}
            <div className="flex items-center gap-3 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Confidence:</span>
                <Progress
                  value={node.confidence * 100}
                  className="w-16 h-1.5"
                />
                <span className="text-xs font-mono text-white">
                  {(node.confidence * 100).toFixed(1)}%
                </span>
              </div>

              {node.metadata?.riskLevel && (
                <Badge
                  variant="outline"
                  className={cn(
                    "text-xs",
                    getRiskColor(node.metadata.riskLevel)
                  )}
                >
                  Risk: {node.metadata.riskLevel}
                </Badge>
              )}

              {node.metadata?.executionTime && (
                <Tooltip content="Estimated execution time">
                  <Badge variant="secondary" className="text-xs">
                    ⏱️ {node.metadata.executionTime}s
                  </Badge>
                </Tooltip>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs capitalize">
              {node.nodeType}
            </Badge>
            {(node.children?.length ||
              node.evidence?.length ||
              node.alternatives?.length) && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDetails(!showDetails);
                }}
              >
                {showDetails ? "−" : "+"}
              </Button>
            )}
          </div>
        </div>

        {/* Expanded Details */}
        {showDetails && (
          <div className="mt-4 pt-4 border-t border-slate-600 space-y-3 animate-slide-up">
            {/* Evidence */}
            {node.evidence && node.evidence.length > 0 && (
              <div>
                <h5 className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1">
                  🔍 Evidence
                </h5>
                <div className="space-y-1">
                  {node.evidence.map((evidence, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span className="text-slate-300">{evidence}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Alternatives */}
            {node.alternatives && node.alternatives.length > 0 && (
              <div>
                <h5 className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1">
                  🔀 Alternatives Considered
                </h5>
                <div className="space-y-2">
                  {node.alternatives.map((alt, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        "p-2 rounded text-xs border",
                        alt.chosen
                          ? "bg-green-500/20 border-green-500/30 text-green-100"
                          : "bg-slate-700/30 border-slate-600 text-slate-300"
                      )}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium">{alt.option}</span>
                        <div className="flex items-center gap-1">
                          <span>{(alt.probability * 100).toFixed(0)}%</span>
                          {alt.chosen && (
                            <span className="text-green-400">✓</span>
                          )}
                        </div>
                      </div>
                      {alt.reasoning && (
                        <p className="text-xs opacity-80">{alt.reasoning}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Impact */}
            {node.metadata?.impact && (
              <div>
                <h5 className="text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
                  💥 Expected Impact
                </h5>
                <p className="text-xs text-slate-300">{node.metadata.impact}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Child Nodes */}
      {node.children && node.children.length > 0 && (
        <div className="space-y-3">
          {node.children.map((child) => (
            <DecisionNodeComponent
              key={child.id}
              node={child}
              level={level + 1}
              onNodeClick={onNodeClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Main Decision Tree Visualization Component
export function DecisionTreeVisualization({
  rootNode,
  onNodeClick,
  className,
}: DecisionTreeProps) {
  const [expandAll, setExpandAll] = useState(false);
  const [selectedPath, setSelectedPath] = useState<string[]>([]);

  const handleNodeClick = (node: DecisionNode) => {
    onNodeClick?.(node);

    // Track selected path for highlighting
    setSelectedPath((prev) => {
      if (prev.includes(node.id)) {
        return prev.filter((id) => id !== node.id);
      } else {
        return [...prev, node.id];
      }
    });
  };

  const getTreeStats = (
    node: DecisionNode
  ): { totalNodes: number; maxDepth: number; avgConfidence: number } => {
    let totalNodes = 1;
    let maxDepth = 1;
    let totalConfidence = node.confidence;

    if (node.children) {
      for (const child of node.children) {
        const childStats = getTreeStats(child);
        totalNodes += childStats.totalNodes;
        maxDepth = Math.max(maxDepth, childStats.maxDepth + 1);
        totalConfidence += childStats.totalNodes * childStats.avgConfidence;
      }
    }

    return {
      totalNodes,
      maxDepth,
      avgConfidence: totalConfidence / totalNodes,
    };
  };

  const stats = getTreeStats(rootNode);

  return (
    <Card className={cn("card-glass", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            🌳 Interactive Decision Tree
            <Tooltip content="Click nodes to expand details, trace decision paths">
              <span className="text-sm text-slate-400 cursor-help">ℹ️</span>
            </Tooltip>
          </CardTitle>

          <div className="flex items-center gap-3">
            {/* Tree Statistics */}
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <Tooltip content="Total decision points in tree">
                <span>📊 {stats.totalNodes} nodes</span>
              </Tooltip>
              <Tooltip content="Maximum decision depth">
                <span>📏 {stats.maxDepth} levels</span>
              </Tooltip>
              <Tooltip content="Average confidence across all decisions">
                <span>🎯 {(stats.avgConfidence * 100).toFixed(1)}% avg</span>
              </Tooltip>
            </div>

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
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Legend */}
          <div className="flex items-center gap-4 p-3 bg-slate-800/30 rounded-lg">
            <div className="flex items-center gap-2 text-xs">
              <span>🔍</span>
              <span className="text-slate-400">Analysis</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span>⚡</span>
              <span className="text-slate-400">Action</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span>⚙️</span>
              <span className="text-slate-400">Execution</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span>❓</span>
              <span className="text-slate-400">Condition</span>
            </div>
            <div className="ml-auto text-xs text-slate-500">
              Click nodes to explore • Hover for details
            </div>
          </div>

          {/* Decision Tree */}
          <div className="relative">
            <DecisionNodeComponent
              node={rootNode}
              level={0}
              onNodeClick={handleNodeClick}
            />
          </div>

          {/* Selected Path Summary */}
          {selectedPath.length > 0 && (
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-300 mb-2">
                🎯 Selected Decision Path
              </h4>
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <span>Nodes selected: {selectedPath.length}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedPath([])}
                  className="h-5 px-2 text-xs"
                >
                  Clear
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Enhanced Decision Summary Component
interface DecisionSummaryProps {
  decisions: Array<{
    id: string;
    title: string;
    confidence: number;
    impact: "low" | "medium" | "high";
    status: "pending" | "executing" | "completed" | "failed";
    reasoning: string;
    timestamp: string;
  }>;
  className?: string;
}

export function DecisionSummary({
  decisions,
  className,
}: DecisionSummaryProps) {
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "high":
        return "text-red-400 bg-red-500/10";
      case "medium":
        return "text-yellow-400 bg-yellow-500/10";
      case "low":
        return "text-green-400 bg-green-500/10";
      default:
        return "text-slate-400 bg-slate-500/10";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return "⏳";
      case "executing":
        return "⚡";
      case "completed":
        return "✅";
      case "failed":
        return "❌";
      default:
        return "❓";
    }
  };

  return (
    <Card className={cn("card-glass", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          📋 Decision Summary
          <Badge variant="secondary" className="text-xs">
            {decisions.length} decisions
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-80 overflow-y-auto">
          {decisions.map((decision) => (
            <div
              key={decision.id}
              className="p-3 border border-slate-600 rounded-lg hover:border-slate-500 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{getStatusIcon(decision.status)}</span>
                    <h4 className="font-medium text-white text-sm">
                      {decision.title}
                    </h4>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {decision.reasoning}
                  </p>
                </div>

                <div className="flex flex-col items-end gap-1 ml-3">
                  <Badge
                    variant="outline"
                    className={cn("text-xs", getImpactColor(decision.impact))}
                  >
                    {decision.impact} impact
                  </Badge>
                  <div className="text-xs font-mono text-slate-400">
                    {(decision.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{decision.timestamp}</span>
                <Progress
                  value={decision.confidence * 100}
                  className="w-16 h-1"
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
