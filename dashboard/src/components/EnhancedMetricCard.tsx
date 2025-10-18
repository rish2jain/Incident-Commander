import * as React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { cn } from "../lib/utils";

// Define the icon type
type IconType =
  | React.ElementType
  | React.FunctionComponent<React.SVGProps<SVGSVGElement>>;

// Define trend types
export type TrendType = "up" | "down" | "neutral";

// Props definition
export interface EnhancedMetricCardProps {
  /** The main value of the metric (e.g., "1,234", "$5.6M", "92%"). */
  value: string;
  /** The descriptive title of the metric (e.g., "Total Users", "Revenue"). */
  title: string;
  /** Optional icon to display in the card header. */
  icon?: IconType;
  /** The percentage or absolute change for the trend (e.g., "2.5%"). */
  trendChange?: string;
  /** The direction of the trend ('up', 'down', 'neutral'). */
  trendType?: TrendType;
  /** Optional class name for the card container. */
  className?: string;
  /** Color theme for the metric */
  color?: "blue" | "green" | "red" | "yellow" | "purple" | "cyan";
  /** Show animated background effect */
  animated?: boolean;
}

/**
 * A professional, animated metric card for the Incident Commander dashboard.
 * Displays a key value, title, icon, and trend indicator with Framer Motion hover effects.
 */
const EnhancedMetricCard: React.FC<EnhancedMetricCardProps> = ({
  value,
  title,
  icon: IconComponent,
  trendChange,
  trendType = "neutral",
  className,
  color = "blue",
  animated = true,
}) => {
  // Determine trend icon and color
  const TrendIcon =
    trendType === "up"
      ? TrendingUp
      : trendType === "down"
      ? TrendingDown
      : Minus;
  const trendColorClass =
    trendType === "up"
      ? "text-green-600 dark:text-green-400"
      : trendType === "down"
      ? "text-red-600 dark:text-red-400"
      : "text-muted-foreground";

  // Color configurations
  const colorConfig = {
    blue: {
      gradient: "from-blue-500/10 to-blue-600/10",
      border: "border-blue-500/20",
      icon: "text-blue-500",
      glow: "hover:shadow-[0_0_20px_rgba(59,130,246,0.2)]",
    },
    green: {
      gradient: "from-green-500/10 to-green-600/10",
      border: "border-green-500/20",
      icon: "text-green-500",
      glow: "hover:shadow-[0_0_20px_rgba(34,197,94,0.2)]",
    },
    red: {
      gradient: "from-red-500/10 to-red-600/10",
      border: "border-red-500/20",
      icon: "text-red-500",
      glow: "hover:shadow-[0_0_20px_rgba(239,68,68,0.2)]",
    },
    yellow: {
      gradient: "from-yellow-500/10 to-yellow-600/10",
      border: "border-yellow-500/20",
      icon: "text-yellow-500",
      glow: "hover:shadow-[0_0_20px_rgba(234,179,8,0.2)]",
    },
    purple: {
      gradient: "from-purple-500/10 to-purple-600/10",
      border: "border-purple-500/20",
      icon: "text-purple-500",
      glow: "hover:shadow-[0_0_20px_rgba(168,85,247,0.2)]",
    },
    cyan: {
      gradient: "from-cyan-500/10 to-cyan-600/10",
      border: "border-cyan-500/20",
      icon: "text-cyan-500",
      glow: "hover:shadow-[0_0_20px_rgba(6,182,212,0.2)]",
    },
  };

  const config = colorConfig[color];

  return (
    <motion.div
      whileHover={{
        y: -4,
        boxShadow:
          "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
      }}
      transition={{ type: "spring", stiffness: 400, damping: 20 }}
      className={cn(
        "cursor-pointer rounded-lg relative overflow-hidden",
        className
      )}
    >
      <Card
        className={`h-full transition-all duration-300 backdrop-blur-sm
        bg-gradient-to-br ${config.gradient} border ${config.border} ${config.glow}`}
      >
        {/* Animated background effect */}
        {animated && (
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
        )}

        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          {IconComponent && (
            <motion.div
              whileHover={{ scale: 1.1, rotate: 5 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
              className={`p-2 rounded-lg bg-background/50 ${config.icon}`}
            >
              <IconComponent className="h-4 w-4" aria-hidden="true" />
            </motion.div>
          )}
        </CardHeader>

        <CardContent className="relative z-10">
          <motion.div
            className="text-2xl font-bold text-foreground mb-2"
            initial={{ scale: 1 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.05 }}
          >
            {value}
          </motion.div>

          {trendChange && (
            <motion.p
              className={cn(
                "flex items-center text-xs font-medium",
                trendColorClass
              )}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <TrendIcon className="h-3 w-3 mr-1" aria-hidden="true" />
              {trendChange}{" "}
              {trendType === "up"
                ? "increase"
                : trendType === "down"
                ? "decrease"
                : "change"}
            </motion.p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default EnhancedMetricCard;
