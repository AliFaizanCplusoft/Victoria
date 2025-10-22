import requests
import time

API_URL = "http://localhost:8000"

def test_health_check():
    print("1. Testing health check...")
    try:
        response = requests.get(f"{API_URL}/health")
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "healthy":
            print(f"✅ Health check passed\n   Response: {data}")
            return True
        else:
            print(f"❌ Health check failed\n   Response: {data}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Health check failed: Could not connect to the API. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{API_URL}/")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Root endpoint working\n   API Version: {data.get('version')}\n   Status: {data.get('status')}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_report_generation():
    print("\n3. Testing report generation...")
    try:
        with open('responses.csv', 'rb') as f:
            files = {'responses_file': ('responses.csv', f, 'text/csv')}
            data = {'person_index': '0'}
            print(f"   Uploading responses.csv...")
            response = requests.post(f"{API_URL}/api/v1/generate-report", files=files, data=data, timeout=120)
        
        response.raise_for_status()
        print(f"✅ Report generation successful!")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   Content-Length: {len(response.content)} bytes")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Report generation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred during report generation: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Victoria Assessment API locally...")
    print("=" * 50)
    
    # Give the API a moment to start up
    time.sleep(3)
    
    all_passed = True
    if not test_health_check():
        all_passed = False
    if not test_root_endpoint():
        all_passed = False
    if not test_report_generation():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Local API testing completed successfully!")
    else:
        print("❌ Local API testing completed with failures.")

