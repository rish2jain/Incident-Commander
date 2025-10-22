"use client";

import { ExecutiveDashboard } from "@/components/ExecutiveDashboard";

/**
 * Executive Dashboard Route - BUSINESS/EXECUTIVE VIEW
 *
 * Dashboard 1: High-level business metrics and ROI demonstration.
 * Designed for executives, investors, and business stakeholders.
 *
 * Features:
 * - ROI and cost savings highlights
 * - Real-time business metrics
 * - Byzantine consensus visualization
 * - AWS services integration showcase
 * - Learning and improvement tracking
 * - Simple, non-technical presentation
 *
 * Use this for:
 * - Executive presentations
 * - Investor demos
 * - Business value proposition
 * - Hackathon pitches (business track)
 *
 * For technical details use:
 * - Dashboard 2: /transparency (engineering deep-dive)
 * - Dashboard 3: /ops (live operations monitoring)
 */
export default function DemoPage() {
  return <ExecutiveDashboard />;
}
