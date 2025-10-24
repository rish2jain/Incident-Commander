/**
 * Executive Dashboard - Dashboard 1
 *
 * High-level business metrics and value proposition for executives.
 * Focus on ROI, cost savings, and business impact.
 *
 * Features:
 * - Real-time cost savings counter
 * - Business impact metrics
 * - Byzantine consensus visualization
 * - Simple, non-technical presentation
 * - Animated statistics
 * - Clear value proposition
 */

"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  DollarSign,
  Clock,
  Shield,
  Zap,
  CheckCircle,
  AlertCircle,
  TrendingDown,
  BarChart3,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
} from "./shared";
import { LiveValueCounter } from "./LiveValueCounter";
import { AWSServicesMonitor } from "./AWSServicesMonitor";
import { AgentNetworkVisualization } from "./AgentNetworkVisualization";
import { LearningJourneyChart } from "./LearningJourneyChart";

// Animated Counter Component
function AnimatedCounter({
  value,
  duration = 2000,
  decimals = 0,
  prefix = "",
  suffix = "",
}: {
  value: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
}) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime: number;
    let animationFrame: number;

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);

      // Ease-out animation
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(value * easedProgress);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [value, duration]);

  return (
    <span>
      {prefix}
      {displayValue.toFixed(decimals)}
      {suffix}
    </span>
  );
}

