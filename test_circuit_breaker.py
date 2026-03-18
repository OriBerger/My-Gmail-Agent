#!/usr/bin/env python3
"""
Test script for circuit breaker functionality
"""

import requests
import json
import time

def test_circuit_breaker_status(base_url="https://my-gmail-agent.onrender.com"):
    """Test the circuit breaker status endpoint"""
    
    print("🔍 Testing Circuit Breaker Status...")
    
    try:
        # Test circuit breaker status
        response = requests.get(f"{base_url}/circuit-breaker", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Circuit Breaker Status:")
            print(f"   Max Attempts: {data.get('max_attempts', 'N/A')}")
            print(f"   Reset Time: {data.get('reset_time_seconds', 'N/A')} seconds")
            print(f"   Failed Messages: {data.get('total_failed_messages', 0)}")
            
            if data.get('failed_messages'):
                print("   Failed Message Details:")
                for msg_id, info in data['failed_messages'].items():
                    print(f"     {msg_id}: {info['failed_attempts']} attempts, last: {info['last_attempt_ago']}")
            else:
                print("   No failed messages currently tracked")
                
        else:
            print(f"❌ Failed to get circuit breaker status: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_circuit_breaker_reset(base_url="https://my-gmail-agent.onrender.com"):
    """Test the circuit breaker reset endpoint"""
    
    print("\n🔄 Testing Circuit Breaker Reset...")
    
    try:
        # Test circuit breaker reset
        response = requests.post(f"{base_url}/circuit-breaker/reset", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Circuit Breaker Reset: {data.get('message', 'Success')}")
        else:
            print(f"❌ Failed to reset circuit breaker: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    
    print("🧪 Circuit Breaker Test Script")
    print("=" * 40)
    
    # Test with Render URL
    base_url = "https://my-gmail-agent.onrender.com"
    
    # Test status first
    test_circuit_breaker_status(base_url)
    
    # Ask if user wants to reset
    print("\n" + "=" * 40)
    reset_choice = input("Do you want to reset the circuit breaker? (y/N): ").lower().strip()
    
    if reset_choice == 'y' or reset_choice == 'yes':
        test_circuit_breaker_reset(base_url)
        
        # Check status again after reset
        print("\n" + "=" * 40)
        print("Checking status after reset...")
        test_circuit_breaker_status(base_url)
    else:
        print("Skipping reset.")
    
    print("\n✅ Circuit breaker test completed!")

if __name__ == "__main__":
    main()