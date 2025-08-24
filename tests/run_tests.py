"""
Test Runner and Utilities
Created by Sergie Code

Main test runner with custom configurations and utilities.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Run all tests with comprehensive coverage"""
    
    print("🧪 Running Audio Enhancement Service Test Suite")
    print("=" * 60)
    
    # Test configuration
    pytest_args = [
        "-v",                           # Verbose output
        "--tb=short",                   # Short traceback format
        "--strict-markers",             # Strict marker checking
        "--disable-warnings",           # Disable warnings for cleaner output
        "-x",                          # Stop on first failure
        "--maxfail=5",                 # Stop after 5 failures
        str(Path(__file__).parent),    # Test directory
    ]
    
    # Add coverage if available
    try:
        import coverage
        pytest_args.extend([
            "--cov=app",                # Coverage for app module
            "--cov-report=html",        # HTML coverage report
            "--cov-report=term-missing", # Terminal coverage with missing lines
            "--cov-fail-under=80",      # Fail if coverage below 80%
        ])
        print("📊 Coverage reporting enabled")
    except ImportError:
        print("⚠️  Coverage reporting not available (install pytest-cov)")
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code


def run_quick_tests():
    """Run quick tests (excluding slow tests)"""
    
    print("⚡ Running Quick Test Suite")
    print("=" * 40)
    
    pytest_args = [
        "-v",
        "-m", "not slow",              # Skip slow tests
        "--tb=short",
        str(Path(__file__).parent),
    ]
    
    return pytest.main(pytest_args)


def run_security_tests():
    """Run only security tests"""
    
    print("🔒 Running Security Test Suite")
    print("=" * 40)
    
    pytest_args = [
        "-v",
        "--tb=short",
        str(Path(__file__).parent / "test_security.py"),
    ]
    
    return pytest.main(pytest_args)


def run_performance_tests():
    """Run only performance tests"""
    
    print("🚀 Running Performance Test Suite")
    print("=" * 40)
    
    pytest_args = [
        "-v",
        "--tb=short",
        str(Path(__file__).parent / "test_performance.py"),
    ]
    
    return pytest.main(pytest_args)


def run_integration_tests():
    """Run only integration tests"""
    
    print("🔗 Running Integration Test Suite")
    print("=" * 40)
    
    pytest_args = [
        "-v",
        "--tb=short",
        str(Path(__file__).parent / "test_integration.py"),
    ]
    
    return pytest.main(pytest_args)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Audio Enhancement Service Test Runner")
    parser.add_argument(
        "--suite", 
        choices=["all", "quick", "security", "performance", "integration"],
        default="all",
        help="Test suite to run"
    )
    
    args = parser.parse_args()
    
    if args.suite == "all":
        exit_code = run_all_tests()
    elif args.suite == "quick":
        exit_code = run_quick_tests()
    elif args.suite == "security":
        exit_code = run_security_tests()
    elif args.suite == "performance":
        exit_code = run_performance_tests()
    elif args.suite == "integration":
        exit_code = run_integration_tests()
    
    sys.exit(exit_code)
