"use client";

import { PowerDashboard } from "../../src/components/PowerDashboard";

/**
 * PowerDashboard Route - INTERACTIVE DEMO VIEW (Updated)
 *
 * Dashboard 1: Interactive incident demonstration with live timeline.
 * Designed for hackathon presentations and technical demonstrations.
 *
 * Features:
 * - Interactive incident timeline with playback controls
 * - Live agent coordination visualization
 * - Before vs After comparison widgets
 * - Real-time business impact calculator
 * - Enhanced transparency with side-by-side views
 * - Predicted incidents section
 * - Industry firsts highlight panel
 * - Competitor comparison
 * - Interactive hotspots and tooltips
 * - Pre-populated demo state for immediate impact
 *
 * Use this for:
 * - Hackathon presentations
 * - Technical demonstrations
 * - Interactive judge evaluations
 * - Power user showcases
 *
 * For other views use:
 * - Dashboard 2: /transparency (engineering deep-dive)
 * - Dashboard 3: /ops (live operations monitoring)
 */
export default function DemoPage() {
  return <PowerDashboard />;
}
