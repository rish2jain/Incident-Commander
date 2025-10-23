# 📁 Repository Organization Guide

**SwarmAI Incident Commander** - Complete repository structure and navigation guide

Last Updated: October 23, 2025

---

## 🎯 Quick Navigation

### For Judges & Evaluators
- **[JUDGE_REVIEW_INSTRUCTIONS.md](JUDGE_REVIEW_INSTRUCTIONS.md)** - Start here! Complete evaluation guide
- **[SwarmAI_Architecture_Diagrams.pdf](SwarmAI_Architecture_Diagrams.pdf)** - Printable architecture reference
- **[SYSTEM_ARCHITECTURE_DIAGRAMS.md](SYSTEM_ARCHITECTURE_DIAGRAMS.md)** - Interactive architecture diagrams

### For Developers
- **[README.md](README.md)** - Developer-focused system overview and quick start
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture details
- **[API.md](API.md)** - Complete API documentation

### For Business Stakeholders
- **[hackathon/MASTER_SUBMISSION_GUIDE.md](hackathon/MASTER_SUBMISSION_GUIDE.md)** - Business case and ROI
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Enterprise deployment guide

---

## 📂 Directory Structure

```
incident-commander/
│
├── 📄 Core Documentation
│   ├── README.md                           # Main project overview
│   ├── JUDGE_REVIEW_INSTRUCTIONS.md        # 🆕 Judge evaluation guide
│   ├── SYSTEM_ARCHITECTURE_DIAGRAMS.md     # 🆕 Interactive architecture diagrams
│   ├── SwarmAI_Architecture_Diagrams.pdf   # 🆕 Printable architecture PDF
│   ├── REPOSITORY_ORGANIZATION.md          # 🆕 This file
│   ├── ARCHITECTURE.md                     # Technical architecture
│   ├── DEPLOYMENT.md                       # Deployment guide
│   ├── API.md                              # API documentation
│   └── MODERNIZATION_PLAN.md               # System evolution roadmap
│
├── 🎨 Branding Assets
│   ├── SwarmAI solid.png                   # Logo - solid background
│   ├── SwarmAI with Name.png               # Logo with text
│   └── SwarmAI only logo.png               # Logo only
│
├── 🏆 Hackathon Materials
│   └── hackathon/
│       ├── README.md                       # Hackathon overview
│       ├── MASTER_SUBMISSION_GUIDE.md      # Complete submission package
│       ├── COMPREHENSIVE_JUDGE_GUIDE.md    # Detailed evaluation guide
│       ├── HACKATHON_ARCHITECTURE.md       # Architecture for judges
│       ├── DEPLOYMENT_CAPABILITIES_SUMMARY.md
│       └── [Additional submission materials]
│
├── 💻 Source Code
│   ├── src/                                # Backend Python code
│   │   ├── main.py                         # FastAPI application entry
│   │   ├── api/                            # API routers and endpoints
│   │   ├── services/                       # Core services and agents
│   │   ├── models/                         # Data models
│   │   ├── schemas/                        # Pydantic schemas
│   │   ├── utils/                          # Utilities and helpers
│   │   └── [Additional modules]
│   │
│   ├── agents/                             # Multi-agent system
│   │   ├── detection/                      # Detection agent
│   │   ├── diagnosis/                      # Diagnosis agent
│   │   ├── prediction/                     # Prediction agent
│   │   ├── resolution/                     # Resolution agent
│   │   └── communication/                  # Communication agent
│   │
│   └── dashboard/                          # Frontend Next.js application
│       ├── app/                            # Next.js 14 app router
│       │   ├── demo/                       # PowerDashboard (executive view)
│       │   ├── transparency/               # AI Transparency dashboard
│       │   └── ops/                        # Operations dashboard
│       ├── src/components/                 # React components
│       ├── package.json                    # Node dependencies
│       └── [Additional frontend files]
│
├── 🧪 Tests
│   └── tests/
│       ├── unit/                           # Unit tests
│       ├── integration/                    # Integration tests
│       ├── contract/                       # Contract tests
│       ├── benchmarks/                     # Performance benchmarks
│       └── [Additional test suites]
│
├── 🏗️ Infrastructure
│   └── infrastructure/
│       ├── cdk/                            # AWS CDK deployment
│       │   ├── app.py                      # CDK app entry point
│       │   ├── incident_commander_stack.py # Main stack
│       │   └── [Additional stacks]
│       └── stacks/                         # Modular stack components
│
├── 📊 Demo & Recordings
│   └── demo_recordings/
│       ├── videos/                         # Demo video recordings
│       ├── screenshots/                    # Demo screenshots
│       └── [Recording metadata]
│
├── 🚀 Deployment Scripts
│   ├── deploy_complete_system.py           # Complete deployment orchestration
│   ├── deploy_production.py                # Production deployment
│   ├── setup_monitoring.py                 # Monitoring setup
│   ├── validate_deployment.py              # Deployment validation
│   └── [Additional deployment tools]
│
├── 🎬 Demo & Testing Scripts
│   ├── start_demo.py                       # Classic demo launcher
│   ├── record_demo.py                      # Professional demo recorder
│   ├── quick_demo_record.py                # Quick demo recording
│   └── [Additional demo tools]
│
├── 📦 Configuration
│   ├── .env.example                        # Environment template
│   ├── .env.hackathon                      # Hackathon configuration
│   ├── requirements.txt                    # Python dependencies
│   ├── pyproject.toml                      # Python project config
│   ├── docker-compose.yml                  # Docker services
│   ├── Dockerfile                          # Container image
│   └── Makefile                            # Build automation
│
├── 🗄️ Archive (Consolidated Old Files)
│   └── archive/
│       └── old_documentation/              # Historical documents
│           ├── README.md                   # Archive index
│           ├── MODERNIZATION_PLAN_.md      # Old version
│           ├── claudedocs/                 # Historical analysis
│           └── [Other archived files]
│
└── 🤖 AI Assistant Configuration
    ├── .kiro/                              # Kiro IDE settings
    │   └── steering/                       # AI steering rules
    │       ├── architecture.md
    │       ├── tech.md
    │       ├── security.md
    │       └── [Other steering docs]
    └── .serena/                            # Serena memory
        └── memories/                       # AI memory storage
```

