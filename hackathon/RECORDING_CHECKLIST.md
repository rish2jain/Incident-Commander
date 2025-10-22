# 🎬 Demo Re-Recording Checklist

**Use this checklist during recording to ensure you capture everything correctly**

---

## ✅ PRE-RECORDING SETUP (15 minutes)

### Backend Verification
- [ ] Start backend: `python dashboard_backend.py` (or appropriate command)
- [ ] Verify health: `curl http://localhost:8000/health` → should return 200 OK
- [ ] Open backend logs in terminal (keep visible during recording)
- [ ] Verify no errors in startup logs

### Dashboard Verification
- [ ] Open browser (Chrome recommended, incognito mode for clean state)
- [ ] Navigate to `http://localhost:3000/ops`
- [ ] Open browser console (F12)
- [ ] **CRITICAL:** Look for "WebSocket connection established" message
- [ ] Wait 10 seconds, verify no "WebSocket connection lost" errors
- [ ] Keep console open but minimized during recording

### Connection Stability Test
- [ ] Let dashboard run for 5 minutes
- [ ] Watch console for any connection errors
- [ ] Trigger one test incident to verify functionality
- [ ] Reset to clean state
- [ ] **If ANY errors:** Fix before proceeding

### Metric Verification
- [ ] Verify Prevention Rate shows **85%** (not 92%)
- [ ] Verify MTTR shows 1.3min
- [ ] Verify System Uptime shows 99.97%
- [ ] All metrics match documentation

### Recording Software Setup
- [ ] Screen recording software ready (OBS, QuickTime, etc.)
- [ ] Set resolution: 1920x1080
- [ ] Set frame rate: 30fps minimum
- [ ] Audio input: Microphone for narration OR silent (add narration later)
- [ ] Test 10-second recording → verify quality

---

## 🎬 RECORDING SEQUENCE (128 seconds)

### Phase 1: Introduction (0:00-0:20) — 20 seconds

**Actions:**
- [ ] Start on Operations Dashboard (`/ops`)
- [ ] Pan slowly across business metrics section
- [ ] Hover briefly over "1.3min MTTR" metric
- [ ] Hover over "85% Incidents prevented" metric
- [ ] Show all 5 agent confidence cards

**Narration (if recording live):**
> "The Autonomous Incident Commander uses 5 specialized AI agents working through Byzantine consensus to resolve production incidents in under 3 minutes—95% faster than traditional approaches, saving $2.8 million annually."

**Checklist:**
- [ ] All metrics visible and clear
- [ ] Agent cards showing high confidence (93-95%)
- [ ] WebSocket status: "Connected" (green dot)
- [ ] No errors in browser console

---

### Phase 2: Incident Trigger (0:20-0:35) — 15 seconds

**Actions:**
- [ ] Navigate to Transparency Dashboard (`/transparency`)
- [ ] Show the 4 scenario buttons clearly
- [ ] **CRITICAL:** Click "Database Cascade Failure" button
- [ ] Show "Trigger Demo" button being clicked
- [ ] Wait for system to respond

**Narration:**
> "Watch as we trigger a database connection pool exhaustion incident—the kind that would normally cascade across microservices, affecting 25,000 users and costing $168,000 in downtime."

**Checklist:**
- [ ] Button click is visible in recording
- [ ] System status changes from "System Ready" to active
- [ ] Agent cards start updating
- [ ] Loading indicators appear (if applicable)

---

### Phase 3: AI Transparency (0:35-1:20) — 45 seconds

**Actions:**
- [ ] **Tab 1 - Reasoning (10s):** Show Detection Agent reasoning
- [ ] Scroll slightly to show all 5 agent reasoning sections
- [ ] **Tab 2 - Confidence (10s):** Click Confidence tab
- [ ] Show confidence scores and uncertainty quantification
- [ ] **Tab 3 - Communication (8s):** Click Communication tab
- [ ] Show agent coordination messages
- [ ] **Tab 4 - Analytics (7s):** Click Analytics tab
- [ ] Show business impact calculation
- [ ] **Tab 5 - Decisions (optional, 5s):** Show decision tree if time permits

**Narration:**
> "Complete AI transparency across five dimensions. The Detection Agent analyzes 143 telemetry signals with 93% confidence. The Diagnosis Agent correlates 15,000 log entries to identify the root cause. The Prediction Agent forecasts a 73% probability of cascade failure. The Resolution Agent plans autonomous remediation. And the Communication Agent coordinates stakeholder updates—all reasoning fully explainable."

**Checklist:**
- [ ] **CRITICAL:** ALL tabs show actual content (NOT "Trigger incident to see...")
- [ ] Reasoning text is readable
- [ ] Confidence scores are visible
- [ ] Agent names and icons are clear
- [ ] Spend minimum 8-10 seconds per major tab

---

### Phase 4: Byzantine Consensus & Resolution (1:20-1:45) — 25 seconds

**Actions:**
- [ ] Navigate back to Operations Dashboard (`/ops`)
- [ ] Show activity feed with live agent messages
- [ ] Scroll activity feed to show multiple agent actions
- [ ] Point to agent confidence cards (should be updating)
- [ ] Highlight Business Impact metric (should be incrementing)

**Narration:**
> "Byzantine consensus ensures fault-tolerant decision making. All five agents must agree before autonomous action. Here, they've reached 94% consensus on the diagnosis and resolution plan. Watch autonomous remediation in action: scaling the connection pool, updating timeout configuration, enabling circuit breakers, restarting affected services, and verifying system health—all without human intervention."

**Checklist:**
- [ ] Activity feed shows 5+ agent messages
- [ ] Messages include timestamps and agent names
- [ ] Agent confidence cards show 90%+ scores
- [ ] Business Impact counter shows value > $100,000
- [ ] Green checkmarks appear on completed agents

