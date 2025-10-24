/**
 * Shared Components Index
 *
 * Centralized exports for all shared dashboard components.
 * Ensures consistent imports across all dashboard pages.
 */

// Layout Components
export {
  DashboardLayout,
  DashboardSection,
  DashboardGrid,
} from "./DashboardLayout";

// Logo Component
export { SwarmAILogo } from "./SwarmAILogo";

// Status Indicators
export {
  AgentStatus,
  SeverityIndicator,
  IncidentStatus,
  ConfidenceScore,
  SystemHealth,
  MTTRIndicator,
} from "./StatusIndicators";

// Metric Cards
export {
  MetricCard,
  ProgressMetricCard,
  ComparisonMetricCard,
  StatusGridCard,
  BusinessImpactCard,
} from "./MetricCards";

// Demo Components for Enhanced Showcase
export { default as ByzantineConsensusDemo } from "../ByzantineConsensusDemo";
export { default as PredictivePreventionDemo } from "../PredictivePreventionDemo";

// Re-export commonly used UI components for convenience
export { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
export { Badge } from "../ui/badge";
export { Button } from "../ui/button";
export { Progress } from "../ui/progress";
export { Alert, AlertDescription } from "../ui/alert";
export { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
