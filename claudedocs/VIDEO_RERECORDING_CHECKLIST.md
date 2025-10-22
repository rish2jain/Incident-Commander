# Video Re-Recording Checklist

**Purpose**: Fix video narrative structure and demonstrate all promised features
**Date**: October 22, 2025
**Target**: 3-minute judge-ready demo following 6-phase structure

---

## 🎬 PRE-RECORDING SETUP

### Environment Preparation
- [ ] Start backend server: `cd backend && python -m uvicorn main:app --reload`
- [ ] Start dashboard: `cd dashboard && npm run dev`
- [ ] Verify `/ops` route loads without errors
- [ ] Clear browser cache and localStorage
- [ ] Set browser window to 1920x1080 resolution
- [ ] Close all unnecessary tabs and applications
- [ ] Test WebSocket connection (should see live updates)

### Feature Verification
- [ ] Click each agent card to verify transparency modal opens
- [ ] Verify all 4 tabs visible: Reasoning, Confidence, Evidence, Guardrails
- [ ] Check RAG sources appear with similarity scores (94%, 89%, 86%)
- [ ] Verify Byzantine consensus visualization shows correct weights:
  - Detection: 20%
  - Diagnosis: 40% (highest)
  - Prediction: 30%
  - Resolution: 10%
  - Communication: 0% (non-voting)
- [ ] Verify consensus threshold shows 85%
- [ ] Test incident simulation triggers correctly
- [ ] Verify no red error boxes appear in UI

### Data Preparation
- [ ] Ensure sample incident data is loaded
- [ ] Verify $2.8M savings metric displays on main dashboard
- [ ] Check MTTR: 2.8 minutes vs 6.2 hour industry average
- [ ] Verify agent confidence values are visible
- [ ] Check trust indicators (Guardrails, PII, Circuit Breaker, Rollback, RAG) appear

---

## 📝 6-PHASE RECORDING SCRIPT

### Phase 1: Main Dashboard Overview (15 seconds) ⭐ NEW
**Timing**: 0:00 - 0:15

**Screen**: `/ops` dashboard main view

**Actions**:
1. Show clean dashboard with 5 agent cards
2. Point to "$2.8M Annual Savings" metric
3. Highlight "MTTR: 2.8 min (vs 6.2 hr industry avg)"

**Narration**:
> "This is Incident Commander - an AI-powered incident response system that saves $2.8 million annually by reducing mean time to resolution from 6.2 hours to just 2.8 minutes."

**Checklist**:
- [ ] $2.8M metric visible
- [ ] MTTR comparison visible
- [ ] All 5 agent cards displayed
- [ ] No errors in console

---

### Phase 2: Incident Trigger (10 seconds) ⭐ NEW
**Timing**: 0:15 - 0:25

**Screen**: Trigger incident simulation

**Actions**:
1. Click "Simulate Database Cascade" button
2. Show incident alert appears

**Narration**:
> "Watch what happens when a database cascade failure is detected."

**Checklist**:
- [ ] Incident simulation button visible
- [ ] Click triggers incident successfully
- [ ] Alert/notification appears
- [ ] Agent confidence values start updating

---

### Phase 3: Multi-Agent Coordination (20 seconds)
**Timing**: 0:25 - 0:45

**Screen**: Agent activity and coordination

**Actions**:
1. Show agent confidence values updating in real-time
2. Highlight each agent's role:
   - Detection Agent: Identifying anomalies
   - Diagnosis Agent: Root cause analysis
   - Prediction Agent: Impact forecasting
   - Resolution Agent: Executing fix
   - Communication Agent: Stakeholder notifications

**Narration**:
> "Five AI agents powered by AWS Bedrock coordinate autonomously. Detection identifies the anomaly, Diagnosis finds the root cause, Prediction forecasts impact, Resolution executes the fix, and Communication handles stakeholders."

**Checklist**:
- [ ] Agent confidence percentages visible (93%, 97%, 73%, 95%, 88%)
- [ ] Agent status updates in real-time
- [ ] All 5 agents mentioned
- [ ] AWS Bedrock integration clear

---

