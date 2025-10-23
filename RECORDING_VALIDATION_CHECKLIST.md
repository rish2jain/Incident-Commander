# Recording Validation Checklist

## 🔍 Pre-Recording UI Validation

### Homepage Validation (/)

- [ ] "Key Features" section visible
- [ ] "All 8 AWS AI services integrated" text present (NO mock label)
- [ ] "$2.8M annual cost savings (458% ROI) (mock)" text present (WITH mock label)
- [ ] Navigation links to other dashboards working

### Operations Dashboard Validation (/ops)

- [ ] "All Systems Operational" status displays
- [ ] "Trigger Demo Incident" button present and functional
- [ ] "Active Incidents" section exists
- [ ] WebSocket connection status shows (green/connected preferred)

### Transparency Dashboard Validation (/transparency)

- [ ] "Predictive Prevention System" module visible
- [ ] "Byzantine Fault Tolerance Demo" module present
- [ ] Tabs working: Reasoning, Decisions, Confidence, Communication, Analytics
- [ ] "🚨 Trigger Demo" button functional

#### Prize Service Modules (Reasoning Tab):

- [ ] "Analysis by Amazon Q Business" card with $3K Prize badge
- [ ] "Action Plan by Nova Act" card with $3K Prize badge
- [ ] "Agent Lifecycle by Strands SDK" card with $3K Prize badge
- [ ] All three cards display in grid layout

### PowerDashboard Validation (/demo)

- [ ] "Live Incidents Resolved Today" counter present
- [ ] "Impact Comparison (Mock)" module visible
- [ ] "Business Impact (Mock)" section shows savings
- [ ] Professional layout and animations working

## 🎬 Recording Flow Test

### Test Sequence:

1. **Start at Homepage** → Verify Key Features display
2. **Navigate to Operations** → Test incident triggering
3. **Go to Transparency** → Verify all prize modules load
4. **Switch to PowerDashboard** → Confirm business metrics display
5. **Return to Transparency** → Test predictive prevention demo

### Critical UI Elements Check:

- [ ] All prize badges ($3K Prize) are visible and properly styled
- [ ] Color coding consistent (Orange=Amazon Q, Purple=Nova Act, Cyan=Strands)
- [ ] Text is readable at recording resolution
- [ ] Animations complete properly (no cut-off transitions)
- [ ] No console errors affecting UI display

## 📸 Screenshot Capture Points

### Timing for Each Screenshot:

1. **Predictive Prevention**: After "Incident Prevented Successfully" appears
2. **Homepage Features**: Static capture of Key Features section
3. **Active Incident**: Immediately after triggering demo incident
4. **Byzantine Fault**: During compromise/recovery sequence
5. **Amazon Q**: After incident analysis text appears
6. **Nova Act + Strands**: When both modules show active content
7. **Business Impact**: After metrics populate in PowerDashboard

## 🚨 Common Issues to Watch For

### UI Issues:

- [ ] Prize badges not displaying correctly
- [ ] Text overflow in smaller cards
- [ ] Grid layout breaking on different screen sizes
- [ ] Loading states showing instead of content

### Functional Issues:

- [ ] Incident trigger not working
- [ ] Tab switching not functioning
- [ ] WebSocket connection failing
- [ ] Animations not completing

### Content Issues:

- [ ] Mock labels in wrong places
- [ ] Prize service content not updating with incident state
- [ ] Timing issues with dynamic content display

## ✅ Final Validation Commands

```bash
# Ensure dashboard is running
cd dashboard && npm run dev

# Test all routes
curl http://localhost:3000/
curl http://localhost:3000/demo
curl http://localhost:3000/transparency
curl http://localhost:3000/ops

# Check for console errors in browser dev tools
# Verify responsive design at 1920x1080
# Test incident triggering end-to-end
```

## 🎯 Success Criteria

### Before Recording:

- [ ] All 4 dashboard views load without errors
- [ ] All prize service modules display correctly
- [ ] Incident triggering works reliably
- [ ] UI is responsive and professional
- [ ] No broken links or missing assets

### During Recording:

- [ ] Smooth transitions between views
- [ ] All dynamic content loads as expected
- [ ] No UI glitches or loading states visible
- [ ] Professional appearance maintained throughout

This checklist ensures your recording captures the system at its best, with all prize-winning features clearly visible and functioning properly.
