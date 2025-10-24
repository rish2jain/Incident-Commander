/**
 * useAudioNotifications Hook
 * React hook for managing audio notifications
 * Requirements: 3.5 - Add configurable audio notifications for major incident lifecycle events
 */

import { useState, useEffect, useCallback } from "react";
import {
  AudioNotificationManager,
  AudioNotificationConfig,
  NotificationEvent,
  audioNotificationManager,
} from "../audio-notification-manager";

export interface UseAudioNotificationsReturn {
  config: AudioNotificationConfig;
  isSupported: boolean;
  isInitialized: boolean;
  updateConfig: (newConfig: Partial<AudioNotificationConfig>) => void;
  setEventEnabled: (event: NotificationEvent, enabled: boolean) => void;
  playNotification: (event: NotificationEvent) => Promise<void>;
  testNotification: (event: NotificationEvent) => Promise<void>;
  initialize: () => Promise<void>;
  getSoundPacks: () => Array<{ id: string; name: string; description: string }>;
  getAvailableEvents: () => Array<{
    event: NotificationEvent;
    description: string;
    category: string;
  }>;
}

export function useAudioNotifications(
  manager: AudioNotificationManager = audioNotificationManager
): UseAudioNotificationsReturn {
  const [config, setConfig] = useState<AudioNotificationConfig>(
    manager.getConfig()
  );
  const [isInitialized, setIsInitialized] = useState(false);

  // Subscribe to configuration changes
  useEffect(() => {
    const unsubscribe = manager.onConfigChange(
      (newConfig: AudioNotificationConfig) => {
        setConfig(newConfig);
      }
    );

    return unsubscribe;
  }, [manager]);

  const updateConfig = useCallback(
    (newConfig: Partial<AudioNotificationConfig>) => {
      manager.updateConfig(newConfig);
    },
    [manager]
  );

  const setEventEnabled = useCallback(
    (event: NotificationEvent, enabled: boolean) => {
      manager.setEventEnabled(event, enabled);
    },
    [manager]
  );

  const playNotification = useCallback(
    async (event: NotificationEvent) => {
      await manager.playNotification(event);
    },
    [manager]
  );

  const testNotification = useCallback(
    async (event: NotificationEvent) => {
      await manager.testNotification(event);
    },
    [manager]
  );

  const initialize = useCallback(async () => {
    await manager.initialize();
    setIsInitialized(true);
  }, [manager]);

  const getSoundPacks = useCallback(() => {
    return manager.getSoundPacks();
  }, [manager]);

  const getAvailableEvents = useCallback(() => {
    return manager.getAvailableEvents();
  }, [manager]);

  return {
    config,
    isSupported: manager.isSupported(),
    isInitialized,
    updateConfig,
    setEventEnabled,
    playNotification,
    testNotification,
    initialize,
    getSoundPacks,
    getAvailableEvents,
  };
}
