import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "next-themes";
import {
  Bell,
  Search,
  Settings,
  AlertTriangle,
  Activity,
  Users,
  ChevronDown,
  Shield,
  Zap,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Input } from "./ui/input";

// HyperText Component for Incident Commander
interface HyperTextProps {
  text: string;
  duration?: number;
  className?: string;
  animateOnLoad?: boolean;
  trigger?: boolean;
}

const alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const getRandomInt = (max: number) => Math.floor(Math.random() * max);

function HyperText({
  text,
  duration = 800,
  className,
  animateOnLoad = true,
  trigger = false,
}: HyperTextProps) {
  const [displayText, setDisplayText] = React.useState(text.split(""));
  const [triggerAnim, setTriggerAnim] = React.useState(trigger);
  const iterations = React.useRef(0);
  const isFirstRender = React.useRef(true);

  const triggerAnimation = () => {
    iterations.current = 0;
    setTriggerAnim(true);
  };

  React.useEffect(() => {
    const interval = setInterval(() => {
      if (!animateOnLoad && isFirstRender.current) {
        clearInterval(interval);
        isFirstRender.current = false;
        return;
      }
      if (iterations.current < text.length) {
        setDisplayText((t) =>
          t.map((l, i) =>
            l === " "
              ? l
              : i <= iterations.current
              ? text[i]
              : alphabets[getRandomInt(26)]
          )
        );
        iterations.current = iterations.current + 0.1;
      } else {
        setTriggerAnim(false);
        clearInterval(interval);
      }
    }, duration / (text.length * 10));
    return () => clearInterval(interval);
  }, [text, duration, triggerAnim, animateOnLoad]);

  return (
    <div
      className="flex scale-100 cursor-default overflow-hidden"
      onMouseEnter={triggerAnimation}
    >
      <AnimatePresence mode="wait">
        {displayText.map((letter, i) => (
          <motion.span
            key={i}
            className={`font-mono ${letter === " " ? "w-3" : ""} ${className}`}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 3 }}
          >
            {letter.toUpperCase()}
          </motion.span>
        ))}
      </AnimatePresence>
    </div>
  );
}

// Enhanced Status Indicator for Incident Commander
interface StatusIndicatorProps {
  variant?: "autonomous" | "monitoring" | "incident" | "maintenance";
  text?: string;
  scale?: number;
  pulse?: boolean;
}

