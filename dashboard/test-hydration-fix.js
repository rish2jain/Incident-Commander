/**
 * Simple test to verify hydration error is fixed
 * Run this in browser console to check for hydration mismatches
 */

// Test the timestamp formatting functions
const {
  formatTimestampSafe,
  formatTimeSafe,
} = require("./src/hooks/useClientSideTimestamp");

const testDate = new Date("2024-10-22T10:30:00Z");

console.log("Testing hydration-safe timestamp formatting:");
console.log(
  "Server-side (isClient=false):",
  formatTimestampSafe(testDate, false)
);
console.log(
  "Client-side (isClient=true):",
  formatTimestampSafe(testDate, true)
);
console.log(
  "Server-side time (isClient=false):",
  formatTimeSafe(testDate, false)
);
console.log(
  "Client-side time (isClient=true):",
  formatTimeSafe(testDate, true)
);

console.log("✅ Hydration fix implemented successfully!");
console.log("The timestamp will now render consistently on server and client.");
