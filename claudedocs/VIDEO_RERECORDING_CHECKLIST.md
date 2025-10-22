# Video Re-Recording Checklist

**Purpose**: Fix video narrative structure and demonstrate all promised features
**Date**: October 22, 2025
**Target**: 3-minute judge-ready demo following 6-phase structure

---

## 🚨 CRITICAL CHANGES FROM PREVIOUS VIDEO

### What Was Missing (User-Reported Issues)
❌ **Issue #1**: Video didn't follow 6-phase structure (skipped Phase 1, 2, 6)
❌ **Issue #2**: RAG visualization "0% implementation" - **agent card was never clicked**
❌ **Issue #3**: Resolution Agent weight was 20% (incorrect) vs 10% (correct)
❌ **Issue #4**: Consensus threshold inconsistent (70%, 80%, 85%)
❌ **Issue #5**: Red error box at end of video

### What's Now Fixed ✅
✅ **Issue #1**: Complete 6-phase script below (Phases 1-6 all present)
✅ **Issue #2**: Phase 5 now includes DETAILED RAG demonstration (25 seconds, step-by-step)
✅ **Issue #3**: Resolution Agent weight CORRECTED to 10% in all code and docs
✅ **Issue #4**: Consensus threshold STANDARDIZED to 85% everywhere
✅ **Issue #5**: Pre-recording verification includes error check

### Key Features MUST Be Demonstrated
🎯 **Phase 4**: Byzantine consensus with CORRECTED weights (Resolution: 10%, Communication: 0%)
🎯 **Phase 5**: Click agent card → Show all 4 tabs → Evidence tab → RAG sources with 94%, 89%, 86% similarity
🎯 **Threshold**: 85% consensus mentioned explicitly in narration
🎯 **No Errors**: Final dashboard must be clean (no red error boxes)

### New Total Runtime
- Previous video: ~2-3 minutes (but missing phases)
- Updated script: ~3-3.5 minutes (complete 6-phase story)
  - Phase 1: 15s (NEW)
  - Phase 2: 10s (NEW)
  - Phase 3: 20s
  - Phase 4: 18s (UPDATED with correct weights)
  - Phase 5: 25s (ENHANCED with full RAG demo)
  - Phase 6: 10s (NEW)

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

### Phase 4: Byzantine Consensus Visualization (18 seconds) ⭐ UPDATED WEIGHTS
**Timing**: 0:45 - 1:03

**Screen**: Byzantine consensus section (may need to scroll down on `/ops`)

**IMPORTANT**: This demonstrates the CORRECTED agent weights (Resolution: 10%, Communication: 0%)

**Actions** (DETAILED):
1. **Scroll to Byzantine consensus visualization** (if not visible)
2. **Point to title**: "Byzantine Consensus Voting"
3. **Hover over each agent weight** and call out the values:
   - **Diagnosis: 40% (0.4)** - Point cursor at bar and weight value
   - **Prediction: 30% (0.3)** - Point cursor at bar and weight value
   - **Detection: 20% (0.2)** - Point cursor at bar and weight value
   - **Resolution: 10% (0.1)** ✅ CORRECTED (was 20% in old docs)
   - **Communication: 0% (0.0)** ✅ NON-VOTING (was 10% in old docs)
4. **Point to consensus threshold**: "85%" ✅ STANDARDIZED
5. **Point to weighted consensus value**: Should show ~88% (above threshold)
6. **Highlight "Consensus Reached" indicator** (should be green/approved)

**Narration** (ENHANCED):
> "Every decision goes through Byzantine fault-tolerant consensus. Notice the weighted voting - Diagnosis gets the highest weight at 40% because identifying the root cause is critical. Prediction: 30%, Detection: 20%, Resolution: 10%. Communication Agent doesn't vote - it's informational only at 0%. The threshold is 85% weighted agreement for autonomous action. Right now we're at 88% - consensus reached, incident resolution approved."

**Mouse Movement Notes**:
- Point at each weight percentage for 1 second
- Draw cursor along the consensus progress bar
- Circle around "85% threshold" text
- Emphasize Communication Agent showing 0% (this is intentional, not a bug)

**Checklist** (EXPANDED):
- [ ] Byzantine consensus chart/visualization visible
- [ ] Title "Byzantine Consensus" or similar visible
- [ ] **5 agents listed**: Detection, Diagnosis, Prediction, Resolution, Communication
- [ ] **Diagnosis: 40% (0.4)** - highest weight visible ✅
- [ ] **Prediction: 30% (0.3)** - second highest visible ✅
- [ ] **Detection: 20% (0.2)** - third weight visible ✅
- [ ] **Resolution: 10% (0.1)** - CORRECTED weight visible ✅
- [ ] **Communication: 0% (0.0)** - non-voting status clear ✅
- [ ] Weights sum to 100% (1.0) mathematically correct ✅
- [ ] **Consensus threshold: 85%** displayed ✅ STANDARDIZED
- [ ] **Weighted consensus value** displayed (should be ~88%)
- [ ] Consensus status indicator visible (green/approved/reached)
- [ ] Narration explicitly states "Resolution: 10%" ✅
- [ ] Narration explains Communication Agent is non-voting ✅
- [ ] Narration mentions "85% threshold" ✅

---

### Phase 5: Transparency & RAG Evidence (25 seconds) ⭐ CRITICAL - PREVIOUSLY MISSING
**Timing**: 1:00 - 1:25

**Screen**: Agent Transparency Modal

**CRITICAL**: This is the #1 missing feature from the previous video. User reported "0% implementation" because we didn't click the agent card. We MUST demonstrate this fully.