### Phase 4: Byzantine Consensus Visualization (15 seconds)
**Timing**: 0:45 - 1:00

**Screen**: Byzantine consensus section (may need to scroll down on `/ops`)

**Actions**:
1. Scroll to or highlight Byzantine consensus visualization
2. Show weighted voting in action:
   - Diagnosis: 40% weight (highest)
   - Prediction: 30% weight
   - Detection: 20% weight
   - Resolution: 10% weight
   - Communication: 0% (non-voting)
3. Point to consensus threshold: 85%

**Narration**:
> "Decisions require 85% consensus through Byzantine fault-tolerant voting. Diagnosis gets highest weight at 40%, ensuring root cause analysis drives decision-making."

**Checklist**:
- [ ] Byzantine consensus chart visible
- [ ] All agent weights displayed correctly (0.4, 0.3, 0.2, 0.1, 0)
- [ ] Consensus threshold 85% visible
- [ ] Weighted consensus value displayed (should be ~88%)

---

### Phase 5: Transparency & RAG Evidence (20 seconds) ⭐ CRITICAL
**Timing**: 1:00 - 1:20

**Screen**: Agent Transparency Modal

**Actions**:
1. Click Detection Agent card
2. Show transparency modal with 4 tabs
3. Click "🔬 Evidence" tab
4. Highlight "🧠 Evidence Sources (Amazon Titan Embeddings)"
5. Point to similarity scores:
   - INC-4512: 94% match
   - INC-3891: 89% match
   - RB-Database-007: 86% match

**Narration**:
> "Click any agent to see full transparency. Here's the Detection Agent's reasoning backed by Amazon Titan Embeddings RAG sources - 94%, 89%, and 86% similarity to historical incidents. This proves the AI's confidence is evidence-based, not a black box."

**Checklist**:
- [ ] Transparency modal opens on click
- [ ] All 4 tabs visible (Reasoning, Confidence, Evidence, Guardrails)
- [ ] "Evidence" tab clicked and displays correctly
- [ ] Amazon Titan Embeddings mentioned in header
- [ ] Three RAG sources visible with similarity scores
- [ ] Incident IDs shown (INC-4512, INC-3891, RB-Database-007)
- [ ] Resolution times and success rates visible

---

### Phase 6: Resolution & Final Metrics (10 seconds) ⭐ NEW
**Timing**: 1:20 - 1:30

**Screen**: Close modal, return to main dashboard

**Actions**:
1. Close transparency modal (X button or click outside)
2. Show incident resolution status
3. Highlight final MTTR: 2.8 minutes
4. Show "$103,360 saved" for this incident

**Narration**:
> "Incident resolved in 2.8 minutes - saving $103,000 compared to the industry average. This is autonomous, transparent, and production-ready."

**Checklist**:
- [ ] Modal closes cleanly
- [ ] Dashboard shows "Resolved" status
- [ ] MTTR: 2.8 minutes visible
- [ ] Savings calculation visible ($103,360 or similar)
- [ ] No errors in final view

---

## ✅ POST-RECORDING VERIFICATION

### Video Quality Checks
- [ ] Total runtime: 2.5 - 3.5 minutes
- [ ] Audio clear and professional
- [ ] All 6 phases present and in correct order
- [ ] No background noise or interruptions
- [ ] Mouse cursor visible and purposeful (not erratic)

### Feature Visibility Checks
- [ ] Byzantine consensus visualization shown ✅
- [ ] RAG sources with similarity scores shown ✅ (94%, 89%, 86%)
- [ ] Amazon Titan Embeddings explicitly mentioned ✅
- [ ] All 5 agents demonstrated ✅
- [ ] 85% consensus threshold visible ✅
- [ ] AWS Bedrock integration clear ✅
- [ ] Trust indicators visible (Guardrails, PII, etc.) ✅
- [ ] NO error boxes in final view ✅

### Narrative Structure Checks
- [ ] Phase 1: Started with main dashboard ($2.8M, MTTR)
- [ ] Phase 2: Triggered incident simulation
- [ ] Phase 3: Showed multi-agent coordination
- [ ] Phase 4: Demonstrated Byzantine consensus
- [ ] Phase 5: Clicked agent for transparency + RAG
- [ ] Phase 6: Showed final resolution and metrics

