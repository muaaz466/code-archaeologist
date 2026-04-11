#!/usr/bin/env python3
"""
Test script for Code Archaeologist API
Week 3: Automated API testing
"""

import requests
import sys
from pathlib import Path

BASE_URL = "http://localhost:8001"

def test_endpoint(method, path, data=None, files=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        elif method == "POST":
            r = requests.post(url, data=data, files=files, timeout=10)
        elif method == "DELETE":
            r = requests.delete(url, timeout=5)
        else:
            print(f"❌ Unknown method: {method}")
            return False
        
        if r.status_code == 200:
            print(f"✅ {method} {path} - {r.status_code}")
            try:
                return r.json()
            except:
                return r.text
        else:
            print(f"❌ {method} {path} - {r.status_code}: {r.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ {method} {path} - Error: {e}")
        return None

def main():
    print("=" * 60)
    print("Code Archaeologist API Test - Week 3")
    print("=" * 60)
    print(f"Testing: {BASE_URL}")
    print()
    
    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    result = test_endpoint("GET", "/")
    if result:
        print(f"   Response: {result}")
    print()
    
    # Test 2: Health check
    print("2. Testing health endpoint...")
    result = test_endpoint("GET", "/health")
    if result:
        print(f"   Response: {result}")
    print()
    
    # Test 3: Sessions (empty initially)
    print("3. Testing sessions endpoint...")
    result = test_endpoint("GET", "/sessions")
    if result:
        print(f"   Response: {result}")
    print()
    
    # Test 4: API Docs
    print("4. Testing API docs...")
    result = test_endpoint("GET", "/docs")
    if result:
        print(f"   Status: OK (HTML page)")
    print()
    
    # Test 5: Upload file
    print("5. Testing file upload...")
    test_file = Path("frontend/streamlit/test.py")
    if test_file.exists():
        with open(test_file, 'rb') as f:
            result = test_endpoint(
                "POST", "/upload",
                data={"language": "python"},
                files={"file": ("test.py", f, "text/x-python")}
            )
        if result:
            print(f"   Response: {result}")
            session_id = result.get('session_id')
            
            # Test 6: Query with session
            if session_id:
                print()
                print(f"6. Testing query with session {session_id}...")
                try:
                    url = f"{BASE_URL}/query/{session_id}"
                    r = requests.post(
                        url,
                        json={"query_type": "callers", "target": "process"},
                        timeout=5
                    )
                    if r.status_code == 200:
                        print(f"✅ POST /query/{session_id} - {r.status_code}")
                        print(f"   Response: {r.json()}")
                    else:
                        print(f"❌ POST /query/{session_id} - {r.status_code}: {r.text[:100]}")
                except Exception as e:
                    print(f"❌ POST /query/{session_id} - Error: {e}")
    else:
        print(f"   ⚠️ Test file not found: {test_file}")
    print()
    
    # Test 7: AI Explain
    print("7. Testing AI explain...")
    try:
        url = f"{BASE_URL}/explain"
        r = requests.post(
            url, 
            json={  # Use json= for proper JSON body
                "function_name": "process",
                "code_snippet": "def process(): return 1"
            },
            timeout=5
        )
        if r.status_code == 200:
            print(f"✅ POST /explain - {r.status_code}")
            print(f"   Response: {r.json()}")
        else:
            print(f"❌ POST /explain - {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"❌ POST /explain - Error: {e}")
    print()
    
    print("=" * 60)
    print("API Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
