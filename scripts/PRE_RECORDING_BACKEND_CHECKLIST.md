# 🔧 Pre-Recording Backend Verification Checklist

**Purpose:** Ensure backend is stable and error-free before demo recording
**Time Required:** 15 minutes
**Critical for:** Preventing WebSocket errors in recording

---

## ✅ STEP 1: Backend Health Check (2 minutes)

### Start the Backend

```bash
# Navigate to project root
cd "/Users/rish2jain/Documents/Incident Commander"

# Start the backend
python3 dashboard_backend.py
```

**Expected Output:**
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Checklist:**
- [ ] Backend starts without errors
- [ ] No Python exceptions in startup logs
- [ ] Port 8000 is available (not in use by another process)
- [ ] Logs show "Application startup complete"

**If Backend Fails to Start:**
```bash
# Check if port 8000 is already in use
lsof -i :8000

# If process found, kill it
kill -9 <PID>

# Try starting backend again
python3 dashboard_backend.py
```

---

### Verify Health Endpoint

```bash
# In a NEW terminal window (keep backend running)
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"healthy","timestamp":"2025-10-21T22:00:00.000000"}
```

**Checklist:**
- [ ] Health endpoint returns 200 OK
- [ ] Response contains "healthy" status
- [ ] Timestamp is current

**If Health Check Fails:**
- Backend not running → Start it
- Port incorrect → Check backend logs for actual port
- Connection refused → Check firewall settings

---

## ✅ STEP 2: Dashboard Connection Test (3 minutes)

### Start the Dashboard

```bash
# Open a NEW terminal window
cd "/Users/rish2jain/Documents/Incident Commander/dashboard"

# Start Next.js development server
npm run dev
```

**Expected Output:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
```

**Checklist:**
- [ ] Dashboard starts on port 3000
- [ ] No compilation errors
- [ ] Logs show "compiled successfully"

---

### Open Dashboard in Browser

```bash
# Open in Chrome (recommended)
open -a "Google Chrome" http://localhost:3000/ops
```

**Checklist:**
- [ ] Dashboard loads within 5 seconds
- [ ] Operations dashboard displays correctly
- [ ] No blank white screen
- [ ] Metrics are visible

---

### Verify WebSocket Connection

**In Browser:**
1. Open Developer Console (F12 or Cmd+Option+I)
2. Go to Console tab
3. Look for connection messages

**Expected Console Output:**
```
WebSocket connection established
Connected to backend successfully
```

**Checklist:**
- [ ] Console shows "WebSocket connection established"
- [ ] Connection status indicator shows green dot
- [ ] Header shows "Connected" badge
- [ ] NO "WebSocket connection lost" errors
- [ ] NO red error messages in console

**If WebSocket Fails:**

Check console for specific error:

**Error: "WebSocket connection to 'ws://localhost:8000/ws' failed"**
- **Cause:** Backend not running
- **Fix:** Start backend with `python3 dashboard_backend.py`

**Error: "Connection refused"**
- **Cause:** Backend crashed or wrong port
- **Fix:** Check backend terminal for errors, restart if needed

**Error: "Connection timeout"**
- **Cause:** Network/firewall issue
- **Fix:** Disable firewall temporarily, check localhost connectivity

---

## ✅ STEP 3: Connection Stability Test (5 minutes)

### Let Dashboard Run

**Action:**
- Leave dashboard open for 5 minutes
- Keep browser console visible
- Monitor for connection drops

**Checklist:**
- [ ] Connection stays green for full 5 minutes
- [ ] No "reconnecting..." messages appear
- [ ] No WebSocket errors in console
- [ ] Backend logs show stable connection

**Watch Backend Terminal:**

**Good (Stable Connection):**
```
INFO:     WebSocket connection accepted
INFO:     Client connected: ws://localhost:8000/ws
```

**Bad (Connection Issues):**
```
WARNING:  WebSocket disconnect
ERROR:    Connection dropped
INFO:     Attempting reconnect...
```

**If Connection Drops:**
1. Check backend terminal for error messages
2. Look for Python exceptions or stack traces
3. Common causes:
   - Backend timeout too aggressive
   - Memory issues
   - Network instability
4. **Fix:** Restart backend and dashboard, verify stability before recording

---

### Test Incident Trigger

**Action:**
1. Navigate to `/transparency` page
2. Click "Database Cascade Failure" button
3. Watch for agent activity

**Expected Behavior:**
- System status changes to "Processing"
- Agent cards start updating
- Activity appears in transparency tabs
- Backend logs show incident processing

**Checklist:**
- [ ] Incident triggers successfully
- [ ] Agents activate (see backend logs)
- [ ] Transparency tabs populate with content
- [ ] NO errors in console
- [ ] NO errors in backend logs
- [ ] Incident completes (status shows "Resolved")

**Backend Logs Should Show:**
```
INFO: Starting incident processing: Database Cascade Failure
INFO: Detection phase started
INFO: Detection phase completed - confidence: 0.93
INFO: Diagnosis phase started
INFO: Diagnosis phase completed - confidence: 0.97
INFO: Prediction phase started
...
INFO: Incident resolved successfully
```

**If Incident Fails:**
- Check backend logs for Python exceptions
- Verify WebSocket is still connected
- Try restarting both backend and dashboard
- Test with different scenario (API Rate Limit Breach)

---

## ✅ STEP 4: Reset to Clean State (2 minutes)

### Prepare for Recording

**Action:**
1. Close all browser tabs
2. Stop dashboard (Ctrl+C in terminal)
3. Keep backend running (DO NOT STOP)
4. Wait 10 seconds

**Checklist:**
- [ ] All previous incidents cleared
- [ ] Backend still running without errors
- [ ] No orphaned WebSocket connections
- [ ] Memory usage normal (<100MB)

---

### Reopen Dashboard

**Action:**
1. Open new Chrome incognito window (Cmd+Shift+N)
2. Navigate to `http://localhost:3000/ops`
3. Wait 10 seconds for connection to establish

