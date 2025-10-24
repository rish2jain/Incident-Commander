/**
 * Design System Tokens
 *
 * Centralized design constants for consistent styling across all dashboards
 */

export const colors = {
  // Primary palette
  primary: {
    blue: "#4da3ff",
    cyan: "#22d3ee",
  },

  // Status colors
  success: "#4ade80",
  warning: "#fbbf24",
  error: "#f87171",
  info: "#3b82f6",

  // Background colors
  background: {
    dark: "#0a0e27",
    darker: "#050814",
    card: "#141829",
    cardHover: "#1a1f3a",
  },

  // Border colors
  border: {
    default: "#1e2746",
    hover: "#2d3659",
    active: "#4da3ff",
  },

  // Text colors
  text: {
    primary: "#e0e6ed",
    secondary: "#8b92a7",
    muted: "#64748b",
  },
} as const;

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "24px",
  "2xl": "32px",
  "3xl": "48px",
} as const;

export const borderRadius = {
  sm: "4px",
  md: "6px",
  lg: "8px",
  xl: "12px",
  full: "9999px",
} as const;

export const typography = {
  // Font sizes
  fontSize: {
    xs: "10px",
    sm: "12px",
    base: "14px",
    lg: "16px",
    xl: "18px",
    "2xl": "24px",
    "3xl": "30px",
    "4xl": "36px",
  },

  // Font weights
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // Line heights
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
  },
} as const;

export const shadows = {
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
  glow: {
    blue: "0 0 20px rgba(77, 163, 255, 0.3)",
    green: "0 0 20px rgba(74, 222, 128, 0.3)",
    red: "0 0 20px rgba(248, 113, 113, 0.3)",
  },
} as const;

export const transitions = {
  fast: "150ms ease-in-out",
  normal: "250ms ease-in-out",
  slow: "350ms ease-in-out",
} as const;

// Agent status colors
export const agentStatusColors = {
  idle: colors.text.muted,
  active: colors.primary.blue,
  complete: colors.success,
  error: colors.error,
} as const;

// Severity colors
export const severityColors = {
  low: colors.success,
  medium: colors.warning,
  high: colors.error,
  critical: "#dc2626", // Darker red
} as const;

// Confidence gradient
export const confidenceGradient = {
  low: colors.error,
  medium: colors.warning,
  high: colors.success,
} as const;

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return confidenceGradient.high;
  if (confidence >= 0.6) return confidenceGradient.medium;
  return confidenceGradient.low;
}

export function getSeverityColor(severity: string): string {
  return severityColors[severity as keyof typeof severityColors] || colors.text.muted;
}

export function getAgentStatusColor(status: string): string {
  return agentStatusColors[status as keyof typeof agentStatusColors] || colors.text.muted;
}