---

### Phase 5: Resolution Complete (1:45-1:55) — 10 seconds

**Actions:**
- [ ] Show final resolved state
- [ ] Highlight "Incidents Resolved" counter (should be +1)
- [ ] Show all 5 agents with green checkmarks
- [ ] Display final Business Impact value

**Narration:**
> "Incident resolved in 1 minute 28 seconds. 25,000 users protected. $163,200 in downtime costs avoided."

**Checklist:**
- [ ] All agents show "Completed" status
- [ ] System status shows "Healthy" or "Resolved"
- [ ] MTTR metric reflects new incident (e.g., 1.4min)
- [ ] No errors or warnings visible

---

### Phase 6: Business Value (1:55-2:08) — 13 seconds

**Actions:**
- [ ] Scroll to Performance Metrics section
- [ ] Highlight each key metric:
  - MTTR: 1.3min (95.2% improvement)
  - Prevention: 85% incidents prevented
  - Cost per incident: $47 vs $5,600
  - Annual savings: $2.8M
- [ ] Hold on final frame for 2-3 seconds

**Narration:**
> "This is the only complete integration of all 8 AWS AI services. Production-ready today. $2.8 million in annual value. 458% ROI. The future of incident response is autonomous."

**Checklist:**
- [ ] All 4 key metrics clearly visible
- [ ] Numbers are large and readable
- [ ] Color coding is appropriate (green for good metrics)
- [ ] Final frame is clean and professional

---

## 🎯 POST-RECORDING VERIFICATION (10 minutes)

### Immediate Playback Check
- [ ] Play recording from start to finish
- [ ] Verify all 6 phases are captured
- [ ] Check that incident trigger is visible
- [ ] Confirm all transparency tabs show content
- [ ] Look for any visible errors or glitches
- [ ] Verify duration is 120-150 seconds

### Technical Quality Check
- [ ] Video resolution is 1920x1080 (check file properties)
- [ ] Frame rate is 30fps minimum
- [ ] No pixelation or compression artifacts
- [ ] Text is readable at full screen
- [ ] Colors are accurate (not washed out)

### Content Completeness Check
- [ ] Incident trigger button click is visible
- [ ] Agent reasoning text is readable
- [ ] Confidence scores are shown
- [ ] Activity feed has multiple messages
- [ ] Business impact counter incremented
- [ ] Final metrics are correct (85% prevention, etc.)
- [ ] **ZERO** "WebSocket connection lost" errors
- [ ] **ZERO** other error messages visible

### Narration Check (if recorded)
- [ ] Audio is clear and professional
- [ ] Volume is consistent throughout
- [ ] Pacing matches visuals (not too fast/slow)
- [ ] All 6 phases have narration
- [ ] No awkward silences >3 seconds

---

## 🔄 IF RECORDING FAILS

### Common Issues and Fixes

**Issue:** "WebSocket connection lost" appears during recording
- **Fix:** Restart backend, wait 10 seconds, verify connection, try again
- **Prevention:** Do 5-minute stability test before recording

**Issue:** Transparency tabs show "Trigger incident to see..."
- **Fix:** Incident didn't trigger properly. Click button again, wait 2-3 seconds
- **Verification:** Look for agent messages in activity feed

**Issue:** Agent confidence cards don't update
- **Fix:** Backend not processing incident. Check backend logs, restart if needed
- **Test:** Trigger test incident before recording

**Issue:** Recording is too long (>150 seconds)
- **Fix:** Speed up tab navigation, reduce scrolling time
- **Target:** Each tab should be 8-10 seconds maximum

**Issue:** Recording is too short (<120 seconds)
- **Fix:** Hold final frame longer, add 2-second pauses between phases
- **Target:** Aim for 125-130 seconds

---

## ✅ FINAL SUBMISSION CHECKLIST

Before declaring recording complete:
- [ ] Duration: 120-150 seconds ✓
- [ ] Resolution: 1920x1080 ✓
- [ ] Frame rate: 30fps minimum ✓
- [ ] All 6 phases demonstrated ✓
- [ ] Incident trigger visible ✓
- [ ] Transparency tabs show content ✓
- [ ] Activity feed has messages ✓
- [ ] Metrics updated during demo ✓
- [ ] Zero errors visible ✓
- [ ] Narration present (or planned) ✓
- [ ] File size reasonable (<50MB) ✓
- [ ] Playback tested on different device ✓

---

## 📝 NOTES SECTION

Use this space to track issues during recording:

**Attempt 1:**
- Issue: ________________________________________________
- Fix: _________________________________________________
- Retry? Y/N

**Attempt 2:**
- Issue: ________________________________________________
- Fix: _________________________________________________
- Retry? Y/N

**Attempt 3:**
- Issue: ________________________________________________
- Fix: _________________________________________________
- Success? Y/N

**Final Recording Details:**
- File name: ___________________________________________
- Duration: ____________ seconds
- File size: ____________ MB
- Date/time recorded: __________________________________
- Ready for submission: Y/N

---

## 🎯 SUCCESS CRITERIA

✅ **Your recording is submission-ready when:**

1. You watch it and think "This proves our system works"
2. Incident lifecycle is clear from trigger to resolution
3. All transparency features are demonstrated with real data
4. No technical errors are visible anywhere
5. Metrics are consistent with documentation (85% prevention)
6. You could show this to a judge and they'd say "impressive"

**If ANY criteria fails, re-record. This is your ONE chance to make a first impression.**

---

**Time budget:**
- Setup: 15 minutes
- Recording attempts: 30-60 minutes (expect 2-3 takes)
- Verification: 10 minutes
- **Total: 1-1.5 hours for perfect recording**

**Remember:** The recording is forever. The setup is temporary. Take the time to get it right.