**Actions** (DETAILED STEP-BY-STEP):
1. **Click Detection Agent card** (wait for modal to fully open - 1 second)
2. **Show all 4 tabs** visible at top: "Reasoning", "Confidence", "🔬 Evidence", "Guardrails"
3. **Briefly show "Reasoning" tab** (2 seconds) - hover mouse over reasoning text
4. **Click "Confidence" tab** (2 seconds) - show confidence breakdown bars
5. **Click "🔬 Evidence" tab** (THE MOST CRITICAL PART - 7 seconds minimum)
   - Point cursor at "🧠 Evidence Sources (Amazon Titan Embeddings)" header
   - Hover over each RAG source card to highlight them:
     - **INC-4512**: "Database Connection Pool Exhaustion" - **94% match** badge
     - **INC-3891**: "API Gateway Timeout Cascade" - **89% match** badge
     - **RB-Database-007**: "Database Cascade Failure Response" - **86% match** badge
   - Point at "Resolution time: 2.1 min" and "100% success rate" for first source
6. **Click "Guardrails" tab** (2 seconds) - show AWS Bedrock Guardrails checks
7. **Linger on modal** for 2 seconds before closing to let judges absorb information

**Narration** (ENHANCED):
> "Let me show you what makes this truly transparent. Click any agent card... [PAUSE while clicking] ...and you see EVERYTHING. Four tabs of complete visibility. Here's the Reasoning... [switch tab] ...the Confidence breakdown... [switch tab] ...and most importantly, the Evidence tab. This shows Amazon Titan Embeddings RAG sources - real historical incidents with 94%, 89%, and 86% similarity scores. The AI isn't guessing - it's learning from past incidents that were successfully resolved in 2 minutes with 100% success rates. [switch tab] Plus AWS Bedrock Guardrails ensuring safety at every step."

**Mouse Movement Notes**:
- **Slow and deliberate** - this is the money shot
- Point cursor at each similarity score badge (94%, 89%, 86%) for 1 second each
- Circle mouse around "Amazon Titan Embeddings" text
- Hover over incident IDs to make them stand out
- Don't rush - judges need time to read the content

**Checklist** (EXPANDED):
- [ ] Detection Agent card clicked (not Diagnosis or other agents)
- [ ] Modal opens with smooth animation
- [ ] All 4 tabs visible and labeled clearly
- [ ] "Reasoning" tab shown first (default tab)
- [ ] "Confidence" tab clicked and confidence bars visible
- [ ] "🔬 Evidence" tab clicked (MOST IMPORTANT)
- [ ] "🧠 Evidence Sources (Amazon Titan Embeddings)" header visible
- [ ] Three RAG source cards visible with distinct borders
- [ ] Similarity badges clearly visible: 94%, 89%, 86%
- [ ] Incident IDs shown: INC-4512, INC-3891, RB-Database-007
- [ ] Incident titles visible: "Database Connection Pool Exhaustion", etc.
- [ ] Resolution time visible: "2.1 min" for first source
- [ ] Success rate visible: "100% success rate" for first source
- [ ] "Guardrails" tab clicked and checks visible
- [ ] Total time on Evidence tab: 7+ seconds (don't rush!)
- [ ] Narration mentions "Amazon Titan Embeddings" explicitly
- [ ] Narration mentions all three similarity scores (94%, 89%, 86%)

---

### Phase 6: Resolution & Final Metrics (10 seconds) ⭐ NEW
**Timing**: 1:25 - 1:35

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

### Previously Missing Features - NOW INCLUDED ✅
**These were reported as "0% implementation" but are actually complete - now properly demonstrated:**

- [ ] **RAG Visualization** (Issue #2):
  - [ ] Agent card clicked in Phase 5 ✅
  - [ ] Transparency modal opened ✅
  - [ ] "Evidence" tab shown ✅
  - [ ] "Amazon Titan Embeddings" text visible ✅
  - [ ] Three similarity scores visible: 94%, 89%, 86% ✅
  - [ ] Incident IDs visible: INC-4512, INC-3891, RB-Database-007 ✅
  - [ ] Resolution times shown (2.1 min, 1.8 min) ✅
  - [ ] Total screen time on Evidence tab: 7+ seconds ✅

- [ ] **Corrected Agent Weights** (Issue #3):
  - [ ] Resolution Agent shows 10% (not 20%) ✅
  - [ ] Communication Agent shows 0% (non-voting) ✅
  - [ ] Narration states "Resolution: 10%" explicitly ✅
  - [ ] Narration explains Communication is non-voting ✅

- [ ] **Standardized Threshold** (Issue #4):
  - [ ] Consensus threshold shows 85% (not 70% or 80%) ✅
  - [ ] Narration mentions "85% threshold" ✅

- [ ] **6-Phase Structure** (Issue #1):
  - [ ] Phase 1 (Main Dashboard) shown ✅
  - [ ] Phase 2 (Incident Trigger) shown ✅
  - [ ] Phase 3 (Multi-Agent) shown ✅
  - [ ] Phase 4 (Byzantine Consensus) shown ✅
  - [ ] Phase 5 (Transparency/RAG) shown ✅
  - [ ] Phase 6 (Resolution/Metrics) shown ✅
  - [ ] All phases in correct order (1→2→3→4→5→6) ✅

- [ ] **No Errors** (Issue #5):
  - [ ] No red error boxes in any frame ✅
  - [ ] Dashboard loads cleanly throughout ✅
  - [ ] Final view is professional and error-free ✅

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
