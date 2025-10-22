/**
 * Learning Journey Chart
 *
 * Visualizes system improvement over time through cross-incident learning.
 * Shows confidence and success rate growth as incidents are processed.
 *
 * Demonstrates long-term value proposition of the memory-enhanced system.
 */

"use client";

import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, Brain, Award } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared";

interface DataPoint {
  incidents: number;
  confidence: number;
  successRate: number;
}

const LEARNING_DATA: DataPoint[] = [
  { incidents: 0, confidence: 70, successRate: 75 },
  { incidents: 10, confidence: 72.5, successRate: 78 },
  { incidents: 25, confidence: 76, successRate: 83 },
  { incidents: 50, confidence: 81, successRate: 88 },
  { incidents: 100, confidence: 87, successRate: 93 },
  { incidents: 200, confidence: 92, successRate: 96 },
];

export function LearningJourneyChart() {
  // Chart dimensions
  const width = 700;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Scales
  const maxIncidents = Math.max(...LEARNING_DATA.map((d) => d.incidents));
  const xScale = (incidents: number) =>
    padding.left + (incidents / maxIncidents) * chartWidth;

  const yScale = (percentage: number) =>
    padding.top + chartHeight - (percentage / 100) * chartHeight;

  // Generate path for line chart
  const generatePath = (dataKey: "confidence" | "successRate") => {
    return LEARNING_DATA.map((d, i) => {
      const x = xScale(d.incidents);
      const y = yScale(d[dataKey]);
      return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
    }).join(" ");
  };

  const confidencePath = generatePath("confidence");
  const successPath = generatePath("successRate");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          System Gets Smarter Over Time
        </CardTitle>
        <p className="text-xs text-slate-400 mt-1">
          Confidence and success rate improvement through cross-incident learning
        </p>
      </CardHeader>
      <CardContent>
        <div className="relative bg-slate-900/50 rounded-lg p-4">
          <svg width={width} height={height} className="w-full h-auto">
            {/* Grid lines */}
            {[0, 25, 50, 75, 100].map((percent) => (
              <g key={percent}>
                <line
                  x1={padding.left}
                  y1={yScale(percent)}
                  x2={width - padding.right}
                  y2={yScale(percent)}
                  stroke="#334155"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 10}
                  y={yScale(percent) + 4}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="12"
                >
                  {percent}%
                </text>
              </g>
            ))}

            {/* X-axis labels */}
            {LEARNING_DATA.map((d) => (
              <text
                key={d.incidents}
                x={xScale(d.incidents)}
                y={height - padding.bottom + 25}
                textAnchor="middle"
                fill="#64748b"
                fontSize="12"
              >
                {d.incidents}
              </text>
            ))}

            {/* Axis labels */}
            <text
              x={width / 2}
              y={height - 10}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="14"
              fontWeight="600"
            >
              Incidents Processed
            </text>
            <text
              x={padding.left - 40}
              y={height / 2}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="14"
              fontWeight="600"
              transform={`rotate(-90 ${padding.left - 40} ${height / 2})`}
            >
              Percentage
            </text>

            {/* Success Rate Line */}
            <motion.path
              d={successPath}
              fill="none"
              stroke="#3b82f6"
              strokeWidth="3"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2, ease: "easeInOut" }}
            />

            {/* Confidence Line */}
            <motion.path
              d={confidencePath}
              fill="none"
              stroke="#10b981"
              strokeWidth="3"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2, ease: "easeInOut", delay: 0.3 }}
            />

            {/* Data points */}
            {LEARNING_DATA.map((d, i) => (
              <g key={i}>
                {/* Success Rate point */}
                <motion.circle
                  cx={xScale(d.incidents)}
                  cy={yScale(d.successRate)}
                  r="5"
                  fill="#3b82f6"
                  stroke="#1e293b"
                  strokeWidth="2"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 2 + i * 0.1 }}
                />

                {/* Confidence point */}
                <motion.circle
                  cx={xScale(d.incidents)}
                  cy={yScale(d.confidence)}
                  r="5"
                  fill="#10b981"
                  stroke="#1e293b"
                  strokeWidth="2"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 2.3 + i * 0.1 }}
                />
              </g>
            ))}

            {/* Legend */}
            <g transform={`translate(${width - 200}, ${padding.top})`}>
              <rect
                x="0"
                y="0"
                width="180"
                height="60"
                fill="#1e293b"
                rx="4"
                stroke="#334155"
                strokeWidth="1"
              />
              <line
                x1="10"
                y1="20"
                x2="40"
                y2="20"
                stroke="#10b981"
                strokeWidth="3"
              />
              <circle cx="25" cy="20" r="4" fill="#10b981" />
              <text x="50" y="24" fill="#94a3b8" fontSize="12">
                Agent Confidence
              </text>

              <line
                x1="10"
                y1="45"
                x2="40"
                y2="45"
                stroke="#3b82f6"
                strokeWidth="3"
              />
              <circle cx="25" cy="45" r="4" fill="#3b82f6" />
              <text x="50" y="49" fill="#94a3b8" fontSize="12">
                Success Rate
              </text>
            </g>
          </svg>

          {/* Key Insights */}
          <div className="mt-6 grid grid-cols-3 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 3 }}
              className="bg-slate-800/50 p-3 rounded border-l-4 border-l-green-500"
            >
              <div className="text-xs text-slate-400 mb-1">Starting Point</div>
              <div className="text-lg font-bold text-green-400">70%</div>
              <div className="text-xs text-slate-500">Initial Confidence</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 3.2 }}
              className="bg-slate-800/50 p-3 rounded border-l-4 border-l-blue-500"
            >
              <div className="text-xs text-slate-400 mb-1">After 200 Incidents</div>
              <div className="text-lg font-bold text-blue-400">96%</div>
              <div className="text-xs text-slate-500">Success Rate</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 3.4 }}
              className="bg-slate-800/50 p-3 rounded border-l-4 border-l-purple-500"
            >
              <div className="text-xs text-slate-400 mb-1">Improvement</div>
              <div className="text-lg font-bold text-purple-400">+22%</div>
              <div className="text-xs text-slate-500">Confidence Gain</div>
            </motion.div>
          </div>

          {/* Summary */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 3.6 }}
            className="mt-4 p-4 bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-500/30 rounded-lg"
          >
            <div className="flex items-start gap-3">
              <Award className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300">
                <span className="font-semibold">Long-term Value:</span> The system
                continuously improves through cross-incident learning. After processing
                200 incidents, agent confidence reaches 92% and success rate hits 96%.
                Each resolved incident makes the system smarter for the next one.
              </div>
            </div>
          </motion.div>
        </div>
      </CardContent>
    </Card>
  );
}