function StatusIndicator({
  variant = "autonomous",
  text = "AUTONOMOUS",
  scale = 1,
  pulse = true,
}: StatusIndicatorProps) {
  const { theme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted ? theme === "dark" : true;

  const getColors = () => {
    switch (variant) {
      case "autonomous":
        return {
          gradientStart: isDark ? "#00d4ff" : "#0066ff",
          gradientEnd: isDark ? "#0066ff" : "#0052cc",
          stroke: isDark ? "#00d4ff" : "#0066ff",
          text: isDark ? "text-cyan-300" : "text-blue-700",
          glow: "rgba(0, 212, 255, 0.3)",
        };
      case "monitoring":
        return {
          gradientStart: isDark ? "#4ade80" : "#16a34a",
          gradientEnd: isDark ? "#15803d" : "#166534",
          stroke: isDark ? "#4ade80" : "#16a34a",
          text: isDark ? "text-green-300" : "text-green-700",
          glow: "rgba(74, 222, 128, 0.3)",
        };
      case "incident":
        return {
          gradientStart: isDark ? "#f87171" : "#dc2626",
          gradientEnd: isDark ? "#b91c1c" : "#991b1b",
          stroke: isDark ? "#f87171" : "#dc2626",
          text: isDark ? "text-red-300" : "text-red-700",
          glow: "rgba(248, 113, 113, 0.3)",
        };
      case "maintenance":
        return {
          gradientStart: isDark ? "#fbbf24" : "#d97706",
          gradientEnd: isDark ? "#b45309" : "#92400e",
          stroke: isDark ? "#fbbf24" : "#d97706",
          text: isDark ? "text-amber-300" : "text-amber-700",
          glow: "rgba(251, 191, 36, 0.3)",
        };
      default:
        return {
          gradientStart: isDark ? "#00d4ff" : "#0066ff",
          gradientEnd: isDark ? "#0066ff" : "#0052cc",
          stroke: isDark ? "#00d4ff" : "#0066ff",
          text: isDark ? "text-cyan-300" : "text-blue-700",
          glow: "rgba(0, 212, 255, 0.3)",
        };
    }
  };

  const colors = getColors();

  return (
    <motion.div
      className="relative"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      style={{ transform: `scale(${scale})` }}
    >
      <div className="relative">
        <svg
          width="200"
          height="40"
          viewBox="0 0 200 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient
              id={`statusGradient-${variant}`}
              x1="0%"
              y1="0%"
              x2="0%"
              y2="100%"
            >
              <stop
                offset="0%"
                stopColor={colors.gradientStart}
                stopOpacity="0.9"
              />
              <stop
                offset="100%"
                stopColor={colors.gradientEnd}
                stopOpacity="0.1"
              />
            </linearGradient>
            {pulse && (
              <filter id={`glow-${variant}`}>
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            )}
          </defs>
          <motion.path
            d="M0 0H200V28H10L0 18V0Z"
            fill={`url(#statusGradient-${variant})`}
            stroke={colors.stroke}
            strokeWidth="1.5"
            filter={pulse ? `url(#glow-${variant})` : undefined}
            animate={
              pulse
                ? {
                    filter: [
                      `drop-shadow(0 0 5px ${colors.glow})`,
                      `drop-shadow(0 0 15px ${colors.glow})`,
                      `drop-shadow(0 0 5px ${colors.glow})`,
                    ],
                  }
                : {}
            }
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
        </svg>

        <div className="absolute inset-0 flex items-center justify-start pl-4 pb-2">
          <HyperText
            text={text}
            className={`${colors.text} text-sm font-mono tracking-wider font-bold`}
            duration={1200}
            animateOnLoad={true}
            trigger={true}
          />
        </div>
      </div>
    </motion.div>
  );
}

// Incident Commander Dashboard Header
interface IncidentCommanderHeaderProps {
  title?: string;
  subtitle?: string;
  user?: {
    name: string;
    email: string;
    avatar: string;
    role: string;
  };
  stats?: {
    activeIncidents: number;
    resolvedToday: number;
    mttrReduction: number;
    agentsActive: number;
  };
  systemStatus?: "autonomous" | "monitoring" | "incident" | "maintenance";
  onTriggerScenario?: (scenario: string) => void;
}

function IncidentCommanderHeader({
  title = "Autonomous Incident Commander",
  subtitle = "AI-Powered Multi-Agent Response System",
  user = {
    name: "System Admin",
    email: "admin@company.com",
    avatar: "https://i.pravatar.cc/150?u=admin",
    role: "Incident Commander",
  },
  stats = {
    activeIncidents: 0,
    resolvedToday: 12,
    mttrReduction: 95,
    agentsActive: 5,
  },
  systemStatus = "autonomous",
  onTriggerScenario,
}: IncidentCommanderHeaderProps) {
  const [searchFocused, setSearchFocused] = React.useState(false);

  return (
    <header className="relative w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Enhanced Glassmorphism overlay with gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-blue-500/5 to-purple-500/5 pointer-events-none" />

      <div className="relative">
        {/* Top section */}
        <div className="flex items-center justify-between px-6 py-4">
          {/* Left section - Title, Logo and Status */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <motion.div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg"
                whileHover={{ scale: 1.05, rotate: 5 }}
                transition={{ type: "spring", stiffness: 400, damping: 10 }}
              >
                <Shield className="w-6 h-6 text-white" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold text-foreground tracking-tight bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent">
                  {title}
                </h1>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {subtitle}
                </p>
              </div>
            </div>

            <div className="hidden lg:block">
              <StatusIndicator
                variant={systemStatus}
                text={systemStatus.toUpperCase()}
                scale={0.9}
                pulse={systemStatus === "incident"}
              />
            </div>
          </div>

          {/* Right section - Actions and User */}
          <div className="flex items-center gap-3">
            {/* Enhanced Search */}
            <motion.div
              initial={false}
              animate={{ width: searchFocused ? 320 : 240 }}
              className="relative hidden md:block"
            >
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search incidents, agents, metrics..."
                className="pl-9 bg-background/50 border-border/50 focus:border-cyan-500/50 transition-all"
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
              />
            </motion.div>

            {/* Enhanced Notifications */}
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              {stats.activeIncidents > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-semibold"
                >
                  {stats.activeIncidents}
                </motion.span>
              )}
            </Button>

            {/* Quick Actions */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="relative">
                  <Zap className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-56 bg-background/95 backdrop-blur"
              >
                <DropdownMenuItem
                  onClick={() => onTriggerScenario?.("database")}
                >
                  <AlertTriangle className="mr-2 h-4 w-4 text-amber-500" />
                  Trigger Database Cascade
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onTriggerScenario?.("ddos")}>
                  <Shield className="mr-2 h-4 w-4 text-red-500" />
                  Simulate DDoS Attack
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onTriggerScenario?.("memory")}>
                  <Activity className="mr-2 h-4 w-4 text-orange-500" />
                  Memory Leak Scenario
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Settings */}
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
            </Button>

            {/* Enhanced User Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2 px-2">
                  <Avatar className="h-8 w-8 border-2 border-cyan-500/20">
                    <AvatarImage src={user.avatar} alt={user.name} />
                    <AvatarFallback className="bg-gradient-to-br from-cyan-500 to-blue-600 text-white">
                      {user.name.charAt(0)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="hidden lg:block text-left">
                    <p className="text-sm font-medium">{user.name}</p>
                    <p className="text-xs text-muted-foreground">{user.role}</p>
                  </div>
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-56 bg-background/95 backdrop-blur"
              >
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Users className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-600">
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Enhanced Bottom section - Stats with better visual hierarchy */}
        <div className="border-t border-border/40 bg-muted/20 backdrop-blur">
          <div className="px-6 py-4 flex items-center gap-8">
            <motion.div
              className="flex items-center gap-3"
              whileHover={{ scale: 1.02 }}
            >
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-red-500/10 to-red-600/10 border border-red-500/20">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">
                  Active Incidents
                </p>
                <p className="text-xl font-bold text-foreground">
                  {stats.activeIncidents}
                </p>
              </div>
            </motion.div>

            <div className="h-10 w-px bg-border/50" />

            <motion.div
              className="flex items-center gap-3"
              whileHover={{ scale: 1.02 }}
            >
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20">
                <Activity className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">
                  Resolved Today
                </p>
                <p className="text-xl font-bold text-foreground">
                  {stats.resolvedToday}
                </p>
              </div>
            </motion.div>

            <div className="h-10 w-px bg-border/50" />

            <motion.div
              className="flex items-center gap-3"
              whileHover={{ scale: 1.02 }}
            >
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/10 to-cyan-600/10 border border-cyan-500/20">
                <Zap className="h-5 w-5 text-cyan-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">
                  MTTR Reduction
                </p>
                <p className="text-xl font-bold text-foreground">
                  {stats.mttrReduction}%
                </p>
              </div>
            </motion.div>

            <div className="h-10 w-px bg-border/50" />

            <motion.div
              className="flex items-center gap-3"
              whileHover={{ scale: 1.02 }}
            >
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20">
                <Users className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">
                  Agents Active
                </p>
                <p className="text-xl font-bold text-foreground">
                  {stats.agentsActive}
                </p>
              </div>
            </motion.div>

            <div className="ml-auto flex items-center gap-3">
              <Badge
                variant="outline"
                className="bg-background/50 border-border/50 text-xs"
              >
                Last sync: {new Date().toLocaleTimeString()}
              </Badge>
              <motion.div
                className="w-2 h-2 rounded-full bg-green-500"
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default IncidentCommanderHeader;
