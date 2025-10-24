/**
 * AutoScrollManager - Manages automatic scrolling behavior for activity feeds
 *
 * Features:
 * - Automatic scroll to bottom on new content
 * - Pause auto-scroll when user manually scrolls up
 * - Resume auto-scroll when user returns to bottom
 * - Performance optimizations for high-frequency updates
 * - Visual indicators for scroll state
 */

export interface AutoScrollConfig {
  threshold: number; // Distance from bottom to pause auto-scroll (pixels)
  resumeDelay: number; // Delay before resuming after user scroll (ms)
  smoothScroll: boolean; // Enable smooth scrolling
  maxScrollSpeed: number; // Maximum scroll speed for performance (px/ms)
  debounceDelay: number; // Debounce delay for scroll events (ms)
}

export interface ScrollState {
  isAutoScrollEnabled: boolean;
  isUserScrolling: boolean;
  isNearBottom: boolean;
  lastScrollPosition: number;
  messageCount: number;
  isPaused: boolean;
  lastUserInteraction: number;
}

export interface ScrollMetrics {
  scrollTop: number;
  scrollHeight: number;
  clientHeight: number;
  distanceFromBottom: number;
}

export class AutoScrollManager {
  private config: AutoScrollConfig;
  private state: ScrollState;
  private scrollContainer: HTMLElement | null = null;
  private resumeTimer: NodeJS.Timeout | null = null;
  private scrollDebounceTimer: NodeJS.Timeout | null = null;
  private animationFrameId: number | null = null;
  private observers: Set<(state: ScrollState) => void> = new Set();
  private isDestroyed = false;

  // Default configuration
  private static readonly DEFAULT_CONFIG: AutoScrollConfig = {
    threshold: 100, // 100px from bottom
    resumeDelay: 1500, // 1.5 seconds
    smoothScroll: true,
    maxScrollSpeed: 2, // 2px per ms
    debounceDelay: 100, // 100ms debounce
  };

  constructor(config: Partial<AutoScrollConfig> = {}) {
    this.config = { ...AutoScrollManager.DEFAULT_CONFIG, ...config };
    this.state = {
      isAutoScrollEnabled: true,
      isUserScrolling: false,
      isNearBottom: true,
      lastScrollPosition: 0,
      messageCount: 0,
      isPaused: false,
      lastUserInteraction: 0,
    };
  }

  /**
   * Attach the manager to a scroll container
   */
  public attachToContainer(container: HTMLElement): void {
    if (this.isDestroyed) {
      throw new Error("AutoScrollManager has been destroyed");
    }

    this.detachFromContainer();
    this.scrollContainer = container;

    // Add event listeners
    container.addEventListener("scroll", this.handleScroll, { passive: true });
    container.addEventListener("wheel", this.handleUserInteraction, {
      passive: true,
    });
    container.addEventListener("touchstart", this.handleUserInteraction, {
      passive: true,
    });
    container.addEventListener("touchmove", this.handleUserInteraction, {
      passive: true,
    });
    container.addEventListener("keydown", this.handleKeyboardInteraction);

    // Initialize state
    this.updateScrollMetrics();
    this.notifyObservers();
  }

  /**
   * Detach from the current container
   */
  public detachFromContainer(): void {
    if (this.scrollContainer) {
      this.scrollContainer.removeEventListener("scroll", this.handleScroll);
      this.scrollContainer.removeEventListener(
        "wheel",
        this.handleUserInteraction
      );
      this.scrollContainer.removeEventListener(
        "touchstart",
        this.handleUserInteraction
      );
      this.scrollContainer.removeEventListener(
        "touchmove",
        this.handleUserInteraction
      );
      this.scrollContainer.removeEventListener(
        "keydown",
        this.handleKeyboardInteraction
      );
      this.scrollContainer = null;
    }

    this.clearTimers();
  }

  /**
   * Scroll to bottom of container
   */
  public scrollToBottom(smooth: boolean = this.config.smoothScroll): void {
    if (!this.scrollContainer || this.isDestroyed) return;

    const scrollHeight = this.scrollContainer.scrollHeight;
    const targetPosition = scrollHeight - this.scrollContainer.clientHeight;

    if (smooth && this.config.smoothScroll) {
      this.smoothScrollTo(targetPosition);
    } else {
      this.scrollContainer.scrollTop = targetPosition;
    }

    // Update state
    this.state.isNearBottom = true;
    this.notifyObservers();
  }

  /**
   * Pause auto-scrolling
   */
  public pauseAutoScroll(): void {
    this.state.isPaused = true;
    this.state.isAutoScrollEnabled = false;
    this.clearResumeTimer();
    this.notifyObservers();
  }

  /**
   * Resume auto-scrolling
   */
  public resumeAutoScroll(): void {
    this.state.isPaused = false;
    this.state.isAutoScrollEnabled = true;
    this.clearResumeTimer();
    this.notifyObservers();
  }

  /**
   * Handle new message arrival
   */
  public handleNewMessage(): void {
    if (this.isDestroyed) return;

    this.state.messageCount++;

    // Auto-scroll if enabled and near bottom
    if (
      this.state.isAutoScrollEnabled &&
      this.state.isNearBottom &&
      !this.state.isUserScrolling
    ) {
      // Use requestAnimationFrame for smooth performance
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
      }

      this.animationFrameId = requestAnimationFrame(() => {
        this.scrollToBottom();
        this.animationFrameId = null;
      });
    }

