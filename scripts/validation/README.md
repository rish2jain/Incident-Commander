# Validation Scripts

All system validation and testing scripts for the Incident Commander system.

## Organization

### Core Validation
- `run_comprehensive_tests.py` - Complete system test suite execution
- `validate_api.py` - API endpoint validation
- `validate_infrastructure.py` - AWS infrastructure verification
- `validate_infrastructure_update.py` - Updated infrastructure checks

### Demo and Performance
- `demo_validation.py` - Demo system validation
- `validate_demo_performance.py` - Demo performance metrics
- `validate_websocket.py` - WebSocket functionality testing

### Integration Testing
- `validate_ultimate_integration.py` - Complete integration testing
- `test_aws_ai_integration.py` - AWS AI services integration

### Phase Validation (Historical)
- `validate_all_phases_complete.py` - All phases completion check
- `validate_phase4_complete.py` - Phase 4 completion validation

### Quick Tests
- `quick_hackathon_test.py` - Fast validation for hackathon demo
- `build_and_test.py` - Build and test combined

### Utilities
- `run_enhanced_system.py` - Enhanced system runner

## Usage

Run individual validation scripts:
```bash
python scripts/validation/validate_api.py
python scripts/validation/run_comprehensive_tests.py
```

## Notes
- Phase validation scripts are historical and may reference completed milestones
- For current system validation, use `run_comprehensive_tests.py`
- All scripts assume they're run from project root directory
