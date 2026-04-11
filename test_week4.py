"""
Code Archaeologist API Test - Week 4
Tests all new Week 4 endpoints
"""

import requests
import sys
import json

BASE_URL = "http://localhost:8001"

def test_endpoint(method, path, **kwargs):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        elif method == "POST":
            data = kwargs.get('json', kwargs.get('data'))
            r = requests.post(url, json=data, timeout=10)
        else:
            return None
        
        if r.status_code == 200:
            return r.json()
        else:
            print(f"❌ {method} {path} - {r.status_code}: {r.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ {method} {path} - Error: {e}")
        return None

def main():
    print("=" * 60)
    print("Code Archaeologist API Test - Week 4")
    print("=" * 60)
    print(f"Testing: {BASE_URL}\n")
    
    session_id = None
    api_key = None
    
    # Test 1: Root
    print("1. Testing root endpoint...")
    result = test_endpoint("GET", "/")
    if result:
        print(f"✅ GET / - 200")
        print(f"   Version: {result.get('version')}")
        print(f"   Features: {result.get('features', [])}")
    
    # Test 2: Health
    print("\n2. Testing health endpoint...")
    result = test_endpoint("GET", "/health")
    if result:
        print(f"✅ GET /health - 200")
        print(f"   Status: {result.get('status')}")
    
    # Test 3: Upload file
    print("\n3. Testing file upload...")
    test_code = """
def process():
    return 42

def main():
    result = process()
    print(result)

if __name__ == "__main__":
    main()
"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            r = requests.post(f"{BASE_URL}/upload", files={"file": f}, timeout=10)
        if r.status_code == 200:
            result = r.json()
            session_id = result.get('session_id')
            print(f"✅ POST /upload - 200")
            print(f"   Session: {session_id}")
            print(f"   Functions: {result.get('functions', [])}")
            print(f"   Events: {result.get('events', 0)}")
        else:
            print(f"❌ POST /upload - {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"❌ POST /upload - Error: {e}")
    
    # Test 4: Causal Discovery
    if session_id:
        print(f"\n4. Testing causal discovery...")
        try:
            r = requests.post(f"{BASE_URL}/causal/discover", params={"session_id": session_id, "min_confidence": 0.2}, timeout=10)
            if r.status_code == 200:
                result = r.json()
                print(f"✅ POST /causal/discover - 200")
                print(f"   Nodes: {len(result.get('nodes', []))}")
                print(f"   Edges: {len(result.get('edges', []))}")
            else:
                print(f"❌ POST /causal/discover - {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"❌ POST /causal/discover - Error: {e}")
    
    # Test 5: What-If Simulator
    if session_id:
        print(f"\n5. Testing what-if simulator...")
        try:
            r = requests.post(f"{BASE_URL}/whatif/simulate", params={"session_id": session_id, "remove_function": "process"}, timeout=10)
            if r.status_code == 200:
                result = r.json()
                print(f"✅ POST /whatif/simulate - 200")
                summary = result.get('summary', {})
                print(f"   Affected: {summary.get('affected_count', 0)}")
                print(f"   Break Prob: {summary.get('total_break_probability', 0)}")
            else:
                print(f"❌ POST /whatif/simulate - {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"❌ POST /whatif/simulate - Error: {e}")
    
    # Test 6: Score Benchmark
    if session_id:
        print(f"\n6. Testing score benchmark...")
        try:
            r = requests.get(f"{BASE_URL}/score/{session_id}", timeout=10)
            if r.status_code == 200:
                result = r.json()
                print(f"✅ GET /score/{session_id} - 200")
                print(f"   Overall Score: {result.get('overall_score')}/100")
                print(f"   Category: {result.get('category')}")
            else:
                print(f"❌ GET /score/{session_id} - {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"❌ GET /score/{session_id} - Error: {e}")
    
    # Test 7: API Key Generation
    print("\n7. Testing API key generation...")
    try:
        r = requests.post(f"{BASE_URL}/apikey/generate", params={"tier": "free"}, timeout=5)
        if r.status_code == 200:
            result = r.json()
            api_key = result.get('api_key')
            print(f"✅ POST /apikey/generate - 200")
            print(f"   Tier: {result.get('tier')}")
            print(f"   Free calls: {result.get('free_calls_remaining')}")
        else:
            print(f"❌ POST /apikey/generate - {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"❌ POST /apikey/generate - Error: {e}")
    
    # Test 8: API Usage
    if api_key:
        print(f"\n8. Testing API usage...")
        try:
            r = requests.get(f"{BASE_URL}/apikey/usage/{api_key}", timeout=5)
            if r.status_code == 200:
                result = r.json()
                print(f"✅ GET /apikey/usage/{api_key[:10]}... - 200")
                print(f"   Total calls: {result.get('total_calls', 0)}")
                print(f"   Total cost: ${result.get('total_cost', 0)}")
            else:
                print(f"❌ GET /apikey/usage/{api_key[:10]}... - {r.status_code}")
        except Exception as e:
            print(f"❌ GET /apikey/usage - Error: {e}")
    
    # Test 9: Trace Format
    print("\n9. Testing trace format endpoint...")
    result = test_endpoint("GET", "/trace/format")
    if result:
        print(f"✅ GET /trace/format - 200")
        print(f"   Version: {result.get('version')}")
        print(f"   Languages: {result.get('supported_languages', [])}")
    
    print("\n" + "=" * 60)
    print("Week 4 Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
