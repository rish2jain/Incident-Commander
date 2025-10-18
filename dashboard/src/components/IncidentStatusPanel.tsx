import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  Clock,
  TrendingUp,
  Users,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";

interface Service {
  name: string;
  status: "operational" | "degraded" | "down";
  impact: string;
}

interface Metric {
  label: string;
  value: string;
  change: number;
  icon: React.ReactNode;
}

interface IncidentStatusPanelProps {
  incidentId?: string;
  title?: string;
  severity?: "critical" | "high" | "medium" | "low";
  startTime?: Date;
  affectedServices?: Service[];
  description?: string;
}

const SeverityBadge = ({ severity }: { severity: string }) => {
  const severityConfig = {
    critical: {
      bg: "bg-red-500/10 dark:bg-red-500/20",
      border: "border-red-500/50",
      text: "text-red-600 dark:text-red-400",
      glow: "shadow-[0_0_20px_rgba(239,68,68,0.3)]",
    },
    high: {
      bg: "bg-orange-500/10 dark:bg-orange-500/20",
      border: "border-orange-500/50",
      text: "text-orange-600 dark:text-orange-400",
      glow: "shadow-[0_0_20px_rgba(249,115,22,0.3)]",
    },
    medium: {
      bg: "bg-yellow-500/10 dark:bg-yellow-500/20",
      border: "border-yellow-500/50",
      text: "text-yellow-600 dark:text-yellow-400",
      glow: "shadow-[0_0_20px_rgba(234,179,8,0.3)]",
    },
    low: {
      bg: "bg-blue-500/10 dark:bg-blue-500/20",
      border: "border-blue-500/50",
      text: "text-blue-600 dark:text-blue-400",
      glow: "shadow-[0_0_20px_rgba(59,130,246,0.3)]",
    },
  };

  const config =
    severityConfig[severity as keyof typeof severityConfig] ||
    severityConfig.low;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
      }}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2
        ${config.bg} ${config.border} ${config.text} ${config.glow}
        backdrop-blur-sm font-semibold text-sm`}
    >
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [1, 0.7, 1],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <AlertTriangle className="w-4 h-4" />
      </motion.div>
      <span className="uppercase tracking-wide">{severity}</span>
    </motion.div>
  );
};

const Timer = ({ startTime }: { startTime: Date }) => {
  const [elapsed, setElapsed] = useState("");

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const diff = now.getTime() - startTime.getTime();
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setElapsed(
        `${hours.toString().padStart(2, "0")}:${minutes
          .toString()
          .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
      );
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  return (
    <div className="flex items-center gap-2 text-muted-foreground">
      <Clock className="w-4 h-4" />
      <span className="font-mono text-lg font-semibold">{elapsed}</span>
    </div>
  );
};

const ServiceStatusIcon = ({ status }: { status: string }) => {
  if (status === "operational")
    return <CheckCircle className="w-4 h-4 text-green-500" />;
  if (status === "degraded")
    return <AlertCircle className="w-4 h-4 text-yellow-500" />;
  if (status === "down") return <XCircle className="w-4 h-4 text-red-500" />;
  return <Activity className="w-4 h-4 text-muted-foreground" />;
};

const MetricCard = ({ metric }: { metric: Metric }) => {
  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="relative overflow-hidden rounded-xl p-4
        bg-gradient-to-br from-background/80 to-background/40
        backdrop-blur-md border border-border/50
        shadow-lg hover:shadow-xl transition-shadow"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
      <div className="relative flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs text-muted-foreground mb-1">{metric.label}</p>
          <p className="text-2xl font-bold text-foreground">{metric.value}</p>
          <div
            className={`flex items-center gap-1 mt-2 text-xs font-medium ${
              metric.change >= 0
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            <TrendingUp
              className={`w-3 h-3 ${metric.change < 0 ? "rotate-180" : ""}`}
            />
            <span>{Math.abs(metric.change)}%</span>
          </div>
        </div>
        <div className="p-2 rounded-lg bg-primary/10 text-primary">
          {metric.icon}
        </div>
      </div>
    </motion.div>
  );
};

const IncidentStatusPanel = ({
  incidentId = "INC-2024-001",
  title = "Database Performance Degradation",
  severity = "critical",
  startTime = new Date(Date.now() - 3600000),
  affectedServices = [
    { name: "API Gateway", status: "degraded", impact: "High latency" },
    { name: "Database Cluster", status: "down", impact: "Connection timeouts" },
    {
      name: "Authentication Service",
      status: "operational",
      impact: "No impact",
    },
    { name: "Email Service", status: "degraded", impact: "Delayed delivery" },
  ],
  description = "We are currently experiencing performance issues with our primary database cluster. Our team is actively investigating and working on a resolution.",
}: IncidentStatusPanelProps) => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const metrics: Metric[] = [
    {
      label: "Affected Users",
      value: "2,847",
      change: -12,
      icon: <Users className="w-5 h-5" />,
    },
    {
      label: "Error Rate",
      value: "23.4%",
      change: 156,
      icon: <Activity className="w-5 h-5" />,
    },
    {
      label: "Response Time",
      value: "4.2s",
      change: 340,
      icon: <Clock className="w-5 h-5" />,
    },
  ];

  if (isLoading) {
    return (
      <div className="w-full max-w-5xl mx-auto p-8">
        <Card className="relative overflow-hidden backdrop-blur-xl bg-background/95 border-border/50">
          <CardContent className="flex items-center justify-center h-96">
            <Loader2 className="w-12 h-12 animate-spin text-primary" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card
          className="relative overflow-hidden
          backdrop-blur-xl bg-background/95
          border-border/50 shadow-2xl"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-destructive/5 pointer-events-none" />

          <CardHeader className="relative space-y-4 pb-6">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <Badge variant="outline" className="font-mono text-xs">
                    {incidentId}
                  </Badge>
                  <SeverityBadge severity={severity} />
                </div>
                <CardTitle className="text-2xl md:text-3xl font-bold">
                  {title}
                </CardTitle>
                <p className="text-sm text-muted-foreground max-w-2xl">
                  {description}
                </p>
              </div>
              <div className="flex flex-col items-start md:items-end gap-2">
                <span className="text-xs text-muted-foreground">Duration</span>
                <Timer startTime={startTime} />
              </div>
            </div>
          </CardHeader>

          <CardContent className="relative space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {metrics.map((metric, index) => (
                <MetricCard key={index} metric={metric} />
              ))}
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" />
                Affected Services
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {affectedServices.map((service, index) => (
                  <motion.div
                    key={service.name}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 rounded-lg
                      bg-card/50 backdrop-blur-sm border border-border/50
                      hover:bg-card/80 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <ServiceStatusIcon status={service.status} />
                      <div>
                        <p className="font-medium text-sm">{service.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {service.impact}
                        </p>
                      </div>
                    </div>
                    <Badge
                      variant={
                        service.status === "operational"
                          ? "default"
                          : "destructive"
                      }
                      className="text-xs capitalize"
                    >
                      {service.status}
                    </Badge>
                  </motion.div>
                ))}
              </div>
            </div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="p-4 rounded-lg border border-primary/20
                bg-primary/5 backdrop-blur-sm"
            >
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-medium text-sm">Latest Update</p>
                  <p className="text-xs text-muted-foreground">
                    Our engineering team has identified the root cause and is
                    implementing a fix. We expect full service restoration
                    within the next 30 minutes.
                  </p>
                  <p className="text-xs text-muted-foreground/70 mt-2">
                    Last updated: {new Date().toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default IncidentStatusPanel;