    this.notifyObservers();
  }

  /**
   * Get current scroll state
   */
  public getState(): ScrollState {
    return { ...this.state };
  }

  /**
   * Check if container is near bottom
   */
  public isNearBottom(): boolean {
    if (!this.scrollContainer) return false;

    const metrics = this.getScrollMetrics();
    return metrics.distanceFromBottom <= this.config.threshold;
  }

  /**
   * Check if auto-scroll should be active
   */
  public shouldAutoScroll(): boolean {
    return (
      this.state.isAutoScrollEnabled &&
      this.state.isNearBottom &&
      !this.state.isUserScrolling &&
      !this.state.isPaused
    );
  }

  /**
   * Add state change observer
   */
  public addObserver(callback: (state: ScrollState) => void): () => void {
    this.observers.add(callback);
    return () => this.observers.delete(callback);
  }

  /**
   * Update configuration
   */
  public updateConfig(newConfig: Partial<AutoScrollConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Destroy the manager and clean up resources
   */
  public destroy(): void {
    this.isDestroyed = true;
    this.detachFromContainer();
    this.observers.clear();
  }

  // Private methods

  private handleScroll = (): void => {
    if (this.isDestroyed || !this.scrollContainer) return;

    // Debounce scroll events for performance
    if (this.scrollDebounceTimer) {
      clearTimeout(this.scrollDebounceTimer);
    }

    this.scrollDebounceTimer = setTimeout(() => {
      this.updateScrollMetrics();
      this.checkScrollDirection();
      this.notifyObservers();
    }, this.config.debounceDelay);
  };

  private handleUserInteraction = (): void => {
    if (this.isDestroyed) return;

    this.state.lastUserInteraction = Date.now();
    this.state.isUserScrolling = true;

    // Always pause auto-scroll on user interaction
    this.pauseAutoScroll();

    // Clear existing timer and set new one
    this.clearResumeTimer();
    this.resumeTimer = setTimeout(() => {
      this.state.isUserScrolling = false;

      // Resume auto-scroll if user is back at bottom
      if (this.isNearBottom() && this.state.isPaused) {
        this.resumeAutoScroll();
      }

      this.notifyObservers();
    }, this.config.resumeDelay);
  };

  private handleKeyboardInteraction = (event: KeyboardEvent): void => {
    // Handle keyboard navigation (arrow keys, page up/down, home/end)
    const scrollKeys = [
      "ArrowUp",
      "ArrowDown",
      "PageUp",
      "PageDown",
      "Home",
      "End",
    ];

    if (scrollKeys.includes(event.key)) {
      this.handleUserInteraction();
    }
  };

  private updateScrollMetrics(): void {
    if (!this.scrollContainer) return;

    const metrics = this.getScrollMetrics();
    const wasNearBottom = this.state.isNearBottom;

    this.state.lastScrollPosition = metrics.scrollTop;
    this.state.isNearBottom =
      metrics.distanceFromBottom <= this.config.threshold;

    // If user scrolled back to bottom, enable auto-scroll
    if (!wasNearBottom && this.state.isNearBottom && this.state.isPaused) {
      this.resumeAutoScroll();
    }
  }

  private checkScrollDirection(): void {
    if (!this.scrollContainer) return;

    const currentPosition = this.scrollContainer.scrollTop;
    const previousPosition = this.state.lastScrollPosition;

    // Detect if user is scrolling up (away from bottom)
    if (currentPosition < previousPosition && this.state.isAutoScrollEnabled) {
      this.handleUserInteraction();
    }
  }

  private getScrollMetrics(): ScrollMetrics {
    if (!this.scrollContainer) {
      return {
        scrollTop: 0,
        scrollHeight: 0,
        clientHeight: 0,
        distanceFromBottom: 0,
      };
    }

    const { scrollTop, scrollHeight, clientHeight } = this.scrollContainer;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    return {
      scrollTop,
      scrollHeight,
      clientHeight,
      distanceFromBottom,
    };
  }

  private smoothScrollTo(targetPosition: number): void {
    if (!this.scrollContainer || this.isDestroyed) return;

    const startPosition = this.scrollContainer.scrollTop;
    const distance = targetPosition - startPosition;
    const duration = Math.min(
      Math.abs(distance) / this.config.maxScrollSpeed,
      500
    ); // Max 500ms
    const startTime = performance.now();

    const animateScroll = (currentTime: number) => {
      if (this.isDestroyed || !this.scrollContainer) return;

      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-out)
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentPosition = startPosition + distance * easeOut;

      this.scrollContainer.scrollTop = currentPosition;

      if (progress < 1) {
        this.animationFrameId = requestAnimationFrame(animateScroll);
      } else {
        this.animationFrameId = null;
      }
    };

    this.animationFrameId = requestAnimationFrame(animateScroll);
  }

  private clearTimers(): void {
    if (this.resumeTimer) {
      clearTimeout(this.resumeTimer);
      this.resumeTimer = null;
    }

    if (this.scrollDebounceTimer) {
      clearTimeout(this.scrollDebounceTimer);
      this.scrollDebounceTimer = null;
    }

    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  private clearResumeTimer(): void {
    if (this.resumeTimer) {
      clearTimeout(this.resumeTimer);
      this.resumeTimer = null;
    }
  }

  private notifyObservers(): void {
    this.observers.forEach((callback) => {
      try {
        callback(this.getState());
      } catch (error) {
        console.error("Error in AutoScrollManager observer:", error);
      }
    });
  }
}
