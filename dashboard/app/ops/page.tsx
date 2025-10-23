"use client";

import { ConsolidatedOperationsDashboard } from "@/components/ConsolidatedOperationsDashboard";

/**
 * SwarmAI Operations Dashboard - CONSOLIDATED SINGLE PANE OF GLASS
 *
 * Consolidated dashboard combining best features from all views.
 * Designed to prove AWS integration and create cohesive judge experience.
 *
 * Features:
 * - Module 1: Business Impact (Projected) - Annual savings, ROI
 * - Module 2: Predictive Prevention System - Live threat detection
 * - Module 3: System Controls - Trigger incidents, reset agents
 * - Module 4: Byzantine Fault Tolerance - Consensus visualization (conditional)
 * - Module 5: Active Incidents - Expandable with reasoning tabs
 *
 * AWS Service Visual Proof:
 * - Amazon Q Business - Natural language incident analysis
 * - Nova Act - Step-by-step action plans
 * - AWS Strands SDK - Agent lifecycle management
 * - Amazon Titan Embeddings - RAG evidence retrieval
 *
 * Data Labeling:
 * - "(Projected)" for financial projections
 * - No labels for live simulation data
 *
 * Use this for:
 * - Hackathon judging (primary dashboard)
 * - Executive + technical demonstrations
 * - Proving 8/8 AWS AI services integration
 */
export default function OpsPage() {
  return <ConsolidatedOperationsDashboard />;
}