**Checklist:**
- [ ] Dashboard loads fresh
- [ ] WebSocket connects immediately (within 2-3 seconds)
- [ ] Console shows "WebSocket connection established"
- [ ] No errors visible
- [ ] Metrics show default state (1 active incident, 85% prevention)

---

## ✅ STEP 5: Final Pre-Recording Check (3 minutes)

### Console Cleanup

**In Browser Console:**
```javascript
// Clear console
console.clear()

// Verify connection
console.log("WebSocket connected:", document.querySelector('[data-connection-status]')?.textContent)
```

**Checklist:**
- [ ] Console is clear (no old messages)
- [ ] Connection status shows "Connected"
- [ ] No error messages visible
- [ ] No warnings visible

---

### Visual Inspection

**On Dashboard:**
- [ ] All metrics display correctly
- [ ] Prevention rate shows **85%** (not 92%)
- [ ] MTTR shows 1.3min
- [ ] System uptime shows 99.97%
- [ ] All 5 agent cards visible
- [ ] Agent confidence levels showing 93-95%
- [ ] No layout issues or broken UI
- [ ] "Connected" badge visible in header

---

### Backend Log Review

**In Backend Terminal:**
- [ ] No error messages in last 5 minutes
- [ ] No warning messages in last 5 minutes
- [ ] Connection stable message visible
- [ ] No memory warnings
- [ ] No timeout errors

**If Any Issues:**
❌ **STOP** - Do not proceed with recording
✅ **FIX** - Restart backend, dashboard, verify stability
✅ **RE-TEST** - Run through checklist again

---

## 🎯 RECORDING READY CRITERIA

✅ **You are ready to record when:**

