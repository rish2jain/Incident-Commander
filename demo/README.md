# Demo & Testing Scripts

All demo recording and testing scripts for the SwarmAI Incident Commander system.

## 📁 Directory Structure

```
demo/
├── Demo Scripts
│   ├── start_demo.py              # Classic demo launcher
│   ├── start_simple.py            # Simplified demo
│   ├── record_demo.py             # Professional demo recorder
│   └── quick_demo_record.py       # Quick recording utility
│
└── Testing Scripts
    ├── test_aws_integration.py          # AWS integration tests
    ├── test_enhanced_recorder.py        # Recorder validation
    └── test_transparency_features.py    # Transparency UI tests
```

## 🎬 Running Demos

### Classic Demo (Recommended)
```bash
python demo/start_demo.py
```

### Quick Demo Recording
```bash
python demo/quick_demo_record.py
```

### Professional Recording
```bash
python demo/record_demo.py
```
Creates high-quality video recordings for presentations.

## 🧪 Running Tests

### AWS Integration Tests
```bash
python demo/test_aws_integration.py
```
Validates all 8 AWS AI service integrations.

### Transparency Features
```bash
python demo/test_transparency_features.py
```
Tests AI transparency dashboard functionality.

## 📖 Documentation

For detailed demo instructions, see:
- [DEMO_GUIDE.md](../DEMO_GUIDE.md) - Complete demo guide
- [VIDEO_RECORDING_SCRIPT.md](../VIDEO_RECORDING_SCRIPT.md) - Recording instructions
- [FINAL_DEMO_RECORDING_SCRIPT.md](../FINAL_DEMO_RECORDING_SCRIPT.md) - Final recording script

## 🎥 Demo Recordings

Recorded demos are stored in:
- `demo_recordings/videos/` - Video files
- `demo_recordings/screenshots/` - Screenshots
- `validation_screenshots/` - Validation captures

## ⚙️ Requirements

```bash
pip install -r requirements.txt
```

Key dependencies:
- FastAPI for backend
- Next.js for dashboard
- Playwright for browser automation
- OpenCV for video processing

## 🔧 Configuration

Demo scripts use:
- `.env` - Local environment variables
- `.env.hackathon` - Hackathon-specific config
- Docker Compose for services

---

**Last Updated**: October 25, 2025
