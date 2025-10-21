/**
 * ActivityFeed Demo Component
 *
 * Demonstrates the enhanced ActivityFeed with auto-scroll functionality
 */

"use client";

import React from "react";
import ActivityFeed from "./ActivityFeed";

interface AgentAction {
  id: string;
  agent_type:
    | "detection"
    | "diagnosis"
    | "prediction"
    | "resolution"
    | "communication";
  title: string;
  description: string;
  timestamp: string;
  confidence?: number;
  status: "pending" | "in_progress" | "completed" | "failed";
  details?: Record<string, any>;
  duration?: number;
  impact?: string;
}

const sampleTitles = [
  "System Alert Detected",
  "Analyzing Metrics",
  "Processing Incident",
  "Executing Resolution",
  "Monitoring Recovery",
  "Updating Status",
  "Coordinating Response",
  "Validating Fix",
  "Generating Report",
  "Notifying Teams",
];

const sampleDescriptions = [
  "High CPU usage detected on server cluster",
  "Analyzing system logs and performance metrics",
  "Processing incident data and determining severity",
  "Executing automated remediation procedures",
  "Monitoring system recovery and validation",
  "Updating incident status and progress",
  "Coordinating with other agents for consensus",
  "Validating that the fix has resolved the issue",
  "Generating comprehensive incident report",
  "Notifying relevant teams and stakeholders",
];

export default function ActivityFeedDemo() {
  const [actions, setActions] = React.useState<AgentAction[]>([
    {
      id: "1",
      agent_type: "detection",
      title: "System Initialized",
      description: "Multi-agent system ready for autonomous incident response",
      timestamp: new Date().toISOString(),
      confidence: 1.0,
      status: "completed",
      duration: 1200,
      impact: "System Ready",
    },
  ]);

  const [isRunning, setIsRunning] = React.useState(false);
  const [messageFrequency, setMessageFrequency] = React.useState(2000);

  // Simulate real-time updates
  React.useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      if (Math.random() < 0.6) {
        // 60% chance of new message
        const agentTypes: AgentAction["agent_type"][] = [
          "detection",
          "diagnosis",
          "prediction",
          "resolution",
          "communication",
        ];

        const statuses: AgentAction["status"][] = [
          "pending",
          "in_progress",
          "completed",
          "failed",
        ];

        const newAction: AgentAction = {
          id: crypto.randomUUID(),
          agent_type: agentTypes[Math.floor(Math.random() * agentTypes.length)],
          title: sampleTitles[Math.floor(Math.random() * sampleTitles.length)],
          description:
            sampleDescriptions[
              Math.floor(Math.random() * sampleDescriptions.length)
            ],
          timestamp: new Date().toISOString(),
          confidence: Math.random(),
          status: statuses[Math.floor(Math.random() * statuses.length)],
          duration: Math.floor(Math.random() * 5000) + 500,
          impact: ["Low", "Medium", "High", "Critical"][
            Math.floor(Math.random() * 4)
          ],
          details: {
            severity: ["low", "medium", "high"][Math.floor(Math.random() * 3)],
            affected_services: Math.floor(Math.random() * 5) + 1,
            estimated_impact: "$" + Math.floor(Math.random() * 10000),
            region: ["us-east-1", "us-west-2", "eu-west-1"][
              Math.floor(Math.random() * 3)
            ],
          },
        };

        setActions((prev) => [newAction, ...prev].slice(0, 100)); // Keep last 100 messages
      }
    }, messageFrequency);

    return () => clearInterval(interval);
  }, [isRunning, messageFrequency]);

  const handleActionClick = (action: AgentAction) => {
    console.log("Action clicked:", action);
    alert(
      `Clicked on: ${action.title}\nAgent: ${action.agent_type}\nStatus: ${action.status}`
    );
  };

  const startDemo = () => setIsRunning(true);
  const stopDemo = () => setIsRunning(false);
  const clearActions = () => {
    setActions([
      {
        id: "1",
        agent_type: "detection",
        title: "System Initialized",
        description:
          "Multi-agent system ready for autonomous incident response",
        timestamp: new Date().toISOString(),
        confidence: 1.0,
        status: "completed",
        duration: 1200,
        impact: "System Ready",
      },
    ]);
  };

  const triggerBurst = () => {
    // Add 10 messages quickly to test high-frequency mode
    for (let i = 0; i < 10; i++) {
      setTimeout(() => {
        const newAction: AgentAction = {
          id: `burst-${Date.now()}-${i}`,
          agent_type: "detection",
          title: `Burst Message ${i + 1}`,
          description: "Testing high-frequency message handling",
          timestamp: new Date().toISOString(),
          confidence: Math.random(),
          status: "in_progress",
          duration: 100,
          impact: "Test",
        };
        setActions((prev) => [newAction, ...prev].slice(0, 100));
      }, i * 100);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Enhanced ActivityFeed Demo</h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          This demo shows the enhanced ActivityFeed component with auto-scroll
          functionality. The feed automatically scrolls to show new messages,
          pauses when you scroll up, and resumes when you return to the bottom.
        </p>
      </div>

      {/* Controls */}
      <div className="bg-card border rounded-lg p-4 space-y-4">
        <h2 className="text-lg font-semibold">Demo Controls</h2>

        <div className="flex flex-wrap gap-4 items-center">
          <button
            onClick={startDemo}
            disabled={isRunning}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            Start Demo
          </button>

          <button
            onClick={stopDemo}
            disabled={!isRunning}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
          >
            Stop Demo
          </button>

          <button
            onClick={clearActions}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Clear Messages
          </button>

          <button
            onClick={triggerBurst}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Trigger Burst (10 messages)
          </button>
        </div>

        <div className="flex items-center gap-4">
          <label className="text-sm font-medium">Message Frequency:</label>
          <select
            value={messageFrequency}
            onChange={(e) => setMessageFrequency(Number(e.target.value))}
            className="px-3 py-1 border rounded"
          >
            <option value={500}>Very Fast (0.5s)</option>
            <option value={1000}>Fast (1s)</option>
            <option value={2000}>Normal (2s)</option>
            <option value={3000}>Slow (3s)</option>
            <option value={5000}>Very Slow (5s)</option>
          </select>
        </div>

        <div className="text-sm text-muted-foreground">
          <p>
            <strong>Status:</strong> {isRunning ? "Running" : "Stopped"}
          </p>
          <p>
            <strong>Total Messages:</strong> {actions.length}
          </p>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">
          How to Test Auto-Scroll:
        </h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>1. Click "Start Demo" to begin generating messages</li>
          <li>2. Watch the feed auto-scroll to show new messages</li>
          <li>
            3. Scroll up manually - notice the "Auto-scroll Paused" indicator
          </li>
          <li>4. Scroll back to bottom - auto-scroll resumes automatically</li>
          <li>
            5. Try "Trigger Burst" to test high-frequency performance mode
          </li>
          <li>6. Click on any message to test the click handler</li>
        </ul>
      </div>

      {/* ActivityFeed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Standard Mode</h3>
          <ActivityFeed
            actions={actions}
            autoScrollEnabled={true}
            onActionClick={handleActionClick}
            maxItems={20}
          />
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Auto-scroll Disabled</h3>
          <ActivityFeed
            actions={actions}
            autoScrollEnabled={false}
            onActionClick={handleActionClick}
            maxItems={20}
          />
        </div>
      </div>
    </div>
  );
}
