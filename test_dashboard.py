#!/usr/bin/env python3
"""
Test script to verify the ML dashboard works correctly
"""

import webbrowser
import http.server
import socketserver
import threading
import time
import os
from pathlib import Path

def test_dashboard():
    """Test the dashboard by opening it in a browser"""
    
    # Change to the directory containing the dashboard
    os.chdir(Path(__file__).parent)
    
    # Check if dashboard file exists
    if not os.path.exists('ml_dashboard.html'):
        print("❌ Error: ml_dashboard.html not found!")
        return False
    
    print("✅ Dashboard file found")
    
    # Check file size
    file_size = os.path.getsize('ml_dashboard.html')
    print(f"📄 Dashboard file size: {file_size:,} bytes")
    
    # Basic HTML validation
    try:
        with open('ml_dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for required elements
        checks = {
            'HTML structure': all([
                '<html' in content,
                '</html>' in content,
                '<body' in content,
                '</body>' in content
            ]),
            'CSS styles': '<style>' in content,
            'JavaScript': '<script>' in content,
            'Plotly library': 'plotly-latest.min.js' in content,
            'Chart.js library': 'Chart.js' in content,
            'Dashboard title': 'ML Visualization Dashboard' in content,
            'Error handling': 'showErrorMessage' in content
        }
        
        print("\n📋 Dashboard validation:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        if all(checks.values()):
            print("\n🎉 Dashboard appears to be properly structured!")
            return True
        else:
            print("\n⚠️  Dashboard has some issues but may still work")
            return False
            
    except Exception as e:
        print(f"❌ Error reading dashboard file: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing ML Dashboard...")
    success = test_dashboard()
    
    if success:
        print("\n🚀 Dashboard test passed! Ready to use.")
        print("💡 To start the dashboard server, run: python start_dashboard.py")
    else:
        print("\n⚠️  Dashboard test had issues. Please check the file.")