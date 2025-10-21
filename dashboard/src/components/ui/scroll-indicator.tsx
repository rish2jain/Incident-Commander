/**
 * ScrollIndicator - Visual component for showing auto-scroll state and controls
 *
 * Features:
 * - Visual indicator when auto-scroll is paused
 * - "Scroll to latest" button
 * - Smooth animations and transitions
 * - Customizable appearance
 */

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Pause, Play, ArrowDown } from "lucide-react";
import { Button } from "./button";
import { Badge } from "./badge";
import { cn } from "../../lib/utils";

export interface ScrollIndicatorProps {
  isVisible: boolean;
  isPaused: boolean;
  isNearBottom: boolean;
  messageCount?: number;
  onScrollToBottom: () => void;
  onResume?: () => void;
  onPause?: () => void;
  className?: string;
  position?: "top" | "bottom" | "floating";
  variant?: "minimal" | "detailed" | "compact";
}

const positionStyles = {
  top: "top-4 left-1/2 -translate-x-1/2",
  bottom: "bottom-4 left-1/2 -translate-x-1/2",
  floating: "bottom-6 right-6",
};

const variantStyles = {
  minimal: "px-3 py-2",
  detailed: "px-4 py-3",
  compact: "px-2 py-1",
};

export function ScrollIndicator({
  isVisible,
  isPaused,
  isNearBottom,
  messageCount,
  onScrollToBottom,
  onResume,
  onPause,
  className,
  position = "floating",
  variant = "detailed",
}: ScrollIndicatorProps) {
  const showScrollButton = isVisible && !isNearBottom;
  const showPauseIndicator = isPaused && isVisible;

  return (
    <AnimatePresence>
      {(showScrollButton || showPauseIndicator) && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.9 }}
          transition={{
            type: "spring",
            stiffness: 400,
            damping: 25,
          }}
          className={cn(
            "fixed z-50 flex items-center gap-2 bg-background/95 backdrop-blur-sm border border-border/50 rounded-lg shadow-lg",
            positionStyles[position],
            variantStyles[variant],
            className
          )}
        >
          {/* Pause Indicator */}
          {showPauseIndicator && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: "auto", opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="flex items-center gap-2"
            >
              <div className="flex items-center gap-1">
                <Pause className="w-3 h-3 text-amber-500" />
                {variant !== "compact" && (
                  <span className="text-xs text-muted-foreground">
                    Auto-scroll paused
                  </span>
                )}
              </div>

              {onResume && variant === "detailed" && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={onResume}
                  className="h-6 px-2 text-xs"
                >
                  <Play className="w-3 h-3 mr-1" />
                  Resume
                </Button>
              )}
            </motion.div>
          )}

          {/* Scroll to Bottom Button */}
          {showScrollButton && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: "auto", opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="flex items-center gap-2"
            >
              <Button
                size="sm"
                onClick={onScrollToBottom}
                className="h-8 px-3 bg-primary/90 hover:bg-primary text-primary-foreground"
              >
                <ArrowDown className="w-3 h-3 mr-1" />
                {variant === "compact" ? (
                  "Latest"
                ) : (
                  <>
                    Scroll to latest
                    {messageCount && variant === "detailed" && (
                      <Badge
                        variant="secondary"
                        className="ml-2 h-4 px-1 text-xs"
                      >
                        {messageCount}
                      </Badge>
                    )}
                  </>
                )}
              </Button>

              {onPause && variant === "detailed" && !isPaused && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={onPause}
                  className="h-6 px-2 text-xs"
                >
                  <Pause className="w-3 h-3" />
                </Button>
              )}
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Floating scroll indicator with pulse animation for new messages
 */
export function FloatingScrollIndicator({
  isVisible,
  isPaused,
  isNearBottom,
  messageCount,
  onScrollToBottom,
  hasNewMessages = false,
  className,
}: Omit<ScrollIndicatorProps, "position" | "variant"> & {
  hasNewMessages?: boolean;
}) {
  return (
    <AnimatePresence>
      {isVisible && !isNearBottom && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: 20 }}
          className={cn("fixed bottom-6 right-6 z-50", className)}
        >
          <motion.div
            animate={
              hasNewMessages
                ? {
                    scale: [1, 1.05, 1],
                    boxShadow: [
                      "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                      "0 10px 15px -3px rgba(59, 130, 246, 0.3)",
                      "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    ],
                  }
                : {}
            }
            transition={{
              duration: 0.6,
              repeat: hasNewMessages ? Infinity : 0,
              repeatDelay: 1,
            }}
          >
            <Button
              size="lg"
              onClick={onScrollToBottom}
              className="h-12 w-12 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg"
            >
              <ChevronDown className="w-5 h-5" />
            </Button>
          </motion.div>

          {messageCount && messageCount > 0 && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-2 -right-2"
            >
              <Badge
                variant="destructive"
                className="h-6 min-w-6 rounded-full flex items-center justify-center text-xs font-medium"
              >
                {messageCount > 99 ? "99+" : messageCount}
              </Badge>
            </motion.div>
          )}

          {isPaused && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-1 -left-1"
            >
              <div className="w-4 h-4 bg-amber-500 rounded-full flex items-center justify-center">
                <Pause className="w-2 h-2 text-white" />
              </div>
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Compact scroll indicator for inline use
 */
export function InlineScrollIndicator({
  isVisible,
  isPaused,
  onScrollToBottom,
  onResume,
  className,
}: Pick<
  ScrollIndicatorProps,
  "isVisible" | "isPaused" | "onScrollToBottom" | "onResume" | "className"
>) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className={cn(
            "flex items-center justify-between p-2 bg-muted/50 border-t border-border/50",
            className
          )}
        >
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {isPaused ? (
              <>
                <Pause className="w-4 h-4 text-amber-500" />
                Auto-scroll paused
              </>
            ) : (
              <>
                <ArrowDown className="w-4 h-4 text-blue-500" />
                New messages available
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            {isPaused && onResume && (
              <Button size="sm" variant="ghost" onClick={onResume}>
                Resume
              </Button>
            )}
            <Button size="sm" onClick={onScrollToBottom}>
              Scroll to latest
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
