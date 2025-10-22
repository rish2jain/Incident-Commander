/**
 * Live Value Counter
 *
 * Real-time counter showing accumulated business value and incident prevention.
 * Creates urgency and demonstrates continuous value generation.
 *
 * Displays:
 * - Cost savings accumulated this session
 * - Number of incidents prevented
 * - Real-time incremental updates
 */

"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Shield, DollarSign } from "lucide-react";
import { Card, CardContent } from "@/components/shared";

export function LiveValueCounter() {
  const [costSaved, setCostSaved] = useState(0);
  const [incidentsPrevented, setIncidentsPrevented] = useState(0);
  const [sessionStart] = useState(Date.now());

  useEffect(() => {
    // Increment cost saved every second
    // Calculation: $250K per incident / 86400 seconds per day
    // Assumes ~100 incidents prevented per month (3.3 per day)
    const interval = setInterval(() => {
      const elapsedSeconds = (Date.now() - sessionStart) / 1000;

      // Cost savings: $250K per incident, ~3.3 incidents per day
      // = $825K per day / 86400 seconds = ~$9.55 per second
      setCostSaved(elapsedSeconds * 9.55);

      // Incidents prevented: ~100 per month = ~3.3 per day
      // = 3.3 / 86400 = 0.0000382 per second
      setIncidentsPrevented(elapsedSeconds * 0.0000382);
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionStart]);

  return (
    <Card className="bg-gradient-to-r from-green-900/40 via-blue-900/40 to-purple-900/40 border-green-500/30">
      <CardContent className="py-6">
        <div className="text-center">
          {/* Header */}
          <div className="flex items-center justify-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <div className="text-sm font-semibold text-slate-300">
              Value Generated This Session
            </div>
          </div>

          {/* Main Counter */}
          <motion.div
            key={Math.floor(costSaved)}
            initial={{ scale: 1 }}
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 0.3 }}
            className="mb-4"
          >
            <div className="flex items-center justify-center gap-2">
              <DollarSign className="w-8 h-8 text-green-400" />
              <div className="text-5xl font-bold text-green-400 tabular-nums">
                {costSaved.toFixed(2)}
              </div>
            </div>
            <div className="text-xs text-slate-400 mt-2">
              Cost Savings Accumulated
            </div>
          </motion.div>

          {/* Secondary Metrics */}
          <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-slate-700">
            <div>
              <div className="flex items-center justify-center gap-1 mb-1">
                <Shield className="w-4 h-4 text-blue-400" />
                <div className="text-xs text-slate-400">Incidents Prevented</div>
              </div>
              <div className="text-2xl font-bold text-blue-400 tabular-nums">
                {incidentsPrevented.toFixed(4)}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400 mb-1">Session Time</div>
              <div className="text-2xl font-bold text-purple-400 tabular-nums">
                {Math.floor((Date.now() - sessionStart) / 1000)}s
              </div>
            </div>
          </div>

          {/* Footer Note */}
          <div className="mt-4 pt-4 border-t border-slate-700">
            <div className="text-xs text-slate-500">
              Based on $250K per incident × 100 incidents/month prevention rate
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
