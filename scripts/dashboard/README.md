# Dashboard Scripts

Dashboard-related utilities and server scripts for the Incident Commander system.

## Scripts

### Backends and Servers
- `dashboard_backend.py` - Dashboard backend server
- `simple_dashboard.py` - Simple demo dashboard
- `serve_demo_dashboards.py` - Demo dashboard server
- `start_refined_dashboard.py` - Main refined dashboard launcher

### Setup and Configuration
- `setup_cloudwatch_dashboard.py` - CloudWatch dashboard configuration

### Testing and Development
- `mock_backend.py` - Mock backend for development/testing
- `inspect_dashboard.py` - Dashboard inspection utility

## Usage

### Start Dashboard
```bash
python scripts/dashboard/start_refined_dashboard.py
```

### Development with Mock Backend
```bash
python scripts/dashboard/mock_backend.py
```

### Setup CloudWatch Monitoring
```bash
python scripts/dashboard/setup_cloudwatch_dashboard.py
```

## Notes
- Main dashboard is React/Next.js in `dashboard/` directory
- These are Python backends and utilities
- Legacy implementations in `dashboard/archive/`
- Default ports and configurations vary by script
