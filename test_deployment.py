#!/usr/bin/env python3
"""
Dexter v3 Deployment Test Script
Tests that all components are properly installed and working
"""

import subprocess
import sys
import os
import time
from pathlib import Path

import pytest

pytest.skip("Deployment tests require full environment", allow_module_level=True)

def run_command(cmd, description, timeout=30, capture_output=True):
    """Run a command and return success status"""
    print(f"Testing: {description}...", end=" ")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            success = result.returncode == 0
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout)
            success = result.returncode == 0
        
        if success:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL")
            if capture_output and result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available"""
    print("\n🔍 Testing System Dependencies")
    print("=" * 40)
    
    tests = [
        ("python3 --version", "Python 3.x installation"),
        ("pip3 --version", "pip package manager"),
        ("node --version", "Node.js installation"),
        ("npm --version", "npm package manager"),
    ]
    
    results = []
    for cmd, desc in tests:
        results.append(run_command(cmd, desc))

    assert all(results)

def test_python_packages():
    """Test that Python packages are installed"""
    print("\n📦 Testing Python Dependencies")
    print("=" * 40)
    
    # Map package names to their import names
    packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"), 
        ("pydantic", "pydantic"),
        ("httpx", "httpx"),
        ("aiosqlite", "aiosqlite"),
        ("PyJWT", "jwt"),  # PyJWT imports as 'jwt'
        ("ldap3", "ldap3"),
        ("psutil", "psutil")
    ]
    
    results = []
    for package_name, import_name in packages:
        cmd = f"python3 -c 'import {import_name}'"
        results.append(run_command(cmd, f"Python package: {package_name}"))

    assert all(results)

def test_frontend_setup():
    """Test that frontend is properly set up"""
    print("\n🎨 Testing Frontend Setup")
    print("=" * 40)
    
    results = []

    # Check if package.json exists
    if Path("frontend/package.json").exists():
        print("Testing: package.json exists... ✅ PASS")
        results.append(True)
    else:
        print("Testing: package.json exists... ❌ FAIL")
        results.append(False)

    # Check if node_modules exists (after install)
    if Path("frontend/node_modules").exists():
        print("Testing: node_modules directory... ✅ PASS")
        results.append(True)
    else:
        print("Testing: node_modules directory... ⚠️  NOT INSTALLED (run install.sh)")
        results.append(False)

    assert all(results)

def test_core_functionality():
    """Test core system functionality"""
    print("\n🧠 Testing Core Functionality")
    print("=" * 40)
    
    # Test demo system
    result = run_command("python3 demo_system.py", "Demo system execution", timeout=60)
    assert result

def test_file_structure():
    """Test that all required files are present"""
    print("\n📁 Testing File Structure")
    print("=" * 40)
    
    required_files = [
        "requirements.txt",
        "config.json",
        "install.sh",
        "install.bat", 
        "launch.sh",
        "launch.bat",
        "README_DEPLOY.md",
        "backend/main.py",
        "frontend/package.json",
        "Dockerfile.sandbox",
        "docker-compose.yml"
    ]
    
    results = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"Testing: {file_path}... ✅ PASS")
            results.append(True)
        else:
            print(f"Testing: {file_path}... ❌ MISSING")
            results.append(False)

    assert all(results)

def main():
    """Run all tests"""
    print("🤖 Dexter v3 Deployment Test Suite")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    test_results = []
    
    # Run all test suites
    test_results.append(test_file_structure())
    test_results.append(test_dependencies()) 
    test_results.append(test_python_packages())
    test_results.append(test_frontend_setup())
    test_results.append(test_core_functionality())
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 40)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if all(test_results):
        print("🎉 ALL TESTS PASSED - System is ready!")
        print("\nNext steps:")
        print("1. Run './launch.sh' (Linux/Mac) or 'launch.bat' (Windows)")
        print("2. Open http://localhost:3000 in your browser")
        return 0
    else:
        print("⚠️  Some tests failed - check installation")
        print("\nTroubleshooting:")
        print("1. Run the appropriate installer: './install.sh' or 'install.bat'")
        print("2. Check that Python 3.8+ and Node.js 16+ are installed")
        print("3. Review error messages above")
        return 1

if __name__ == "__main__":
    sys.exit(main())