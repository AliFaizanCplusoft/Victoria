#!/usr/bin/env python3
"""
Test script for Victoria Assessment API running in Docker
"""

import requests
import time
import os

def test_docker_api():
    """Test the Victoria Assessment API running in Docker"""
    
    base_url = "http://localhost:8000"
    
    print("🐳 Testing Victoria Assessment API in Docker...")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint working")
            data = response.json()
            print(f"   API Version: {data.get('version', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test 3: API Documentation
    print("\n3. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print(f"❌ API documentation failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API documentation failed: {e}")
    
    # Test 4: Report Generation (if responses.csv exists)
    print("\n4. Testing report generation...")
    if os.path.exists("responses.csv"):
        try:
            with open("responses.csv", "rb") as f:
                files = {"responses_file": ("responses.csv", f, "text/csv")}
                data = {"person_index": 0}
                
                print("   Uploading responses.csv...")
                response = requests.post(
                    f"{base_url}/api/v1/generate-report",
                    files=files,
                    data=data,
                    timeout=60  # Longer timeout for report generation
                )
                
                if response.status_code == 200:
                    print("✅ Report generation successful!")
                    print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
                    print(f"   Content-Length: {len(response.content)} bytes")
                    
                    # Save the report
                    with open("victoria_report_docker.html", "wb") as out_file:
                        out_file.write(response.content)
                    print("   Report saved as: victoria_report_docker.html")
                else:
                    print(f"❌ Report generation failed: {response.status_code}")
                    print(f"   Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Report generation failed: {e}")
    else:
        print("⚠️  responses.csv not found, skipping report generation test")
    
    print("\n" + "=" * 50)
    print("🎉 Docker API testing completed!")
    print("\nNext steps:")
    print("- View API docs: http://localhost:8000/docs")
    print("- Test with curl: curl http://localhost:8000/health")
    print("- Generate report: Use the /api/v1/generate-report endpoint")

if __name__ == "__main__":
    test_docker_api()

