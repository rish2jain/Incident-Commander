# 🎬 Demo Automation Scripts

Professional demo recording and automation tools for the Incident Commander system.

## 📋 Quick Reference

| Script                       | Purpose                                   | Usage                               |
| ---------------------------- | ----------------------------------------- | ----------------------------------- |
| `run_demo_recording.sh`      | **Quick Start** - Complete automated demo | `./run_demo_recording.sh`           |
| `automated_demo_recorder.py` | **Core Engine** - Playwright automation   | `python automated_demo_recorder.py` |
| `test_demo_recorder.py`      | **Validation** - Test setup and config    | `python test_demo_recorder.py`      |
| `demo_recorder_config.yaml`  | **Configuration** - All settings          | Edit for customization              |

## 🚀 Quick Start (30 Seconds)

```bash
# 1. Ensure services are running
cd dashboard && npm run dev &              # Terminal 1
python -m uvicorn src.main:app --reload & # Terminal 2

# 2. Run automated demo recording
cd scripts
./run_demo_recording.sh
```

**Output**: Full HD video, 9 screenshots, performance metrics

## 📦 What You Get

### 1. **Automated Demo Recorder** (`automated_demo_recorder.py`)

Complete Playwright-based automation that:

- ✅ Records 1920x1080 HD video
- ✅ Captures 9 key screenshots
- ✅ Collects performance metrics
- ✅ Executes 3-minute demo flow
- ✅ Saves judge-ready output

**Key Features**:

- **Video Recording**: Full HD with H.264 codec
- **Smart Screenshots**: Captures at decision points
- **Metrics Collection**: MTTR, cost savings, agent activity
- **Error Handling**: Screenshots on failure
- **Flexible Configuration**: YAML-based settings

### 2. **Quick Start Script** (`run_demo_recording.sh`)

One-command demo execution:

- ✅ Verifies services are running
- ✅ Sets up Python environment
- ✅ Installs dependencies
- ✅ Runs demo recorder
- ✅ Shows output summary

### 3. **Configuration** (`demo_recorder_config.yaml`)

Comprehensive settings for:

- Video resolution and quality
- Screenshot capture points
- Demo scenarios and timing
- Metrics collection
- Output organization
- Browser configuration

### 4. **Test Suite** (`test_demo_recorder.py`)

Validation tests for:

- Playwright installation
- Browser availability
- Configuration validity
- Dashboard connection
- Backend API connection

## 📖 Usage Guide

### Basic Recording

```bash
# Standard 3-minute demo
./run_demo_recording.sh
```

### Custom Scenarios

```bash
# Record specific incident type
python automated_demo_recorder.py --scenario ddos_attack

# Available scenarios:
#   database_cascade (default) - Database connection pool failure
#   ddos_attack               - Distributed denial of service
#   memory_leak               - Memory exhaustion
#   api_overload              - API rate limit breach
#   storage_failure           - Storage system failure
```

### Test Before Recording

```bash
# Validate setup
python test_demo_recorder.py

# Expected output:
# ✅ PASS Playwright Installation
# ✅ PASS Configuration File
# ✅ PASS Output Directories
# ✅ PASS Dashboard Connection
# ✅ PASS Backend Connection
```

## 🎯 Demo Flow (3 Minutes)

| Time | Phase            | Actions                 | Screenshot                  |
| ---- | ---------------- | ----------------------- | --------------------------- |
| 0:00 | **Initial**      | Dashboard loaded        | `dashboard_initial.png`     |
| 0:10 | **Trigger**      | Incident button clicked | `incident_triggered.png`    |
| 0:25 | **Discovery**    | Agents analyzing        | `agents_discovering.png`    |
| 0:45 | **Consensus**    | Byzantine voting        | `consensus_progress.png`    |
| 1:30 | **Decision**     | Consensus reached       | `consensus_reached.png`     |
| 2:00 | **Remediation**  | Fix executing           | `remediation_executing.png` |
| 2:30 | **Verification** | Validation running      | `verification_complete.png` |
| 2:50 | **Metrics**      | Final business data     | `final_metrics.png`         |
| 3:00 | **Complete**     | Demo finished           | `demo_complete.png`         |

## 📁 Output Structure

```
demo_recordings/
├── videos/
│   └── demo_20251019_143022.mp4          # 3-min HD video
│
├── screenshots/                           # 9 key moments
│   ├── 143025_dashboard_initial.png
│   ├── 143035_incident_triggered.png
│   ├── 143050_agents_discovering.png
│   ├── 143110_consensus_progress.png
│   ├── 143155_consensus_reached.png
│   ├── 143225_remediation_executing.png
│   ├── 143255_verification_complete.png
│   ├── 143315_final_metrics.png
│   └── 143325_demo_complete.png
│
├── metrics/
│   └── demo_metrics_20251019_143022.json  # Performance data
│
└── logs/
    └── demo_log_20251019_143022.txt       # Execution log
```