1. **Backend Health:**
   - ✅ Running without errors
   - ✅ Health endpoint returns 200 OK
   - ✅ Logs show stable operation
   - ✅ No exceptions or warnings

2. **Dashboard Connection:**
   - ✅ Loads in <5 seconds
   - ✅ WebSocket connected (green indicator)
   - ✅ No console errors
   - ✅ Stable for 5+ minutes

3. **Functionality:**
   - ✅ Incident triggers work
   - ✅ Agents activate correctly
   - ✅ Transparency tabs populate
   - ✅ Resolution completes successfully

4. **Visual Quality:**
   - ✅ All metrics correct (85% prevention)
   - ✅ UI renders properly
   - ✅ No layout issues
   - ✅ Professional appearance

5. **Stability:**
   - ✅ 5-minute soak test passed
   - ✅ No reconnection attempts
   - ✅ No errors in 5+ minutes
   - ✅ Backend logs clean

**If ALL criteria met:** ✅ **PROCEED TO RECORDING**
**If ANY criteria fail:** ❌ **TROUBLESHOOT BEFORE RECORDING**

---

## 🚨 COMMON ISSUES & QUICK FIXES

### Issue: "Cannot connect to backend"
**Symptoms:** Red disconnected indicator, no WebSocket in console
**Fix:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it
python3 dashboard_backend.py

# Reload dashboard
```

---

### Issue: "WebSocket connection lost" appears during use
**Symptoms:** Intermittent reconnection messages
**Fix:**
1. Check backend terminal for errors
2. Restart backend: Ctrl+C, then `python3 dashboard_backend.py`
3. Reload dashboard in browser
4. Re-run 5-minute stability test

---

### Issue: Incident doesn't trigger
**Symptoms:** Button click doesn't activate agents
**Fix:**
1. Check backend logs - should show "Starting incident processing"
2. If no logs, WebSocket disconnected - check connection
3. Try different scenario button
4. Restart both backend and dashboard if persists

---

### Issue: Transparency tabs remain empty
**Symptoms:** Tabs show "Trigger incident to see..." even after triggering
**Fix:**
1. Wait 3-5 seconds after triggering (agents need time to process)
2. Check backend logs for agent execution
3. Refresh page and try again
4. If persists, backend may not be broadcasting updates - restart

---

### Issue: Metrics show wrong values
**Symptoms:** Prevention rate shows 92% instead of 85%
**Fix:**
This was already fixed in RefinedDashboard.tsx
If still appears:
1. Clear browser cache (Cmd+Shift+R)
2. Use incognito mode
3. Check if using old dashboard component

---

## 📝 RECORDING DAY CHECKLIST

**Morning of Recording:**
- [ ] Restart computer (fresh start, no background processes)
- [ ] Close all unnecessary applications
- [ ] Disable notifications (Do Not Disturb mode)
- [ ] Check internet connection stability
- [ ] Verify disk space available (>2GB for recording)

**30 Minutes Before Recording:**
- [ ] Start backend
- [ ] Verify health endpoint
- [ ] Start dashboard
- [ ] Verify WebSocket connection
- [ ] Run 5-minute stability test
- [ ] Clear browser console

**Immediately Before Recording:**
- [ ] Backend running ✓
- [ ] Dashboard connected ✓
- [ ] No errors visible ✓
- [ ] Metrics correct (85%) ✓
- [ ] Clean console ✓
- [ ] Recording software ready ✓

---

## 🎬 YOU'RE READY!

Once all checklists are complete, proceed to:
1. [RECORDING_CHECKLIST.md](RECORDING_CHECKLIST.md) for recording process
2. [DEMO_NARRATION_SCRIPT.md](DEMO_NARRATION_SCRIPT.md) for narration

**Remember:**
- Keep backend terminal visible (optional for credibility)
- Don't close dashboard during recording
- If ANY error appears, stop and troubleshoot
- Quality over speed - take time to get it perfect

**Good luck! 🚀**
