#!/usr/bin/env python3
"""
Test script for Dexter's autonomous skill generation
"""
import requests
import json

def test_dexter_autonomous():
    base_url = "http://127.0.0.1:8080"
    
    # Test 1: Authentication
    print("🔐 Testing authentication...")
    auth_response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "Jeff", "password": "S3rv3r123"}
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.text}")
        return
    
    auth_data = auth_response.json()
    print(f"Auth response: {auth_data}")
    
    if "token" not in auth_data:
        print(f"❌ No token in response: {auth_data}")
        return
        
    token = auth_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Test 2: Test autonomous skill generation for various requests
    test_requests = [
        "create a simple calculator and save it to my desktop",
        "write me a poem about robots",
        "make a file that lists all the files in my downloads folder",
        "help me with a script that counts words in a text file"
    ]
    
    for i, test_message in enumerate(test_requests, 1):
        print(f"\n🤖 Test {i}: '{test_message}'")
        
        chat_response = requests.post(
            f"{base_url}/chat",
            json={"message": test_message},
            headers=headers
        )
        
        if chat_response.status_code != 200:
            print(f"❌ Chat request failed: {chat_response.text}")
            continue
            
        response_data = chat_response.json()
        print(f"📝 Full response: {response_data}")
        print(f"📝 Dexter's reply: {response_data.get('reply', 'No reply')[:100]}...")
        
        # Check if autonomous action was triggered
        if 'executed' in response_data and response_data['executed']:
            print("🚀 ✅ Autonomous skill generation TRIGGERED!")
            executed = response_data['executed']
            print(f"   - Skill created: {executed.get('success', False)}")
            print(f"   - File saved: {executed.get('file_path', 'N/A')}")
        else:
            print("⏳ No autonomous action yet (may be asking clarifying questions)")
    
    print("\n🎯 Testing complete!")

if __name__ == "__main__":
    test_dexter_autonomous()
