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
    // Ensure timestamp is a valid Date object
    if (timestamp instanceof Date && !isNaN(timestamp.getTime())) {
      return timestamp.toISOString();
    }
    // Fallback for invalid dates
    return new Date().toISOString();
  }

  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  // Check if date is valid
  if (isNaN(date.getTime())) {
    return "Invalid Date";
  }
  return date.toLocaleTimeString();
};