---

## 🎯 Document Purpose Guide

### Judge & Evaluator Documents

| Document | Purpose | Time to Review |
|----------|---------|----------------|
| **JUDGE_REVIEW_INSTRUCTIONS.md** | Complete evaluation guide with scoring rubric | 15-30 min |
| **SwarmAI_Architecture_Diagrams.pdf** | Printable architecture reference | 10-15 min |
| **SYSTEM_ARCHITECTURE_DIAGRAMS.md** | Interactive diagrams (view on GitHub) | 15-20 min |
| **hackathon/COMPREHENSIVE_JUDGE_GUIDE.md** | Detailed hackathon evaluation | 20-30 min |
| **demo_recordings/** | Professional HD demo recordings | 2-5 min |

---

### Developer Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| **README.md** | System overview, quick start, features | All developers |
| **ARCHITECTURE.md** | Technical architecture details | Engineers |
| **API.md** | API endpoint documentation | API consumers |
| **DEPLOYMENT.md** | Deployment and operations guide | DevOps |
| **src/** | Source code implementation | Developers |

---

### Business Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| **hackathon/MASTER_SUBMISSION_GUIDE.md** | Business case and ROI | Executives, judges |
| **MODERNIZATION_PLAN.md** | System evolution roadmap | Product managers |
| **JUDGE_REVIEW_INSTRUCTIONS.md** | Business value assessment | Business stakeholders |

---

## 🔍 Finding What You Need

### "I want to evaluate the system"
→ Start with **[JUDGE_REVIEW_INSTRUCTIONS.md](JUDGE_REVIEW_INSTRUCTIONS.md)**

### "I want to understand the architecture"
→ See **[SYSTEM_ARCHITECTURE_DIAGRAMS.md](SYSTEM_ARCHITECTURE_DIAGRAMS.md)** or **[SwarmAI_Architecture_Diagrams.pdf](SwarmAI_Architecture_Diagrams.pdf)**

### "I want to run the demo"
→ Follow **[README.md Quick Start](README.md#-quick-start)** section

### "I want to deploy to production"
→ Follow **[DEPLOYMENT.md](DEPLOYMENT.md)** guide

### "I want to integrate with the API"
→ See **[API.md](API.md)** documentation

### "I want to contribute code"
→ Review **[README.md Contributing](README.md#-contributing)** section

### "I want to see the business case"
→ Read **[hackathon/MASTER_SUBMISSION_GUIDE.md](hackathon/MASTER_SUBMISSION_GUIDE.md)**

---

## 📋 Recent Changes (October 23, 2025)

### 🆕 New Files
- **JUDGE_REVIEW_INSTRUCTIONS.md** - Comprehensive judge evaluation guide
- **SYSTEM_ARCHITECTURE_DIAGRAMS.md** - Interactive architecture diagrams with Mermaid
- **SwarmAI_Architecture_Diagrams.pdf** - Printable architecture reference
- **REPOSITORY_ORGANIZATION.md** - This navigation guide
- **generate_architecture_pdf.py** - PDF generation script

### 📁 Reorganized
- Moved duplicate files to `archive/old_documentation/`
- Consolidated modernization plans (kept MODERNIZATION_PLAN.md)
- Archived old recording documentation
- Organized demo recordings

### 🗑️ Archived Files
- `MODERNIZATION_PLAN_.md` → `archive/old_documentation/`
- `ENHANCED_RECORDING_README.md` → `archive/old_documentation/`
- `SEGMENTED_MP4_RECORDING_SYSTEM.md` → `archive/old_documentation/`
- `claudedocs/` → `archive/old_documentation/claudedocs/`

---

## 🚀 Quick Start Paths

### Path 1: Judge Evaluation (30 seconds)
```bash
1. Read: JUDGE_REVIEW_INSTRUCTIONS.md
2. Choose evaluation method:
   - Live AWS: curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/health
   - Local: cd dashboard && npm run dev
   - Recording: Open demo_recordings/
```

### Path 2: Developer Setup (2 minutes)
```bash
git clone <repository-url>
cd incident-commander
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
python src/main.py
```

### Path 3: Architecture Review (15 minutes)
```bash
1. Open: SwarmAI_Architecture_Diagrams.pdf
2. Review: SYSTEM_ARCHITECTURE_DIAGRAMS.md (interactive diagrams)
3. Read: ARCHITECTURE.md (technical details)
```

---

## 📊 Repository Statistics

- **Total Lines of Code**: ~50,000+ (Python + TypeScript)
- **Test Coverage**: 95%+
- **AWS Services Integrated**: 8/8
- **Agent Count**: 5 specialized agents
- **Dashboard Views**: 3 (Demo, Transparency, Operations)
- **API Endpoints**: 50+
- **Documentation Files**: 30+

---

## 🏆 Key Deliverables

### For Hackathon Submission
✅ **Code Repository** - Complete, documented, production-ready
✅ **Live Demo** - AWS deployment + local setup
✅ **Architecture Diagrams** - PDF + interactive markdown
✅ **Judge Instructions** - Comprehensive evaluation guide
✅ **Business Case** - ROI calculator, competitive analysis
✅ **Demo Recording** - Professional HD video + screenshots
✅ **Documentation** - Complete technical and business docs

### Quality Standards
✅ **Production Code** - Type-safe, tested, documented
✅ **Enterprise Architecture** - Scalable, secure, resilient
✅ **Professional Presentation** - Executive-ready materials
✅ **Complete Integration** - All 8 AWS AI services
✅ **Quantified Value** - Industry benchmark-based ROI

---

## 🔗 External Resources

- **Live AWS Deployment**: https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com
- **API Documentation**: http://localhost:8000/docs (when running locally)
- **Dashboard**: http://localhost:3000 (when running locally)

---

## 📞 Support & Questions

For questions or issues:
1. Check relevant documentation in this guide
2. Review API documentation at [API.md](API.md)
3. See troubleshooting in [JUDGE_REVIEW_INSTRUCTIONS.md](JUDGE_REVIEW_INSTRUCTIONS.md)
4. Review deployment logs and health endpoints

---

## ✅ File Verification Checklist

Use this to verify all key files are present:

- [ ] JUDGE_REVIEW_INSTRUCTIONS.md
- [ ] SYSTEM_ARCHITECTURE_DIAGRAMS.md
- [ ] SwarmAI_Architecture_Diagrams.pdf
- [ ] REPOSITORY_ORGANIZATION.md
- [ ] README.md
- [ ] ARCHITECTURE.md
- [ ] API.md
- [ ] DEPLOYMENT.md
- [ ] hackathon/MASTER_SUBMISSION_GUIDE.md
- [ ] hackathon/COMPREHENSIVE_JUDGE_GUIDE.md
- [ ] src/main.py
- [ ] dashboard/package.json
- [ ] requirements.txt
- [ ] docker-compose.yml

---

**Repository Status**: ✅ **Production Ready - Organized & Documented**

All files consolidated, duplicate content archived, and comprehensive navigation guides created for optimal judge and developer experience.

---

**Last Updated**: October 23, 2025
**Version**: 1.0
**Maintained By**: SwarmAI Development Team
