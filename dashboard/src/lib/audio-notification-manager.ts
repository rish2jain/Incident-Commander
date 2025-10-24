/**
 * Audio Notification Manager
 * Manages configurable audio notifications for incident lifecycle events
 * Requirements: 3.5 - Add configurable audio notifications for major incident lifecycle events
 */

export type NotificationEvent =
  | "incident_detected"
  | "phase_transition"
  | "agent_completed"
  | "conflict_detected"
  | "conflict_resolved"
  | "incident_resolved"
  | "human_escalation"
  | "system_error";

export interface AudioNotificationConfig {
  enabled: boolean;
  volume: number; // 0-1
  enabledEvents: Set<NotificationEvent>;
  soundPack: "default" | "minimal" | "professional" | "retro";
}

export interface NotificationSound {
  event: NotificationEvent;
  url: string;
  duration: number; // milliseconds
  description: string;
}

export class AudioNotificationManager {
  private config: AudioNotificationConfig;
  private audioContext: AudioContext | null = null;
  private soundBuffers: Map<NotificationEvent, AudioBuffer> = new Map();
  private configCallbacks: Array<(config: AudioNotificationConfig) => void> =
    [];
  private isInitialized = false;

  // Default sound URLs (in a real app, these would be actual audio files)
  private readonly SOUND_PACKS = {
    default: {
      incident_detected: {
        url: "/sounds/alert-high.mp3",
        duration: 1500,
        description: "High priority alert",
      },
      phase_transition: {
        url: "/sounds/transition.mp3",
        duration: 800,
        description: "Soft transition chime",
      },
      agent_completed: {
        url: "/sounds/success.mp3",
        duration: 600,
        description: "Success notification",
      },
      conflict_detected: {
        url: "/sounds/warning.mp3",
        duration: 1200,
        description: "Warning tone",
      },
      conflict_resolved: {
        url: "/sounds/resolved.mp3",
        duration: 900,
        description: "Resolution chime",
      },
      incident_resolved: {
        url: "/sounds/celebration.mp3",
        duration: 2000,
        description: "Celebration sound",
      },
      human_escalation: {
        url: "/sounds/escalation.mp3",
        duration: 1000,
        description: "Escalation alert",
      },
      system_error: {
        url: "/sounds/error.mp3",
        duration: 800,
        description: "Error notification",
      },
    },
    minimal: {
      incident_detected: {
        url: "/sounds/minimal/beep-high.mp3",
        duration: 300,
        description: "High beep",
      },
      phase_transition: {
        url: "/sounds/minimal/click.mp3",
        duration: 100,
        description: "Soft click",
      },
      agent_completed: {
        url: "/sounds/minimal/ding.mp3",
        duration: 200,
        description: "Simple ding",
      },
      conflict_detected: {
        url: "/sounds/minimal/beep-low.mp3",
        duration: 400,
        description: "Low beep",
      },
      conflict_resolved: {
        url: "/sounds/minimal/chime.mp3",
        duration: 300,
        description: "Simple chime",
      },
      incident_resolved: {
        url: "/sounds/minimal/success.mp3",
        duration: 500,
        description: "Success tone",
      },
      human_escalation: {
        url: "/sounds/minimal/alert.mp3",
        duration: 300,
        description: "Alert beep",
      },
      system_error: {
        url: "/sounds/minimal/error.mp3",
        duration: 200,
        description: "Error beep",
      },
    },
    professional: {
      incident_detected: {
        url: "/sounds/professional/alert.wav",
        duration: 1000,
        description: "Professional alert",
      },
      phase_transition: {
        url: "/sounds/professional/transition.wav",
        duration: 600,
        description: "Smooth transition",
      },
      agent_completed: {
        url: "/sounds/professional/complete.wav",
        duration: 400,
        description: "Task complete",
      },
      conflict_detected: {
        url: "/sounds/professional/attention.wav",
        duration: 800,
        description: "Attention required",
      },
      conflict_resolved: {
        url: "/sounds/professional/resolved.wav",
        duration: 600,
        description: "Issue resolved",
      },
      incident_resolved: {
        url: "/sounds/professional/success.wav",
        duration: 1200,
        description: "Mission success",
      },
      human_escalation: {
        url: "/sounds/professional/escalate.wav",
        duration: 700,
        description: "Escalation notice",
      },
      system_error: {
        url: "/sounds/professional/error.wav",
        duration: 500,
        description: "System error",
      },
    },
    retro: {
      incident_detected: {
        url: "/sounds/retro/alarm.wav",
        duration: 2000,
        description: "Retro alarm",
      },
      phase_transition: {
        url: "/sounds/retro/blip.wav",
        duration: 300,
        description: "8-bit blip",
      },
      agent_completed: {
        url: "/sounds/retro/powerup.wav",
        duration: 800,
        description: "Power-up sound",
      },
      conflict_detected: {
        url: "/sounds/retro/warning.wav",
        duration: 1500,
        description: "Retro warning",
      },
      conflict_resolved: {
        url: "/sounds/retro/coin.wav",
        duration: 600,
        description: "Coin collect",
      },
      incident_resolved: {
        url: "/sounds/retro/victory.wav",
        duration: 3000,
        description: "Victory fanfare",
      },
      human_escalation: {
        url: "/sounds/retro/urgent.wav",
        duration: 1000,
        description: "Urgent beep",
      },
      system_error: {
        url: "/sounds/retro/error.wav",
        duration: 1200,
        description: "Error buzz",
      },
    },
  };

