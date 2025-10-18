"""Configuration smoke tests for the ProductionValidationFramework."""

import pytest

from src.services.production_validation_framework import (
    ProductionValidationFramework,
    ValidationCategory,
    ValidationSeverity,
)


pytestmark = pytest.mark.manual


def test_validation_framework_registration() -> None:
    """Ensure core validation categories and budgets stay intact."""

    framework = ProductionValidationFramework()

    categories = {test.category for test in framework.validation_tests}
    expected = {
        ValidationCategory.LOAD_TESTING,
        ValidationCategory.SECURITY_TESTING,
        ValidationCategory.DISASTER_RECOVERY,
        ValidationCategory.COMPLIANCE_VALIDATION,
        ValidationCategory.EMERGENCY_PROCEDURES,
        ValidationCategory.DATA_INTEGRITY,
        ValidationCategory.COST_VALIDATION,
        ValidationCategory.RESILIENCE_TESTING,
    }

    assert expected.issubset(categories), "Missing validation categories"
    assert framework.cost_budget == 200.0


def test_blocker_tests_have_strict_thresholds() -> None:
    """Blocker tests should define explicit success criteria."""

    framework = ProductionValidationFramework()
    blocker_tests = [
        test for test in framework.validation_tests if test.severity == ValidationSeverity.BLOCKER
    ]

    assert blocker_tests, "Expected at least one blocker-level validation test"

    for test in blocker_tests:
        assert test.success_criteria, f"{test.name} lacks success criteria"
        assert test.timeout_minutes > 0, f"{test.name} requires a timeout"
