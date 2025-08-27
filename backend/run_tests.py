#!/usr/bin/env python3
"""
Test runner script for Multi-Agent Development System
"""
import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False


def check_environment():
    """Check if the development environment is properly set up"""
    print("🔍 Checking development environment...")
    
    # Check if we're in the backend directory
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        return False
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found. Run 'make dev-setup' first")
        return False
    
    # Check if requirements are installed
    try:
        import pytest
        import fastapi
        import ollama
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("   Run 'make dev-setup' to install dependencies")
        return False


def run_tests():
    """Run the test suite"""
    print("🧪 Starting test suite...")
    
    # Run tests with coverage
    success = run_command(
        "python -m pytest tests/ -v --cov=app --cov-report=term-missing",
        "Running tests with coverage"
    )
    
    if success:
        print("\n🎉 All tests completed successfully!")
        return True
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        return False


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    print(f"🧪 Running specific test: {test_path}")
    
    success = run_command(
        f"python -m pytest {test_path} -v",
        f"Running test: {test_path}"
    )
    
    return success


def main():
    """Main function"""
    print("🚀 Multi-Agent Development System - Test Runner")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        success = run_specific_test(test_path)
    else:
        success = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
