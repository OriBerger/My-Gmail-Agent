#!/usr/bin/env python3
"""
Test webhook functionality - works on any platform
"""

import requests
import json

def test_webhook():
    """Test the webhook endpoint"""
    
    webhook_url = "https://my-gmail-agent.onrender.com/webhook/gmail"
    
    # Test data that simulates a Pub/Sub message
    test_data = {
        "message": {
            "data": "eyJ0ZXN0IjoidGVzdCJ9",  # Base64 encoded '{"test":"test"}'
            "messageId": "test123"
        }
    }
    
    print(f"Testing webhook at: {webhook_url}")
    print("Sending test data...")
    
    try:
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Webhook responded correctly!")
            try:
                response_json = response.json()
                print(f"Response: {json.dumps(response_json, indent=2)}")
            except:
                print(f"Response text: {response.text}")
        else:
            print(f"WARNING: Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to webhook: {e}")
        print("\nPossible issues:")
        print("1. Check if your Render app is deployed and running")
        print("2. Verify the URL is correct")
        print("3. Check if the app has any startup errors in Render logs")

def test_health_endpoint():
    """Test the health check endpoint"""
    
    health_url = "https://my-gmail-agent.onrender.com/"
    
    print(f"\nTesting health endpoint at: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("SUCCESS: Health check passed!")
            try:
                health_data = response.json()
                print(f"Health data: {json.dumps(health_data, indent=2)}")
            except:
                print(f"Health response: {response.text}")
        else:
            print(f"WARNING: Health check failed with status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Health check failed: {e}")

if __name__ == '__main__':
    print("WEBHOOK TESTING SCRIPT")
    print("=" * 30)
    
    # Test health endpoint first
    test_health_endpoint()
    
    print("\n" + "=" * 30)
    
    # Test webhook endpoint
    test_webhook()
    
    print("\n" + "=" * 30)
    print("Testing complete!")