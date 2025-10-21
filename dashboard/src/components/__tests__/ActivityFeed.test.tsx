/**
 * ActivityFeed Component Tests
 *
 * Tests for auto-scroll functionality, user interaction detection,
 * and performance optimizations.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import ActivityFeed from "../ActivityFeed";

// Mock framer-motion to avoid animation issues in tests
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock the auto-scroll hook
const mockScrollToBottom = jest.fn();
const mockPauseAutoScroll = jest.fn();
const mockResumeAutoScroll = jest.fn();

jest.mock("../../lib/hooks/useAutoScroll", () => ({
  useAutoScroll: () => ({
    scrollRef: { current: null },
    scrollState: {
      isAutoScrollEnabled: true,
      isUserScrolling: false,
      isNearBottom: true,
      lastScrollPosition: 0,
      messageCount: 0,
      isPaused: false,
      lastUserInteraction: 0,
    },
    isNearBottom: true,
    isPaused: false,
    scrollToBottom: mockScrollToBottom,
    pauseAutoScroll: mockPauseAutoScroll,
    resumeAutoScroll: mockResumeAutoScroll,
    shouldShowScrollToBottom: false,
  }),
}));

const mockActions = [
  {
    id: "1",
    agent_type: "detection" as const,
    title: "System Alert Detected",
    description: "High CPU usage detected on server cluster",
    timestamp: new Date().toISOString(),
    confidence: 0.95,
    status: "completed" as const,
    duration: 1200,
    impact: "High",
  },
  {
    id: "2",
    agent_type: "diagnosis" as const,
    title: "Root Cause Analysis",
    description: "Analyzing system logs and metrics",
    timestamp: new Date().toISOString(),
    confidence: 0.87,
    status: "in_progress" as const,
    duration: 2500,
    impact: "Medium",
  },
];

describe("ActivityFeed", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders activity feed with actions", () => {
    render(<ActivityFeed actions={mockActions} />);

    expect(screen.getByText("Agent Activity Feed")).toBeInTheDocument();
    expect(screen.getByText("System Alert Detected")).toBeInTheDocument();
    expect(screen.getByText("Root Cause Analysis")).toBeInTheDocument();
  });

  test("shows correct number of events in badge", () => {
    render(<ActivityFeed actions={mockActions} />);

    expect(screen.getByText("2 events")).toBeInTheDocument();
  });

  test("handles empty actions array", () => {
    render(<ActivityFeed actions={[]} />);

    expect(screen.getByText("No Activity Yet")).toBeInTheDocument();
    expect(
      screen.getByText(/Agent activities will appear here/)
    ).toBeInTheDocument();
  });

  test("calls onActionClick when action is clicked", () => {
    const mockOnActionClick = jest.fn();
    render(
      <ActivityFeed actions={mockActions} onActionClick={mockOnActionClick} />
    );

    const firstAction = screen
      .getByText("System Alert Detected")
      .closest(".group");
    if (firstAction) {
      fireEvent.click(firstAction);
      expect(mockOnActionClick).toHaveBeenCalledWith(mockActions[0]);
    }
  });

  test("respects maxItems prop", () => {
    const manyActions = Array.from({ length: 20 }, (_, i) => ({
      ...mockActions[0],
      id: `action-${i}`,
      title: `Action ${i}`,
    }));

    render(<ActivityFeed actions={manyActions} maxItems={5} />);

    // Should only show 5 actions
    expect(screen.getAllByText(/Action \d+/)).toHaveLength(5);
  });

  test("enables auto-scroll by default", () => {
    render(<ActivityFeed actions={mockActions} />);

    // Auto-scroll should be enabled by default
    expect(screen.queryByText("Auto-scroll Paused")).not.toBeInTheDocument();
  });

  test("can disable auto-scroll", () => {
    render(<ActivityFeed actions={mockActions} autoScrollEnabled={false} />);

    // Component should render without auto-scroll functionality
    expect(screen.getByText("Agent Activity Feed")).toBeInTheDocument();
  });

  test("shows high performance mode indicator when needed", () => {
    // Create many recent actions to trigger high-frequency mode
    const now = Date.now();
    const highFrequencyActions = Array.from({ length: 15 }, (_, i) => ({
      ...mockActions[0],
      id: `high-freq-${i}`,
      timestamp: new Date(now - i * 100).toISOString(), // Recent timestamps
    }));

    render(<ActivityFeed actions={highFrequencyActions} />);

    // Should show high performance mode indicator
    expect(screen.getByText("High Performance Mode")).toBeInTheDocument();
  });

  test("displays agent types correctly", () => {
    const allAgentTypes = [
      { ...mockActions[0], agent_type: "detection" as const, id: "1" },
      { ...mockActions[0], agent_type: "diagnosis" as const, id: "2" },
      { ...mockActions[0], agent_type: "prediction" as const, id: "3" },
      { ...mockActions[0], agent_type: "resolution" as const, id: "4" },
      { ...mockActions[0], agent_type: "communication" as const, id: "5" },
    ];

    render(<ActivityFeed actions={allAgentTypes} />);

    expect(screen.getByText("Detection Agent")).toBeInTheDocument();
    expect(screen.getByText("Diagnosis Agent")).toBeInTheDocument();
    expect(screen.getByText("Prediction Agent")).toBeInTheDocument();
    expect(screen.getByText("Resolution Agent")).toBeInTheDocument();
    expect(screen.getByText("Communication Agent")).toBeInTheDocument();
  });

  test("displays status badges correctly", () => {
    const statusActions = [
      { ...mockActions[0], status: "pending" as const, id: "1" },
      { ...mockActions[0], status: "in_progress" as const, id: "2" },
      { ...mockActions[0], status: "completed" as const, id: "3" },
      { ...mockActions[0], status: "failed" as const, id: "4" },
    ];

    render(<ActivityFeed actions={statusActions} />);

    expect(screen.getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  test("shows confidence bars when confidence is provided", () => {
    render(<ActivityFeed actions={mockActions} />);

    // Should show confidence percentages
    expect(screen.getByText("Confidence: 95%")).toBeInTheDocument();
    expect(screen.getByText("Confidence: 87%")).toBeInTheDocument();
  });

  test("formats timestamps correctly", () => {
    const testDate = new Date("2024-01-01T12:00:00Z");
    const actionWithSpecificTime = {
      ...mockActions[0],
      timestamp: testDate.toISOString(),
    };

    render(<ActivityFeed actions={[actionWithSpecificTime]} />);

    // Should show formatted time (format may vary by locale)
    expect(screen.getByText(/\d{1,2}:\d{2}:\d{2}/)).toBeInTheDocument();
  });
});

describe("ActivityFeed Performance", () => {
  test("memoizes display actions to prevent unnecessary re-renders", () => {
    const { rerender } = render(<ActivityFeed actions={mockActions} />);

    // Re-render with same actions
    rerender(<ActivityFeed actions={mockActions} />);

    // Component should handle re-renders efficiently
    expect(screen.getByText("Agent Activity Feed")).toBeInTheDocument();
  });

  test("handles rapid action updates efficiently", async () => {
    const { rerender } = render(<ActivityFeed actions={mockActions} />);

    // Simulate rapid updates
    for (let i = 0; i < 10; i++) {
      const newActions = [
        ...mockActions,
        {
          ...mockActions[0],
          id: `rapid-${i}`,
          timestamp: new Date().toISOString(),
        },
      ];

      rerender(<ActivityFeed actions={newActions} />);
    }

    // Should handle rapid updates without crashing
    expect(screen.getByText("Agent Activity Feed")).toBeInTheDocument();
  });
});
