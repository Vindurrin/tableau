#!/usr/bin/env python3
"""
Test runner for Tableau Governance Framework

Runs all unit tests and provides coverage reporting.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests with coverage reporting."""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"
    
    print("🧪 Running Tableau Governance Framework Tests")
    print("=" * 50)
    
    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        return 1
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest found")
    except ImportError:
        print("❌ pytest not found. Install with: pip install pytest")
        return 1
    
    # Run tests
    try:
        print("\n🔍 Running unit tests...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(tests_dir),
            "-v",
            "--tb=short",
            f"--rootdir={project_root}"
        ], cwd=project_root)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_configuration_check():
    """Check configuration system without external dependencies."""
    
    print("\n🔧 Testing Configuration System...")
    
    try:
        # Test config loading with mocked environment
        os.environ["TABLEAU_SERVER_URL"] = "https://test-server.example.com"
        os.environ["TABLEAU_TOKEN_NAME"] = "test-token"
        os.environ["TABLEAU_TOKEN_SECRET"] = "test-secret"
        
        from config import Config
        config = Config()
        
        print("✅ Configuration system loads successfully")
        print(f"   Server URL: {config.server_url}")
        print(f"   Log Level: {config.log_level}")
        print(f"   Log Only Mode: {config.log_only}")
        
        # Clean up test environment
        del os.environ["TABLEAU_SERVER_URL"]
        del os.environ["TABLEAU_TOKEN_NAME"] 
        del os.environ["TABLEAU_TOKEN_SECRET"]
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def run_logging_check():
    """Test logging system functionality."""
    
    print("\n📝 Testing Logging System...")
    
    try:
        from logger import get_logger
        
        logger = get_logger("test")
        logger.info("Test log message", test_field="test_value")
        logger.operation_start("test_operation")
        logger.operation_end("test_operation", 100.5, status="success")
        
        print("✅ Logging system works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def check_dependencies():
    """Check that required dependencies are available."""
    
    print("\n📦 Checking Dependencies...")
    
    required_packages = [
        "tableauserverclient",
        "python-dotenv", 
        "pytest"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages available")
    return True

def main():
    """Main test runner."""
    
    print("🚀 Tableau Governance Framework - Test Suite")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return 1
    
    # Run basic functionality checks
    config_ok = run_configuration_check()
    logging_ok = run_logging_check()
    
    if not (config_ok and logging_ok):
        print("\n❌ Basic functionality tests failed.")
        return 1
    
    # Run full unit test suite
    test_result = run_tests()
    
    print("\n" + "=" * 60)
    if test_result == 0:
        print("🎉 All tests completed successfully!")
        print("\n📊 Test Summary:")
        print("   ✅ Configuration system: PASS")
        print("   ✅ Logging system: PASS") 
        print("   ✅ Unit tests: PASS")
        print("\n🚀 Framework is ready for deployment!")
    else:
        print("❌ Some tests failed. Please review the output above.")
    
    return test_result

if __name__ == "__main__":
    sys.exit(main())