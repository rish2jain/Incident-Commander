import { useState, useEffect } from "react";

/**
 * Hook to prevent hydration mismatches with timestamps
 * Returns a flag indicating if we're on the client side
 */
export const useClientSideTimestamp = () => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return isClient;
};

/**
 * Safe timestamp formatter that prevents hydration mismatches
 */
export const formatTimestampSafe = (
  timestamp: string | Date,
  isClient: boolean
) => {
  if (!isClient) {
    // Return a consistent server-side representation
    return typeof timestamp === "string" ? timestamp : timestamp.toISOString();
  }

  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  return date.toLocaleString();
};

/**
 * Safe time formatter that prevents hydration mismatches
 */
export const formatTimeSafe = (timestamp: string | Date, isClient: boolean) => {
  if (!isClient) {
    // Return a consistent server-side representation
    if (typeof timestamp === "string") {
      return timestamp;
    }
    // Ensure timestamp is a Date object before calling toISOString
    if (
      timestamp &&
      typeof timestamp === "object" &&
      "toISOString" in timestamp
    ) {
      return timestamp.toISOString();
    }
    return new Date().toISOString(); // Fallback
  }

  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  if (!date || isNaN(date.getTime())) {
    return new Date().toLocaleTimeString(); // Fallback for invalid dates
  }
  return date.toLocaleTimeString();
};
