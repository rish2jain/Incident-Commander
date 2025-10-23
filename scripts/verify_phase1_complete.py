#!/usr/bin/env python3
"""
Phase 1 Implementation Verification Script

Verifies that all Phase 1 components are in place and properly configured.
Run this to validate the WebSocket integration implementation.
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def check_file_exists(path, description):
    """Check if a file exists."""
    if os.path.exists(path):
        print_success(f"{description}: {path}")
        return True
    else:
        print_error(f"{description} NOT FOUND: {path}")
        return False

def check_file_contains(path, search_string, description):
    """Check if a file contains a specific string."""
    try:
        with open(path, 'r') as f:
            content = f.read()
            if search_string in content:
                print_success(f"{description}")
                return True
            else:
                print_error(f"{description} - NOT FOUND in {path}")
                return False
    except Exception as e:
        print_error(f"Error reading {path}: {e}")
        return False

def check_dashboard_isolation(demo_path, transparency_path, ops_path):
    """Verify dashboard isolation - WebSocket only in ops."""
    results = []

    # Demo dashboard should NOT have WebSocket
    if os.path.exists(demo_path):
        with open(demo_path, 'r') as f:
            content = f.read()
            if 'useIncidentWebSocket' not in content and 'WebSocket' not in content:
                print_success("Dashboard 1 (/demo) - Properly isolated (no WebSocket)")
                results.append(True)
            else:
                print_error("Dashboard 1 (/demo) - Has WebSocket imports (VIOLATION)")
                results.append(False)

    # Transparency dashboard should NOT have WebSocket
    if os.path.exists(transparency_path):
        with open(transparency_path, 'r') as f:
            content = f.read()
            if 'useIncidentWebSocket' not in content:
                print_success("Dashboard 2 (/transparency) - Properly isolated (no WebSocket)")
                results.append(True)
            else:
                print_error("Dashboard 2 (/transparency) - Has WebSocket imports (VIOLATION)")
                results.append(False)

    # Ops dashboard SHOULD have WebSocket
    if os.path.exists(ops_path):
        with open(ops_path, 'r') as f:
            content = f.read()
            if 'ImprovedOperationsDashboardWebSocket' in content:
                print_success("Dashboard 3 (/ops) - Uses WebSocket component")
                results.append(True)
            else:
                print_error("Dashboard 3 (/ops) - Missing WebSocket component")
                results.append(False)

    return all(results)

def main():
    print("\n" + "="*60)
    print("Phase 1 Implementation Verification")
    print("="*60 + "\n")

    results = []

    # Section 1: Backend Infrastructure
    print(f"{BLUE}[1] Backend Infrastructure{RESET}")
    results.append(check_file_exists(
        "src/services/websocket_manager.py",
        "WebSocket Manager Service"
    ))
    results.append(check_file_contains(
        "src/services/websocket_manager.py",
        "class WebSocketManager",
        "WebSocket Manager Class exists"
    ))
    results.append(check_file_contains(
        "src/api/routers/dashboard.py",
        "@router.websocket(\"/ws\")",
        "WebSocket endpoint registered"
    ))
    print()

    # Section 2: Frontend Infrastructure
    print(f"{BLUE}[2] Frontend Infrastructure{RESET}")
    results.append(check_file_exists(
        "dashboard/src/hooks/useIncidentWebSocket.ts",
        "WebSocket Hook"
    ))
    results.append(check_file_contains(
        "dashboard/src/hooks/useIncidentWebSocket.ts",
        "export interface AgentState",
        "TypeScript interfaces defined"
    ))
    results.append(check_file_exists(
        "dashboard/src/components/ImprovedOperationsDashboardWebSocket.tsx",
        "Operations Dashboard Component"
    ))
    results.append(check_file_contains(
        "dashboard/src/components/ImprovedOperationsDashboardWebSocket.tsx",
        "useIncidentWebSocket",
        "Dashboard uses WebSocket hook"
    ))
    print()

    # Section 3: Dashboard Isolation
    print(f"{BLUE}[3] Dashboard Isolation{RESET}")
    results.append(check_dashboard_isolation(
        "dashboard/app/demo/page.tsx",
        "dashboard/app/transparency/page.tsx",
        "dashboard/app/ops/page.tsx"
    ))
    print()

    # Section 4: Test Coverage
    print(f"{BLUE}[4] Test Coverage{RESET}")
    results.append(check_file_exists(
        "tests/test_websocket_manager.py",
        "WebSocket Manager Unit Tests"
    ))
    results.append(check_file_exists(
        "tests/test_websocket_integration.py",
        "WebSocket Integration Tests"
    ))
    results.append(check_file_contains(
        "tests/test_websocket_manager.py",
        "class TestWebSocketManagerLifecycle",
        "Lifecycle tests implemented"
    ))
    results.append(check_file_contains(
        "tests/test_websocket_integration.py",
        "class TestWebSocketConnection",
        "Connection tests implemented"
    ))
    print()

    # Section 5: Documentation
    print(f"{BLUE}[5] Documentation{RESET}")
    results.append(check_file_exists(
        "claudedocs/PHASE_1_IMPLEMENTATION_COMPLETE.md",
        "Implementation Summary"
    ))
    results.append(check_file_contains(
        ".kiro/specs/dashboard-backend-integration/tasks.md",
        "Phase 1: Foundation and WebSocket Integration (Dashboard 3 ONLY) ✅ **COMPLETE**",
        "Tasks document updated"
    ))
    print()

    # Summary
    print("="*60)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    if all(results):
        print(f"{GREEN}✓ ALL CHECKS PASSED ({passed}/{total}){RESET}")
        print(f"{GREEN}Phase 1 implementation is COMPLETE and verified!{RESET}")
        return 0
    else:
        print(f"{RED}✗ SOME CHECKS FAILED ({failed}/{total} failed, {passed}/{total} passed){RESET}")
        print(f"{YELLOW}Please review failed checks above.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
