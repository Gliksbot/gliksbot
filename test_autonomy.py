#!/usr/bin/env python3
"""
Simple test script to verify autonomy manager changes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dexter_brain.autonomy import AutonomyManager

# Create a minimal autonomy manager for testing
class MockConfig:
    pass

class MockCollaboration:
    pass

class MockSkills:
    pass

class MockSandbox:
    pass

def test_autonomy_detection():
    """Test the updated autonomy detection logic"""
    
    # Create mock objects
    config = MockConfig()
    collaboration_mgr = MockCollaboration()
    skills_mgr = MockSkills()
    sandbox_factory = MockSandbox()
    
    # Create autonomy manager
    autonomy = AutonomyManager(config, collaboration_mgr, skills_mgr, sandbox_factory)
    
    # Test cases
    test_cases = [
        ("write me a poem and save it to my desktop", True),  # Should trigger
        ("create a file for me", True),  # Should trigger
        ("help me with something", True),  # Should trigger
        ("get me some data from the internet", True),  # Should trigger
        ("hello", False),  # Should NOT trigger
        ("thanks", False),  # Should NOT trigger
        ("how are you", False),  # Should NOT trigger
        ("make me a calculator", True),  # Should trigger
        ("I need a script", True),  # Should trigger
    ]
    
    print("Testing autonomy detection logic:")
    print("=" * 50)
    
    for test_input, expected in test_cases:
        needs_skill, missing_params = autonomy.detect_intent_and_missing_params(test_input, [])
        result = "✓ PASS" if (needs_skill == expected) else "✗ FAIL"
        print(f"{result} '{test_input}' -> trigger={needs_skill}, missing={missing_params}")
    
    print("\nTesting clarification requirements:")
    print("=" * 50)
    
    # Test that we get minimal clarifications
    _, missing = autonomy.detect_intent_and_missing_params("write me a poem and save it to my desktop", [])
    print(f"Poem request missing params: {missing} (should be empty or minimal)")
    
    _, missing = autonomy.detect_intent_and_missing_params("help", [])
    print(f"Vague 'help' missing params: {missing} (should ask for specifics)")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_autonomy_detection()
