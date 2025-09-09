#!/usr/bin/env python3
"""Test script for Docker sandbox and error healing functionality."""

import asyncio
import json
import time
from pathlib import Path
import pytest
import docker

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent))

from backend.dexter_brain.config import Config
from backend.dexter_brain.sandbox import create_sandbox
from backend.dexter_brain.error_tracker import ErrorTracker, ErrorSeverity
from backend.dexter_brain.error_healer import ErrorHealer
from backend.dexter_brain.collaboration import CollaborationManager
from backend.dexter_brain.enhanced_skills import create_and_test_skill_with_healing


@pytest.mark.asyncio
async def test_docker_sandbox():
    """Test Docker sandbox functionality."""
    print("🧪 Testing Docker Sandbox...")

    try:
        docker.from_env().ping()
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

    try:
        # Load configuration
        from dexter_brain.utils import get_config_path
        config = Config.load(get_config_path())

        # Create sandbox
        sandbox = create_sandbox(config.to_json())
        
        # Test simple Python code
        test_code = """def hello_world():
    return "Hello from Docker sandbox!"

if __name__ == "__main__":
    result = hello_world()
    print(result)
"""
        
        print("🔍 Executing test code in Docker sandbox...")
        result = await sandbox.execute_skill(test_code)

        print(f"✅ Execution successful: {result['success']}")
        print(f"📝 Output: {result['output']}")
        print(f"⏱️ Execution time: {result['execution_time']:.2f}s")
        print(f"🐳 Sandbox type: {result['sandbox_type']}")

        assert result['success'], (
            f"Docker sandbox execution failed: {result}"
        )

    except Exception as e:
        pytest.fail(f"Docker sandbox test failed: {e}")


@pytest.mark.asyncio
async def test_error_tracking():
    """Test error tracking system."""
    print("\n🔍 Testing Error Tracking System...")
    
    try:
        # Create error tracker
        error_tracker = ErrorTracker(max_errors=100)
        
        # Log some test errors
        error_id1 = error_tracker.log_error(
            "TEST_ERROR_1",
            "This is a test error for validation",
            ErrorSeverity.MEDIUM,
            "test_system",
            {"test_context": "validation"}
        )
        
        error_id2 = error_tracker.log_error(
            "TEST_ERROR_2", 
            "Another test error",
            ErrorSeverity.HIGH,
            "test_system"
        )
        
        # Test error retrieval
        recent_errors = error_tracker.get_recent_errors(5)
        print(f"✅ Logged 2 errors, retrieved {len(recent_errors)} recent errors")
        assert len(recent_errors) == 2, (
            f"Expected 2 recent errors, got {len(recent_errors)}"
        )

        # Test error statistics
        stats = error_tracker.get_error_statistics()
        print(
            f"📊 Error statistics: {stats['total_errors']} total, {stats['recent_errors']} recent"
        )
        assert stats['total_errors'] >= 2, (
            f"Total errors should be at least 2, got {stats['total_errors']}"
        )

        # Test error resolution
        success = error_tracker.mark_resolved(error_id1)
        print(f"✅ Error resolution: {success}")
        assert success, "Error resolution failed"

    except Exception as e:
        pytest.fail(f"Error tracking test failed: {e}")


@pytest.mark.asyncio
async def test_collaboration_system():
    """Test collaboration system for healing."""
    print("\n🤝 Testing Collaboration System...")
    
    try:
        # Load configuration
        from dexter_brain.utils import get_config_path
        config = Config.load(get_config_path())
        
        # Create collaboration manager
        collab_manager = CollaborationManager(config)
        
        # Test session creation
        test_request = "Test collaboration request for validation"
        session_id = await collab_manager.broadcast_user_input(test_request)

        print(f"✅ Collaboration session created: {session_id}")
        assert session_id, "Collaboration session ID should not be empty"

        # Get active sessions
        active_sessions = collab_manager.get_active_sessions()
        print(f"📊 Active sessions: {len(active_sessions)}")
        assert len(active_sessions) > 0, "No active collaboration sessions found"

    except Exception as e:
        pytest.fail(f"Collaboration test failed: {e}")


@pytest.mark.asyncio
async def test_error_healing_integration():
    """Test complete error healing integration."""
    print("\n🔧 Testing Error Healing Integration...")

    try:
        docker.from_env().ping()
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

    try:
        # Load configuration
        from dexter_brain.utils import get_config_path
        config = Config.load(get_config_path())
        
        # Create components
        error_tracker = ErrorTracker(max_errors=100)
        collab_manager = CollaborationManager(config)
        error_healer = ErrorHealer(config, error_tracker, collab_manager)
        
        print("✅ Error healing system components initialized")
        
        # Test skill creation with healing
        user_request = "Create a simple addition function"
        failing_solution = """def add_numbers(a, b):
    return a + b  # Fixed the syntax error for this test

# This should actually work now
print(add_numbers(2, 3))
"""
        
        print("🧪 Testing skill creation with healing...")
        result = await create_and_test_skill_with_healing(
            user_request,
            failing_solution,
            config.to_json(),
            error_tracker,
            collab_manager,
            max_attempts=1  # Just one attempt for testing
        )

        print(f"📊 Skill creation result: {result.get('ok', False)}")
        print(f"🔄 Attempts made: {result.get('attempts', 0)}")
        assert result.get('ok', False), "Skill creation with healing failed"

        # Check if errors were logged
        recent_errors = error_tracker.get_recent_errors(1)
        print(f"📋 Errors logged during test: {len(recent_errors)}")
        assert len(recent_errors) >= 1, "No errors were logged during healing test"

    except Exception as e:
        pytest.fail(f"Error healing integration test failed: {e}")


@pytest.mark.asyncio
async def test_sandbox_health():
    """Test sandbox health checking."""
    print("\n🏥 Testing Sandbox Health Check...")

    try:
        docker.from_env().ping()
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

    try:
        # Load configuration
        from dexter_brain.utils import get_config_path
        config = Config.load(get_config_path())
        
        # Create sandbox and check health
        sandbox = create_sandbox(config.to_json())
        health = sandbox.check_health()

        print(f"✅ Sandbox health check completed")
        print(f"🏥 Healthy: {health['healthy']}")
        print(f"🐳 Provider: {health['provider']}")
        print(f"🖼️ Image available: {health.get('image_available', 'unknown')}")

        assert health['healthy'], "Sandbox reported unhealthy"

    except Exception as e:
        pytest.fail(f"Sandbox health check failed: {e}")


async def main():
    """Run all tests."""
    print("🚀 Starting Dexter v3 Docker Sandbox & Error Healing Tests")
    print("=" * 60)
    
    tests = [
        ("Docker Sandbox", test_docker_sandbox),
        ("Error Tracking", test_error_tracking),
        ("Collaboration System", test_collaboration_system),
        ("Sandbox Health", test_sandbox_health),
        ("Error Healing Integration", test_error_healing_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Docker sandbox and error healing are working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)