  constructor() {
    this.config = {
      enabled: false, // Disabled by default for better UX
      volume: 0.5,
      enabledEvents: new Set([
        "incident_detected" as NotificationEvent,
        "incident_resolved" as NotificationEvent,
        "conflict_detected" as NotificationEvent,
        "human_escalation" as NotificationEvent,
      ]),
      soundPack: "default",
    };

    // Load config from localStorage if available
    this.loadConfig();
  }

  /**
   * Initialize audio context (must be called after user interaction)
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Create audio context
      this.audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();

      // Resume context if suspended (required by some browsers)
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }

      this.isInitialized = true;
      console.log("Audio notification system initialized");
    } catch (error) {
      console.warn("Failed to initialize audio context:", error);
    }
  }

  /**
   * Play notification sound for an event
   */
  public async playNotification(event: NotificationEvent): Promise<void> {
    if (!this.config.enabled || !this.config.enabledEvents.has(event)) {
      return;
    }

    if (!this.isInitialized) {
      console.warn("Audio system not initialized. Call initialize() first.");
      return;
    }

    if (!this.audioContext) {
      console.warn("Audio context not available");
      return;
    }

    try {
      // Get or load sound buffer
      let buffer = this.soundBuffers.get(event);
      if (!buffer) {
        const loadedBuffer = await this.loadSound(event);
        if (!loadedBuffer) return;
        buffer = loadedBuffer;
      }

      // Create and play sound
      const source = this.audioContext.createBufferSource();
      const gainNode = this.audioContext.createGain();

      source.buffer = buffer;
      gainNode.gain.value = this.config.volume;

      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      source.start();
    } catch (error) {
      console.warn(`Failed to play notification for ${event}:`, error);
    }
  }

  /**
   * Load sound buffer for an event
   */
  private async loadSound(
    event: NotificationEvent
  ): Promise<AudioBuffer | null> {
    if (!this.audioContext) return null;

    try {
      const soundInfo = this.SOUND_PACKS[this.config.soundPack][event];

      // In a real implementation, this would fetch actual audio files
      // For now, we'll generate synthetic sounds
      const buffer = this.generateSyntheticSound(event);

      if (buffer) {
        this.soundBuffers.set(event, buffer);
      }

      return buffer;
    } catch (error) {
      console.warn(`Failed to load sound for ${event}:`, error);
      return null;
    }
  }

  /**
   * Generate synthetic sounds (fallback when audio files aren't available)
   */
  private generateSyntheticSound(event: NotificationEvent): AudioBuffer | null {
    if (!this.audioContext) return null;

    const sampleRate = this.audioContext.sampleRate;
    let duration: number;
    let frequency: number;
    let type: OscillatorType = "sine";

    // Define sound characteristics for each event
    switch (event) {
      case "incident_detected":
        duration = 0.8;
        frequency = 800;
        type = "square";
        break;
      case "phase_transition":
        duration = 0.3;
        frequency = 600;
        type = "sine";
        break;
      case "agent_completed":
        duration = 0.4;
        frequency = 1000;
        type = "triangle";
        break;
      case "conflict_detected":
        duration = 0.6;
        frequency = 400;
        type = "sawtooth";
        break;
      case "conflict_resolved":
        duration = 0.5;
        frequency = 700;
        type = "sine";
        break;
      case "incident_resolved":
        duration = 1.0;
        frequency = 1200;
        type = "triangle";
        break;
      case "human_escalation":
        duration = 0.7;
        frequency = 500;
        type = "square";
        break;
      case "system_error":
        duration = 0.4;
        frequency = 300;
        type = "sawtooth";
        break;
      default:
        duration = 0.3;
        frequency = 600;
        type = "sine";
    }

    const frameCount = sampleRate * duration;
    const buffer = this.audioContext.createBuffer(1, frameCount, sampleRate);
    const channelData = buffer.getChannelData(0);

    // Generate waveform
    for (let i = 0; i < frameCount; i++) {
      const t = i / sampleRate;
      let sample = 0;

      switch (type) {
        case "sine":
          sample = Math.sin(2 * Math.PI * frequency * t);
          break;
        case "square":
          sample = Math.sign(Math.sin(2 * Math.PI * frequency * t));
          break;
        case "triangle":
          sample =
            (2 / Math.PI) * Math.asin(Math.sin(2 * Math.PI * frequency * t));
          break;
        case "sawtooth":
          sample = 2 * (t * frequency - Math.floor(t * frequency + 0.5));
          break;
      }

      // Apply envelope (fade in/out)
      const envelope = Math.min(
        1,
        Math.min(t * 10, (duration - t) * 10) // 100ms fade in/out
      );

      channelData[i] = sample * envelope * 0.3; // Reduce volume
    }

    return buffer;
  }

