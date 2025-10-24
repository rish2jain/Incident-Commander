/**
 * AWS Services Monitoring Panel
 *
 * Displays real-time performance metrics for integrated AWS AI services:
 * - Amazon Q Business: Historical knowledge retrieval
 * - Amazon Nova: Multi-model inference
 * - Bedrock Agents with Memory: Cross-incident learning
 *
 * Professional operational widget for Dashboard 3.
 */

"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Cloud,
  Database,
  Zap,
  Brain,
  Activity,
  TrendingDown,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
} from "./shared";

interface ServiceStats {
  total_queries?: number;
  avg_confidence?: number;
  matches?: number;
  total_calls?: number;
  avg_latency_ms?: number;
  savings?: number;
  learned?: number;
  improvement?: number;
  success_rate?: number;
}

interface CostStats {
  traditional_cost?: number;
  nova_cost?: number;
}

export function AWSServicesMonitor() {
  const [qBusinessStats, setQBusinessStats] = useState<ServiceStats>({
    total_queries: 1247, // Mock data
    avg_confidence: 85, // Mock data
    matches: 342, // Mock data
  });

  const [novaStats, setNovaStats] = useState<ServiceStats & CostStats>({
    total_calls: 3891, // Mock data
    avg_latency_ms: 142, // Mock data
    savings: 2847.32, // Mock data
    traditional_cost: 3000, // Mock data
    nova_cost: 152.68, // Mock data
  });

  const [memoryStats, setMemoryStats] = useState<ServiceStats>({
    learned: 89,
    improvement: 22.5,
    success_rate: 93.2,
  });

  // Simulate live updates (replace with real WebSocket data)
  useEffect(() => {
    const interval = setInterval(() => {
      setQBusinessStats((prev) => ({
        ...prev,
        total_queries:
          (prev.total_queries || 0) + Math.floor(Math.random() * 3),
      }));

      setNovaStats((prev) => ({
        ...prev,
        total_calls: (prev.total_calls || 0) + Math.floor(Math.random() * 5),
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const costReduction =
    novaStats.traditional_cost && novaStats.nova_cost
      ? (
          ((novaStats.traditional_cost - novaStats.nova_cost) /
            novaStats.traditional_cost) *
          100
        ).toFixed(0)
      : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Cloud className="w-5 h-5 text-blue-400" />
          AI Services Performance (Mock Data)
        </CardTitle>
        <p className="text-xs text-slate-400 mt-1">
          Demo simulation of AWS AI service integration
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Amazon Q Business */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="border-l-4 border-l-orange-500 pl-3 bg-slate-800/50 p-3 rounded-r"
          >
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-4 h-4 text-orange-400" />
              <h3 className="font-semibold text-sm text-orange-400">
                Amazon Q Business
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Historical Knowledge Retrieval
            </p>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Queries:</span>
                <span className="font-mono text-sm font-semibold">
                  {qBusinessStats.total_queries?.toLocaleString() || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Confidence:</span>
                <span className="font-mono text-sm font-semibold text-green-400">
                  {qBusinessStats.avg_confidence || 0}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Matches:</span>
                <span className="font-mono text-sm font-semibold">
                  {qBusinessStats.matches || 0}
                </span>
              </div>
            </div>
            <Badge
              variant="default"
              className="mt-3 text-xs bg-green-600 hover:bg-green-600"
            >
              <Activity className="w-3 h-3 mr-1" />
              ACTIVE
            </Badge>
          </motion.div>

          {/* Amazon Nova */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="border-l-4 border-l-blue-500 pl-3 bg-slate-800/50 p-3 rounded-r"
          >
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-blue-400" />
              <h3 className="font-semibold text-sm text-blue-400">
                Amazon Nova
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-3">Multi-Model Inference</p>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Calls:</span>
                <span className="font-mono text-sm font-semibold">
                  {novaStats.total_calls?.toLocaleString() || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Latency:</span>
                <span className="font-mono text-sm font-semibold text-blue-400">
                  {novaStats.avg_latency_ms || 0}ms
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Savings:</span>
                <span className="font-mono text-sm font-semibold text-green-400">
                  ${novaStats.savings?.toFixed(2) || 0}
                </span>
              </div>
            </div>
            <Badge
              variant="default"
              className="mt-3 text-xs bg-green-600 hover:bg-green-600"
            >
              <Activity className="w-3 h-3 mr-1" />
              ACTIVE
            </Badge>
          </motion.div>

          {/* Bedrock Agents with Memory */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="border-l-4 border-l-purple-500 pl-3 bg-slate-800/50 p-3 rounded-r"
          >
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-purple-400" />
              <h3 className="font-semibold text-sm text-purple-400">
                Bedrock Agents + Memory
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Cross-Incident Learning
            </p>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Learned:</span>
                <span className="font-mono text-sm font-semibold">
                  {memoryStats.learned || 0} incidents
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Improved:</span>
                <span className="font-mono text-sm font-semibold text-green-400">
                  +{memoryStats.improvement || 0}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Success:</span>
                <span className="font-mono text-sm font-semibold text-green-400">
                  {memoryStats.success_rate || 0}%
                </span>
              </div>
            </div>
            <Badge
              variant="default"
              className="mt-3 text-xs bg-purple-600 hover:bg-purple-600"
            >
              <Brain className="w-3 h-3 mr-1" />
              LEARNING
            </Badge>
          </motion.div>
        </div>

        {/* Cost Efficiency Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-4 pt-4 border-t border-slate-700"
        >
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <TrendingDown className="w-4 h-4 text-green-400" />
            <span>
              Cost efficiency: Nova multi-model routing saves{" "}
              <span className="text-green-400 font-semibold">
                $
                {(
                  (novaStats.traditional_cost || 0) - (novaStats.nova_cost || 0)
                ).toFixed(2)}
              </span>{" "}
              ({costReduction}% reduction vs single-model approach)
            </span>
          </div>
        </motion.div>
      </CardContent>
    </Card>
  );
}