## ⚙️ Configuration

Edit `demo_recorder_config.yaml`:

### Video Settings

```yaml
video:
  width: 1920 # 1280 for faster testing
  height: 1080 # 720 for faster testing
  fps: 30
  quality: "high" # low, medium, high
```

### Custom Screenshots

```yaml
screenshots:
  capture_points:
    - name: "my_moment"
      description: "Custom screenshot"
      timing: "90s"
```

### Scenario Configuration

```yaml
scenarios:
  custom_scenario:
    name: "My Custom Demo"
    duration: 180
    incident_type: "custom_type"
    expected_mttr: 15
```

## 🔧 Installation

### Dependencies

```bash
# Core dependencies
pip install -r requirements_demo_recorder.txt

# Install Playwright browsers
playwright install chromium
```

**Required Packages**:

- `playwright>=1.45.0` - Browser automation
- `pyyaml>=6.0.1` - Configuration parsing
- `pandas>=2.0.0` - Metrics processing (optional)

### System Requirements

- **Python**: 3.9+
- **RAM**: 4GB minimum
- **Disk**: 2GB free
- **OS**: macOS, Linux, Windows

## 🐛 Troubleshooting

### "Dashboard not running"

```bash
# Start the Next.js dashboard
cd dashboard
npm install
npm run dev
```

### "Backend not accessible"

```bash
# Start FastAPI backend
python -m uvicorn src.main:app --reload
```

### "Playwright not installed"

```bash
# Install Playwright and browsers
pip install playwright
playwright install chromium
```

### "No screenshots captured"

```bash
# Check dashboard has data-test attributes
# Verify in dashboard/pages/index.tsx:
# <button data-test="trigger-database_cascade">Trigger</button>
```

### "Video file empty"

```bash
# Ensure browser context closes properly
# The video only saves when context.close() is called
```

## 📊 Metrics Output

Example `demo_metrics_*.json`:

```json
{
  "session_id": "20251019_143022",
  "duration_seconds": 180.5,
  "screenshots_captured": 9,
  "incidents_triggered": [
    {
      "type": "database_cascade",
      "triggered_at": "2025-10-19T14:30:35Z"
    }
  ],
  "business_metrics": {
    "mttr": "15 seconds",
    "cost_saved": "$103,360",
    "affected_users": "12,450",
    "sla_compliance": "100%"
  }
}
```

## 🎓 Best Practices

1. **Test First**: Run `test_demo_recorder.py` before recording
2. **Clean Output**: Delete old recordings before new ones
3. **Close Browsers**: Prevent port conflicts
4. **Monitor Execution**: Watch browser during recording
5. **Verify Output**: Check video plays correctly
6. **Save Configs**: Keep custom configurations versioned

## 📚 Documentation

- **Complete Guide**: [DEMO_RECORDER_GUIDE.md](DEMO_RECORDER_GUIDE.md)
- **Configuration**: [demo_recorder_config.yaml](demo_recorder_config.yaml)
- **Playwright Docs**: https://playwright.dev/python/

## 🏆 Judge Submission

Perfect for hackathon demos:

### Checklist

- [ ] 3-minute HD video recorded
- [ ] All 9 screenshots captured
- [ ] Metrics JSON file generated
- [ ] Business impact visible ($103,360)
- [ ] Agent consensus demonstrated
- [ ] Automated remediation shown

### Quick Package

```bash
# Create submission package
cd demo_recordings
zip -r ../incident_commander_demo.zip *

# Includes:
#   - videos/*.mp4 (Full demo)
#   - screenshots/*.png (9 key moments)
#   - metrics/*.json (Performance data)
```

## 💡 Advanced Usage

### Python API

```python
from automated_demo_recorder import DemoRecorder

async def custom_demo():
    recorder = DemoRecorder(
        base_url="http://localhost:3000",
        output_dir="my_demo"
    )

    # Run demo
    metrics = await recorder.run_3min_demo()

    # Access results
    print(f"MTTR: {metrics['business_metrics']['mttr']}")
```

### Custom Scenarios

```python
# Add to automated_demo_recorder.py
async def run_custom_scenario(self, scenario_config):
    # Your custom automation logic
    await self.trigger_incident(page, scenario_config['type'])
    await self.monitor_agent_consensus(page, scenario_config['duration'])
```

## 🚀 Next Steps

1. **Run Test**: `python test_demo_recorder.py`
2. **Record Demo**: `./run_demo_recording.sh`
3. **Review Output**: `open demo_recordings/`
4. **Customize**: Edit `demo_recorder_config.yaml`
5. **Share**: Package demo_recordings/ for submission

---

**Questions?** See [DEMO_RECORDER_GUIDE.md](DEMO_RECORDER_GUIDE.md) for detailed documentation.

**Ready?** Run `./run_demo_recording.sh` and create a professional demo! 🎬
