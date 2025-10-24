/**
 * Loading State Components
 *
 * Reusable loading skeletons and spinners for better UX.
 */

"use client";

import React from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "../shared";

// Simple spinner
export function Spinner({ size = "md", className = "" }: { size?: "sm" | "md" | "lg"; className?: string }) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8",
  };

  return (
    <Loader2 className={`${sizeClasses[size]} animate-spin ${className}`} />
  );
}

// Loading overlay
export function LoadingOverlay({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-slate-800 rounded-lg p-8 flex flex-col items-center gap-4"
      >
        <Spinner size="lg" className="text-blue-400" />
        <div className="text-white font-medium">{message}</div>
      </motion.div>
    </div>
  );
}

// Skeleton loader
export function Skeleton({ className = "", animate = true }: { className?: string; animate?: boolean }) {
  return (
    <div
      className={`bg-slate-700 rounded ${animate ? "animate-pulse" : ""} ${className}`}
    />
  );
}

// Skeleton card
export function SkeletonCard() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-1/3" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </CardContent>
    </Card>
  );
}

// Agent card skeleton
export function AgentCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton className="w-5 h-5 rounded-full" />
            <Skeleton className="h-4 w-24" />
          </div>
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-3 w-full mb-2" />
        <Skeleton className="h-3 w-2/3" />
      </CardContent>
    </Card>
  );
}

// Metric card skeleton
export function MetricCardSkeleton() {
  return (
    <Card>
      <CardContent className="py-4">
        <Skeleton className="h-3 w-20 mb-3" />
        <Skeleton className="h-8 w-24 mb-1" />
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}

// Dashboard skeleton with grid
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-64 mb-2" />
        <Skeleton className="h-4 w-96" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <AgentCardSkeleton key={i} />
        ))}
      </div>

      <SkeletonCard />
    </div>
  );
}

// Pulsing dot indicator (for live data)
export function PulseDot({ color = "green" }: { color?: "green" | "blue" | "red" | "yellow" }) {
  const colorClasses = {
    green: "bg-green-500",
    blue: "bg-blue-500",
    red: "bg-red-500",
    yellow: "bg-yellow-500",
  };

  return (
    <motion.div
      className={`w-2 h-2 rounded-full ${colorClasses[color]}`}
      animate={{ opacity: [1, 0.3, 1] }}
      transition={{ duration: 1.5, repeat: Infinity }}
    />
  );
}

// Progress spinner with percentage
export function ProgressSpinner({ progress, size = "md" }: { progress: number; size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: { container: "w-12 h-12", text: "text-xs" },
    md: { container: "w-16 h-16", text: "text-sm" },
    lg: { container: "w-24 h-24", text: "text-lg" },
  };

  const { container, text } = sizeClasses[size];

  return (
    <div className={`relative ${container}`}>
      <svg className="w-full h-full transform -rotate-90">
        <circle
          cx="50%"
          cy="50%"
          r="40%"
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          className="text-slate-700"
        />
        <motion.circle
          cx="50%"
          cy="50%"
          r="40%"
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
          className="text-blue-400"
          initial={{ strokeDashoffset: 251 }}
          animate={{ strokeDashoffset: 251 - (251 * progress) / 100 }}
          transition={{ duration: 0.5 }}
          style={{
            strokeDasharray: "251",
          }}
        />
      </svg>
      <div className={`absolute inset-0 flex items-center justify-center ${text} font-semibold text-white`}>
        {Math.round(progress)}%
      </div>
    </div>
  );
}
