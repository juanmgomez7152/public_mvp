#!/usr/bin/env python3
"""
Test Runner Script for Omnicom MVP Project

This script runs all unit tests and integration tests for the project.
Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --coverage         # Run with coverage report
"""

import unittest
import sys
import os
import argparse
from io import StringIO

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_test_modules():
    """Get all test modules"""
    unit_tests = [
        'tests.test_campaign_agent',
        'tests.test_db_tool',
        'tests.test_openai_tool',
        'tests.test_campaign_agent_endpoints',
        'tests.test_campaign_endpoints',
        'tests.test_database_models',
        'tests.test_main'
    ]
    
    integration_tests = [
        'tests.test_integration'
    ]
    
    return unit_tests, integration_tests

def run_tests(test_modules, verbosity=1):
    """Run the specified test modules"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load tests from modules
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            suite.addTests(loader.loadTestsFromModule(module))
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
            continue
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)
    
    return result

def run_with_coverage(test_modules, verbosity=1):
    """Run tests with coverage reporting"""
    try:
        import coverage
    except ImportError:
        print("Coverage not available. Install with: pip install coverage")
        return run_tests(test_modules, verbosity)
    
    # Start coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Run tests
    result = run_tests(test_modules, verbosity)
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "="*50)
    print("COVERAGE REPORT")
    print("="*50)
    
    # Generate coverage report
    cov.report(show_missing=True)
    
    # Generate HTML report
    try:
        cov.html_report(directory='htmlcov')
        print(f"\nHTML coverage report generated in: htmlcov/index.html")
    except Exception as e:
        print(f"Could not generate HTML report: {e}")
    
    return result

def print_test_summary(result):
    """Print a summary of test results"""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    print(f"Total tests run: {total_tests}")
    print(f"Successes: {total_tests - failures - errors - skipped}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"- {test}")
        
        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"- {test}")
    
    return result.wasSuccessful()

def check_dependencies():
    """Check if required testing dependencies are available"""
    missing_deps = []
    
    # Check for required packages
    required_packages = [
        ('unittest', 'unittest'),
        ('unittest.mock', 'unittest.mock')
    ]
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_deps.append(package_name)
    
    # Check for optional packages
    optional_packages = [
        ('coverage', 'coverage'),
    ]
    
    for package_name, import_name in optional_packages:
        try:
            __import__(import_name)
        except ImportError:
            print(f"Optional package '{package_name}' not available. Install with: pip install {package_name}")
    
    if missing_deps:
        print(f"Missing required dependencies: {', '.join(missing_deps)}")
        return False
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run tests for Omnicom MVP project')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Get test modules
    unit_tests, integration_tests = get_test_modules()
    
    # Determine which tests to run
    if args.unit:
        test_modules = unit_tests
        print("Running unit tests only...")
    elif args.integration:
        test_modules = integration_tests
        print("Running integration tests only...")
    else:
        test_modules = unit_tests + integration_tests
        print("Running all tests...")
    
    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    print(f"Test modules to run: {len(test_modules)}")
    for module in test_modules:
        print(f"  - {module}")
    print()
    
    # Run tests
    try:
        if args.coverage:
            result = run_with_coverage(test_modules, verbosity)
        else:
            result = run_tests(test_modules, verbosity)
        
        # Print summary
        success = print_test_summary(result)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error running tests: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()