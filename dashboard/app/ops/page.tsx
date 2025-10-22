"use client";

import { ImprovedOperationsDashboard } from "@/components/ImprovedOperationsDashboard";

/**
 * Operations Dashboard Route
 *
 * Production-ready dashboard with live backend integration.
 * Connects via WebSocket for real-time incident monitoring and agent coordination.
 *
 * Use this for:
 * - Actual deployment in production environments
 * - Real-time incident response and monitoring
 * - Day-to-day SRE/DevOps operations
 * - Live system health tracking
 *
 * NOT for demos - use /demo or /transparency instead
 */
export default function OpsPage() {
  return <ImprovedOperationsDashboard />;
}
