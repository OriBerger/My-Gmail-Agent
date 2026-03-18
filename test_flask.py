#!/usr/bin/env python3
"""
Simple test to verify Flask app imports and basic functionality
"""

try:
    from app import app
    print("SUCCESS: Flask app imported successfully!")
    
    # Test the app in test mode
    with app.test_client() as client:
        response = client.get('/')
        print(f"SUCCESS: Health check endpoint: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        if response.status_code == 200:
            print("SUCCESS: Flask app is working correctly!")
        else:
            print("ERROR: Flask app health check failed")
            
except Exception as e:
    print(f"ERROR: Error testing Flask app: {e}")
    import traceback
    traceback.print_exc()