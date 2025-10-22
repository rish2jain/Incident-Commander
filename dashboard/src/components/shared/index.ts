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

// Re-export commonly used UI components for convenience
export { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
export { Badge } from "@/components/ui/badge";
export { Button } from "@/components/ui/button";
export { Progress } from "@/components/ui/progress";
export { Alert, AlertDescription } from "@/components/ui/alert";
export { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