// Metric Card Component
function MetricCard({
  icon: Icon,
  title,
  value,
  change,
  changeLabel,
  trend,
  color = "blue",
}: {
  icon: React.ElementType;
  title: string;
  value: string | React.ReactNode;
  change?: string;
  changeLabel?: string;
  trend?: "up" | "down";
  color?: "blue" | "green" | "purple" | "orange";
}) {
  const colorClasses = {
    blue: "border-blue-500 bg-blue-900/20",
    green: "border-green-500 bg-green-900/20",
    purple: "border-purple-500 bg-purple-900/20",
    orange: "border-orange-500 bg-orange-900/20",
  };

  const iconColors = {
    blue: "text-blue-400",
    green: "text-green-400",
    purple: "text-purple-400",
    orange: "text-orange-400",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      whileHover={{ scale: 1.02, y: -4 }}
    >
      <Card className={`border-l-4 ${colorClasses[color]} transition-all`}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className={`w-5 h-5 ${iconColors[color]}`} />
              <span className="text-sm text-slate-400">{title}</span>
            </div>
            {trend && (
              <div
                className={`flex items-center gap-1 ${
                  trend === "up" ? "text-green-400" : "text-red-400"
                }`}
              >
                {trend === "up" ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-white mb-1">{value}</div>
          {change && (
            <div className="text-xs text-slate-400">
              <span className="text-green-400 font-semibold">{change}</span>{" "}
              {changeLabel}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ROI Highlight Component
function ROIHighlight() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
    >
      <Card className="border-2 border-green-500 bg-gradient-to-br from-green-900/30 to-blue-900/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-2xl">
            <DollarSign className="w-7 h-7 text-green-400" />
            Return on Investment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-sm text-slate-400 mb-2">
                Traditional MTTR (Mock)
              </div>
              <div className="text-4xl font-bold text-red-400">
                <AnimatedCounter value={30} decimals={0} suffix=" min" />
              </div>
            </div>
            <div className="flex items-center justify-center">
              <motion.div
                animate={{ x: [0, 10, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <ArrowRight className="w-8 h-8 text-green-400" />
              </motion.div>
            </div>
            <div className="text-center">
              <div className="text-sm text-slate-400 mb-2">
                With AI Agents (Mock)
              </div>
              <div className="text-4xl font-bold text-green-400">
                <AnimatedCounter value={2.5} decimals={1} suffix=" min" />
              </div>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-slate-700 text-center">
            <div className="text-sm text-slate-400 mb-2">
              MTTR Reduction (Mock)
            </div>
            <div className="text-5xl font-bold text-green-400">
              <AnimatedCounter value={91.8} decimals={1} suffix="%" />
            </div>
            <div className="text-sm text-slate-400 mt-2">
              Saves <span className="text-green-400 font-semibold">$229K</span>{" "}
              per major incident
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// System Status Component
function SystemStatus() {
  const [status, setStatus] = useState<"operational" | "incident" | "warning">(
    "operational"
  );

  const statusConfig = {
    operational: {
      icon: CheckCircle,
      text: "All Systems Operational",
      color: "text-green-400",
      bgColor: "bg-green-900/20",
      borderColor: "border-green-500",
    },
    incident: {
      icon: AlertCircle,
      text: "Incident Detected - AI Responding",
      color: "text-red-400",
      bgColor: "bg-red-900/20",
      borderColor: "border-red-500",
    },
    warning: {
      icon: Shield,
      text: "Predictive Alert - Prevention Active",
      color: "text-yellow-400",
      bgColor: "bg-yellow-900/20",
      borderColor: "border-yellow-500",
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card
        className={`border-l-4 ${config.borderColor} ${config.bgColor} transition-all`}
      >
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <motion.div
                animate={
                  status !== "operational"
                    ? { scale: [1, 1.1, 1], opacity: [1, 0.8, 1] }
                    : {}
                }
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Icon className={`w-8 h-8 ${config.color}`} />
              </motion.div>
              <div>
                <div className={`text-xl font-bold ${config.color}`}>
                  {config.text}
                </div>
                <div className="text-sm text-slate-400 mt-1">
                  5 AI agents monitoring 47 services
                </div>
              </div>
            </div>
            <Badge
              variant={status === "operational" ? "default" : "destructive"}
              className={
                status === "operational"
                  ? "bg-green-600 text-lg px-4 py-2"
                  : "text-lg px-4 py-2"
              }
            >
              {status === "operational" ? "HEALTHY" : "ACTIVE"}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Main Executive Dashboard
export function ExecutiveDashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-green-400 bg-clip-text text-transparent mb-3">
            SwarmAI
          </h1>
          <p className="text-xl text-slate-400">
            AI-Powered Incident Response • 92% Faster Resolution
          </p>
          <div className="flex items-center justify-center gap-3 mt-4">
            <Badge variant="outline" className="text-sm px-3 py-1">
              <Sparkles className="w-3 h-3 mr-1" />
              Powered by 8 AWS Services
            </Badge>
            <Badge variant="outline" className="text-sm px-3 py-1">
              <Shield className="w-3 h-3 mr-1" />
              Byzantine Fault Tolerant
            </Badge>
            <Badge variant="outline" className="text-sm px-3 py-1">
              <Zap className="w-3 h-3 mr-1" />
              Production Ready
            </Badge>
          </div>
        </motion.div>

        {/* System Status */}
        <SystemStatus />

        {/* ROI Highlight */}
        <ROIHighlight />

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Clock}
            title="Mean Time to Resolution (Mock)"
            value={<AnimatedCounter value={147} decimals={0} suffix="s" />}
            change="↓ 91.8% (mock)"
            changeLabel="vs traditional"
            trend="up"
            color="green"
          />
          <MetricCard
            icon={DollarSign}
            title="Cost Savings (Per Incident) (Mock)"
            value={
              <>
                $
                <AnimatedCounter value={230} decimals={0} suffix="K" />
              </>
            }
            change="92% faster"
            changeLabel="resolution"
            trend="up"
            color="green"
          />
          <MetricCard
            icon={BarChart3}
            title="Incidents Prevented (Mock)"
            value={<AnimatedCounter value={89} decimals={0} />}
            change="↑ 22.5%"
            changeLabel="with learning"
            trend="up"
            color="purple"
          />
          <MetricCard
            icon={Shield}
            title="System Accuracy (Mock)"
            value={<AnimatedCounter value={95.3} decimals={1} suffix="%" />}
            change="40% failures"
            changeLabel="tolerated"
            trend="up"
            color="blue"
          />
        </div>

        {/* Live Value Counter */}
        <LiveValueCounter />

        {/* Agent Network Visualization */}
        <Card className="border-blue-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-blue-400" />
              Byzantine Consensus Network
              <Badge variant="outline" className="ml-2">
                5 Agents • 3/5 Required
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-center">
              <AgentNetworkVisualization activeIncident={false} />
            </div>
            <div className="mt-4 text-center text-sm text-slate-400">
              Distributed consensus ensures 95% accuracy even with 40% agent
              failures (mock data)
            </div>
          </CardContent>
        </Card>

        {/* AWS Services Monitor */}
        <AWSServicesMonitor />

        {/* Learning Journey Chart */}
        <LearningJourneyChart />

        {/* Call to Action */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.6 }}
          className="text-center pt-6"
        >
          <Card className="border-purple-500/30 bg-gradient-to-r from-purple-900/20 to-blue-900/20">
            <CardContent className="py-8">
              <h2 className="text-2xl font-bold mb-4">
                Ready to Transform Your Incident Response?
              </h2>
              <p className="text-slate-400 mb-6 max-w-2xl mx-auto">
                Deploy in 30 minutes with AWS CDK. Full production readiness
                with health endpoints, metrics, and comprehensive documentation.
              </p>
              <div className="flex items-center justify-center gap-4">
                <Button className="bg-blue-600 hover:bg-blue-700 text-lg px-6 py-3">
                  View Technical Details
                </Button>
                <Button variant="outline" className="text-lg px-6 py-3">
                  See Live Demo
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Footer */}
        <div className="text-center text-xs text-slate-500 pt-6 border-t border-slate-800">
          <p>Dashboard 1: Executive Overview • High-Level Business Metrics</p>
          <p className="mt-1">
            <a href="/transparency" className="text-blue-400 hover:underline">
              Dashboard 2: Engineering Transparency
            </a>
            {" • "}
            <a href="/ops" className="text-blue-400 hover:underline">
              Dashboard 3: Live Operations
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
