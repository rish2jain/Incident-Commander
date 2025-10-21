/**
 * AutoScrollExample - Simple example demonstrating auto-scroll functionality
 *
 * This component shows how to integrate the auto-scroll utilities with
 * a basic message feed component.
 */

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, Plus, Pause, Play, RotateCcw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { useAutoScroll } from "../lib/hooks/useAutoScroll";
import { FloatingScrollIndicator } from "./ui/scroll-indicator";

interface Message {
  id: string;
  text: string;
  timestamp: Date;
  type: "system" | "user" | "agent";
}

const messageTemplates = [
  "Analyzing system metrics...",
  "Detected anomaly in response times",
  "Initiating automated recovery sequence",
  "Scaling resources to handle increased load",
  "Monitoring system stability",
  "Recovery completed successfully",
  "System performance restored to normal levels",
  "Updating incident status",
  "Notifying stakeholders of resolution",
  "Incident closed - all systems operational",
];

export function AutoScrollExample() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Auto-scroll system initialized",
      timestamp: new Date(),
      type: "system",
    },
  ]);

  const [isAutoAdding, setIsAutoAdding] = useState(false);
  const [addingSpeed, setAddingSpeed] = useState(2000); // ms between messages

  // Use auto-scroll hook
  const {
    scrollRef,
    scrollState,
    isNearBottom,
    isPaused,
    scrollToBottom,
    pauseAutoScroll,
    resumeAutoScroll,
    shouldShowScrollToBottom,
  } = useAutoScroll({
    enabled: true,
    dependencies: [messages.length],
    threshold: 50,
    resumeDelay: 1000,
  });

  // Auto-add messages for demonstration
  useEffect(() => {
    if (!isAutoAdding) return;

    const interval = setInterval(() => {
      const template =
        messageTemplates[Math.floor(Math.random() * messageTemplates.length)];
      const newMessage: Message = {
        id: Date.now().toString(),
        text: template,
        timestamp: new Date(),
        type: Math.random() > 0.7 ? "agent" : "system",
      };

      setMessages((prev) => [...prev, newMessage]);
    }, addingSpeed);

    return () => clearInterval(interval);
  }, [isAutoAdding, addingSpeed]);

  const addMessage = () => {
    const template =
      messageTemplates[Math.floor(Math.random() * messageTemplates.length)];
    const newMessage: Message = {
      id: Date.now().toString(),
      text: template,
      timestamp: new Date(),
      type: "user",
    };

    setMessages((prev) => [...prev, newMessage]);
  };

  const clearMessages = () => {
    setMessages([
      {
        id: "1",
        text: "Messages cleared - auto-scroll system ready",
        timestamp: new Date(),
        type: "system",
      },
    ]);
  };

  const getMessageTypeColor = (type: Message["type"]) => {
    switch (type) {
      case "system":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20";
      case "agent":
        return "bg-green-500/10 text-green-500 border-green-500/20";
      case "user":
        return "bg-purple-500/10 text-purple-500 border-purple-500/20";
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20";
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">Auto-Scroll Demo</h1>
        <p className="text-muted-foreground">
          Demonstrates automatic scrolling behavior with user interaction
          detection
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button onClick={addMessage} variant="outline">
              <Plus className="w-4 h-4 mr-2" />
              Add Message
            </Button>

            <Button
              onClick={() => setIsAutoAdding(!isAutoAdding)}
              variant={isAutoAdding ? "destructive" : "default"}
            >
              {isAutoAdding ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Stop Auto-Add
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start Auto-Add
                </>
              )}
            </Button>

            <Button onClick={clearMessages} variant="outline">
              <RotateCcw className="w-4 h-4 mr-2" />
              Clear Messages
            </Button>

            {isPaused ? (
              <Button onClick={resumeAutoScroll} variant="outline">
                <Play className="w-4 h-4 mr-2" />
                Resume Auto-Scroll
              </Button>
            ) : (
              <Button onClick={pauseAutoScroll} variant="outline">
                <Pause className="w-4 h-4 mr-2" />
                Pause Auto-Scroll
              </Button>
            )}

            <Button onClick={() => scrollToBottom()} variant="outline">
              Scroll to Bottom
            </Button>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <label className="flex items-center gap-2">
              Speed:
              <select
                value={addingSpeed}
                onChange={(e) => setAddingSpeed(Number(e.target.value))}
                className="px-2 py-1 border rounded"
              >
                <option value={500}>Fast (0.5s)</option>
                <option value={1000}>Medium (1s)</option>
                <option value={2000}>Slow (2s)</option>
                <option value={5000}>Very Slow (5s)</option>
              </select>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Status Display */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Badge variant={isNearBottom ? "default" : "secondary"}>
                {isNearBottom ? "Near Bottom" : "Scrolled Up"}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={isPaused ? "destructive" : "default"}>
                {isPaused ? "Paused" : "Active"}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{messages.length} Messages</Badge>
            </div>
            <div className="flex items-center gap-2">
              <Badge
                variant={scrollState.isUserScrolling ? "secondary" : "outline"}
              >
                {scrollState.isUserScrolling ? "User Scrolling" : "Idle"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Message Feed */}
      <Card className="relative">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Message Feed</span>
            <Badge variant="outline">{messages.length} messages</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea
            className="h-[400px] p-4"
            ref={scrollRef as React.RefObject<HTMLDivElement>}
          >
            <AnimatePresence initial={false}>
              <div className="space-y-3">
                {messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -20, scale: 0.95 }}
                    transition={{
                      duration: 0.3,
                      delay: index === messages.length - 1 ? 0.1 : 0,
                    }}
                    className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 border border-border/50"
                  >
                    <div
                      className={`w-2 h-2 rounded-full mt-2 ${
                        message.type === "system"
                          ? "bg-blue-500"
                          : message.type === "agent"
                          ? "bg-green-500"
                          : "bg-purple-500"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant="outline"
                          className={`text-xs ${getMessageTypeColor(
                            message.type
                          )}`}
                        >
                          {message.type}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-foreground">{message.text}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </AnimatePresence>
          </ScrollArea>

          {/* Floating Scroll Indicator */}
          <FloatingScrollIndicator
            isVisible={shouldShowScrollToBottom}
            isPaused={isPaused}
            isNearBottom={isNearBottom}
            messageCount={messages.length}
            onScrollToBottom={scrollToBottom}
            hasNewMessages={!isNearBottom && messages.length > 1}
          />
        </CardContent>
      </Card>

      {/* Debug Info */}
      <Card>
        <CardHeader>
          <CardTitle>Debug Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm font-mono">
            <div>
              <h4 className="font-semibold mb-2">Scroll State:</h4>
              <ul className="space-y-1">
                <li>
                  Auto-scroll enabled:{" "}
                  {scrollState.isAutoScrollEnabled.toString()}
                </li>
                <li>
                  User scrolling: {scrollState.isUserScrolling.toString()}
                </li>
                <li>Near bottom: {scrollState.isNearBottom.toString()}</li>
                <li>Paused: {scrollState.isPaused.toString()}</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Metrics:</h4>
              <ul className="space-y-1">
                <li>Message count: {scrollState.messageCount}</li>
                <li>Last scroll position: {scrollState.lastScrollPosition}</li>
                <li>Last interaction: {scrollState.lastUserInteraction}</li>
                <li>
                  Should show scroll button:{" "}
                  {shouldShowScrollToBottom.toString()}
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
