"use client";

import { ImprovedOperationsDashboardWebSocket } from "@/components/ImprovedOperationsDashboardWebSocket";

/**
 * Operations Dashboard Route - PRODUCTION LIVE SYSTEM
 *
 * Dashboard 3: Production-ready dashboard with real-time WebSocket integration.
 * Connects to backend for live incident monitoring and agent coordination.
 *
 * Features:
 * - Real-time WebSocket connection
 * - Live agent status updates
 * - Active incident monitoring
 * - Business metrics streaming
 * - System health dashboard
 * - Demo incident triggering
 * - Agent reset controls
 *
 * Use this for:
 * - Production deployment and operations
 * - Real-time incident response
 * - SRE/DevOps daily monitoring
 * - Live system health tracking
 *
 * For demos use:
 * - Dashboard 1: /demo (executive presentation)
 * - Dashboard 2: /transparency (technical deep-dive)
 */
export default function OpsPage() {
  return <ImprovedOperationsDashboardWebSocket />;
}
