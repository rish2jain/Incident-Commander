# Utility Scripts

Organized utility scripts for the SwarmAI Incident Commander system.

## 📁 Directory Structure

```
scripts/
├── pdf/                    # PDF generation scripts
│   ├── generate_combined_pdf.py       # Combined documentation PDF
│   ├── generate_architecture_pdf.py   # Architecture diagrams PDF
│   ├── generate_judge_instructions_pdf.py  # Judge guide PDF
│   ├── create_judge_pdf.py           # Judge materials
│   └── create_simple_judge_pdf.py    # Simplified judge guide
│
├── monitoring/             # System monitoring
│   ├── check_system_status.py        # Health checks
│   └── setup_monitoring.py           # Monitoring setup
│
├── utilities/              # General utilities
│   ├── add_dashboard_to_api.py       # Dashboard integration
│   ├── dashboard_lambda.py           # Lambda dashboard
│   └── simple_dashboard_lambda.py    # Simplified Lambda
│
└── archive/               # Archived/deprecated scripts
    ├── convert_md_to_pdf.py          # Old conversion (v1)
    └── convert_md_to_pdf_v2.py       # Old conversion (v2)
```

## 📄 PDF Generation

### Generate All Documentation PDFs
```bash
python scripts/pdf/generate_combined_pdf.py
```

### Architecture Diagrams PDF
```bash
python scripts/pdf/generate_architecture_pdf.py
```

### Judge Instructions PDF
```bash
python scripts/pdf/generate_judge_instructions_pdf.py
```

## 📊 Monitoring

### Check System Health
```bash
python scripts/monitoring/check_system_status.py
```

### Setup Monitoring
```bash
python scripts/monitoring/setup_monitoring.py
```

## 🔧 Utilities

### Add Dashboard to API
```bash
python scripts/utilities/add_dashboard_to_api.py
```

### Lambda Dashboard Deployment
```bash
python scripts/utilities/dashboard_lambda.py
```

## 📦 Dependencies

PDF generation requires:
```bash
pip install markdown WeasyPrint Pillow
```

Monitoring requires:
```bash
pip install boto3 requests
```

## 🗄️ Archive

The `archive/` directory contains deprecated scripts:
- Old PDF conversion utilities
- Legacy deployment scripts
- Superseded by newer implementations

**Do not use archived scripts** - they are kept for reference only.

## 📖 Documentation

For more information, see:
- [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- [REPOSITORY_ORGANIZATION.md](../REPOSITORY_ORGANIZATION.md)

---

**Last Updated**: October 25, 2025
