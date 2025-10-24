"use client";

import { ImprovedOperationsDashboardWebSocket } from "@/components/ImprovedOperationsDashboardWebSocket";

/**
 * Operations Dashboard Route - PRODUCTION LIVE SYSTEM
 *
 * Dashboard 3: Production-ready dashboard with real-time WebSocket integration.
 * For Live SREs: The "Now" (Active Incidents)
 *
 * Features:
 * - Real-time WebSocket connection
 * - Live agent status updates
 * - Active incident monitoring
 * - Business metrics streaming
 * - System health dashboard
 * - Demo incident triggering
 * - Agent reset controls
 * - Clickable incidents that navigate to AI Transparency
 *
 * Use this for:
 * - Production deployment and operations
 * - Real-time incident response
 * - SRE/DevOps daily monitoring
 * - Live system health tracking
 */
export default function OpsPage() {
  return <ImprovedOperationsDashboardWebSocket />;
}