  /**
   * Update configuration
   */
  public updateConfig(newConfig: Partial<AudioNotificationConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.saveConfig();
    this.notifyConfigCallbacks();
  }

  /**
   * Get current configuration
   */
  public getConfig(): AudioNotificationConfig {
    return {
      ...this.config,
      enabledEvents: new Set(this.config.enabledEvents), // Return copy
    };
  }

  /**
   * Enable/disable specific event
   */
  public setEventEnabled(event: NotificationEvent, enabled: boolean): void {
    if (enabled) {
      this.config.enabledEvents.add(event);
    } else {
      this.config.enabledEvents.delete(event);
    }
    this.saveConfig();
    this.notifyConfigCallbacks();
  }

  /**
   * Test play a notification
   */
  public async testNotification(event: NotificationEvent): Promise<void> {
    const wasEnabled = this.config.enabled;
    const wasEventEnabled = this.config.enabledEvents.has(event);

    // Temporarily enable for testing
    this.config.enabled = true;
    this.config.enabledEvents.add(event);

    await this.playNotification(event);

    // Restore original settings
    this.config.enabled = wasEnabled;
    if (!wasEventEnabled) {
      this.config.enabledEvents.delete(event);
    }
  }

  /**
   * Get available sound packs
   */
  public getSoundPacks(): Array<{
    id: string;
    name: string;
    description: string;
  }> {
    return [
      {
        id: "default",
        name: "Default",
        description: "Rich notification sounds",
      },
      {
        id: "minimal",
        name: "Minimal",
        description: "Simple, unobtrusive sounds",
      },
      {
        id: "professional",
        name: "Professional",
        description: "Corporate-friendly tones",
      },
      { id: "retro", name: "Retro", description: "8-bit style sounds" },
    ];
  }

  /**
   * Get available events with descriptions
   */
  public getAvailableEvents(): Array<{
    event: NotificationEvent;
    description: string;
    category: string;
  }> {
    return [
      {
        event: "incident_detected",
        description: "New incident detected",
        category: "Incidents",
      },
      {
        event: "incident_resolved",
        description: "Incident resolved successfully",
        category: "Incidents",
      },
      {
        event: "phase_transition",
        description: "Incident phase changed",
        category: "Progress",
      },
      {
        event: "agent_completed",
        description: "Agent task completed",
        category: "Agents",
      },
      {
        event: "conflict_detected",
        description: "Agent conflict detected",
        category: "Conflicts",
      },
      {
        event: "conflict_resolved",
        description: "Conflict resolved",
        category: "Conflicts",
      },
      {
        event: "human_escalation",
        description: "Escalated to human",
        category: "Escalation",
      },
      {
        event: "system_error",
        description: "System error occurred",
        category: "Errors",
      },
    ];
  }

  /**
   * Subscribe to configuration changes
   */
  public onConfigChange(
    callback: (config: AudioNotificationConfig) => void
  ): () => void {
    this.configCallbacks.push(callback);

    return () => {
      const index = this.configCallbacks.indexOf(callback);
      if (index > -1) {
        this.configCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Check if audio is supported
   */
  public isSupported(): boolean {
    return !!(window.AudioContext || (window as any).webkitAudioContext);
  }

  /**
   * Save configuration to localStorage
   */
  private saveConfig(): void {
    try {
      const configToSave = {
        ...this.config,
        enabledEvents: Array.from(this.config.enabledEvents),
      };
      localStorage.setItem(
        "audioNotificationConfig",
        JSON.stringify(configToSave)
      );
    } catch (error) {
      console.warn("Failed to save audio config:", error);
    }
  }

  /**
   * Load configuration from localStorage
   */
  private loadConfig(): void {
    try {
      const saved = localStorage.getItem("audioNotificationConfig");
      if (saved) {
        const parsed = JSON.parse(saved);
        this.config = {
          ...this.config,
          ...parsed,
          enabledEvents: new Set(
            parsed.enabledEvents || ([] as NotificationEvent[])
          ),
        };
      }
    } catch (error) {
      console.warn("Failed to load audio config:", error);
    }
  }

  /**
   * Notify configuration callbacks
   */
  private notifyConfigCallbacks(): void {
    this.configCallbacks.forEach((callback) => callback(this.getConfig()));
  }

  /**
   * Clear all cached sounds (useful when changing sound packs)
   */
  public clearSoundCache(): void {
    this.soundBuffers.clear();
  }
}

// Create singleton instance
export const audioNotificationManager = new AudioNotificationManager();