### Promise vs. Reality Alignment
- [ ] Script promises match what's visible in video
- [ ] No features mentioned that aren't shown
- [ ] No UI shown without explanation
- [ ] All AWS services mentioned are visible
- [ ] Byzantine consensus algorithm is visual, not just described
- [ ] RAG sources are shown, not just claimed

---

## 🚨 KNOWN ISSUES TO AVOID

### Issue: Red Error Box at End
**Problem**: Previous video ended with "1 error" message
**Solution**:
- [ ] Verify no console errors before recording
- [ ] If error appears, investigate and fix before continuing
- [ ] If unavoidable, add "Fallback Mode" UI banner with explanation
- [ ] DO NOT record with error visible unless intentionally demonstrating fallback

### Issue: RAG Not Visible
**Problem**: Previous video didn't show RAG sources (user reported "0% implementation")
**Solution**:
- [ ] MUST click agent card in Phase 5
- [ ] MUST click "Evidence" tab
- [ ] MUST show similarity scores clearly
- [ ] Point cursor at "Amazon Titan Embeddings" text
- [ ] Linger on this screen for 5-7 seconds (not just flash by)

### Issue: Phases Out of Order
**Problem**: Previous video showed 4 → 5 → 3 instead of 1 → 2 → 3 → 4 → 5 → 6
**Solution**:
- [ ] Follow this checklist sequentially from top to bottom
- [ ] Don't skip Phase 1 (main dashboard)
- [ ] Don't skip Phase 2 (trigger)
- [ ] Don't skip Phase 6 (resolution)
- [ ] Record in ONE continuous take to ensure correct order

---

## 📊 SUCCESS METRICS

**Video passes if**:
- ✅ All 6 phases present in correct order
- ✅ Byzantine consensus visualization visible with correct weights
- ✅ RAG sources shown with 94%, 89%, 86% similarity
- ✅ Amazon Titan Embeddings mentioned and shown
- ✅ No red error boxes in final view
- ✅ Total runtime 2.5-3.5 minutes
- ✅ Professional narration and mouse movement
- ✅ Every feature promised in script is demonstrated in video

**Video fails if**:
- ❌ Skips any of the 6 phases
- ❌ Shows phases out of order
- ❌ RAG sources not visible
- ❌ Red error box at end
- ❌ Mentions features not shown
- ❌ Runtime >4 minutes or <2 minutes
- ❌ Audio unclear or unprofessional

---

## 🎯 RECORDING TIPS

### Technical Tips
1. **Record in 1080p or higher** for clarity
2. **Use Zoom cursor highlight** or similar to make clicks obvious
3. **Slow down mouse movement** - deliberate, not frantic
4. **Pause 1-2 seconds** before/after each major action
5. **Keep narration conversational** - imagine explaining to a judge live

### Timing Tips
1. **Use a timer** - aim for 3 minutes total
2. **Practice once** before final recording
3. **Don't rush Phase 5** (RAG evidence) - this is most critical
4. **Linger on key metrics** - $2.8M, 94%, 85% should be on screen 2-3 seconds each

### Recovery Tips
1. **If you make a mistake** - stop, take a breath, restart from Phase 1
2. **If UI doesn't respond** - pause recording, fix, then restart
3. **If backend crashes** - restart services, verify all features, then record
4. **If error appears** - DO NOT continue recording, investigate and fix first

---

## 📁 DELIVERABLES

After successful recording:
- [ ] Raw video file (MP4, 1080p+)
- [ ] Edited video with consistent volume levels
- [ ] Transcript of narration (for accessibility)
- [ ] Screenshots of key moments (one per phase)
- [ ] Update `VIDEO_RERECORDING_CHECKLIST.md` with actual results
- [ ] Update `CRITICAL_GAPS_PROGRESS.md` marking Recommendation 1 complete

---

**Last Updated**: October 22, 2025
**Checklist Status**: Ready for use
**Estimated Recording Time**: 15-30 minutes (including setup and 1-2 practice runs)
