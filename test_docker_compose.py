#!/usr/bin/env python3
"""
Test docker-compose.yml configuration for potential issues
"""

import yaml
import os

def test_docker_compose_config():
    """Test docker-compose.yml for common configuration issues"""
    print("DOCKER-COMPOSE CONFIGURATION TEST")
    print("=" * 40)
    
    if not os.path.exists('docker-compose.yml'):
        print("ERROR: docker-compose.yml not found")
        return False
    
    try:
        with open('docker-compose.yml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("SUCCESS: docker-compose.yml is valid YAML")
        
        # Check service configuration
        services = config.get('services', {})
        gmail_service = services.get('gmail-agent', {})
        
        # Check volumes configuration
        volumes = gmail_service.get('volumes', [])
        
        token_mount = None
        credentials_mount = None
        
        for volume in volumes:
            if 'token.json' in volume:
                token_mount = volume
            elif 'credentials.json' in volume:
                credentials_mount = volume
        
        print(f"Token mount: {token_mount}")
        print(f"Credentials mount: {credentials_mount}")
        
        # Check if token.json is writable
        if token_mount and ':ro' in token_mount:
            print("ERROR: token.json is mounted as read-only (:ro)")
            print("This will prevent credential refresh from working!")
            return False
        elif token_mount:
            print("SUCCESS: token.json is writable (no :ro flag)")
        else:
            print("INFO: token.json mount not found")
        
        # Check if credentials.json is read-only (good for security)
        if credentials_mount and ':ro' in credentials_mount:
            print("SUCCESS: credentials.json is read-only (good for security)")
        elif credentials_mount:
            print("INFO: credentials.json is writable (consider making read-only)")
        else:
            print("INFO: credentials.json mount not found")
        
        # Check environment variables
        env_vars = gmail_service.get('environment', [])
        env_file = gmail_service.get('env_file', [])
        
        if env_file:
            print(f"SUCCESS: Environment file configured: {env_file}")
        else:
            print("INFO: No env_file configured")
        
        # Check healthcheck
        healthcheck = gmail_service.get('healthcheck', {})
        if healthcheck:
            test_cmd = healthcheck.get('test', [])
            if 'curl' in str(test_cmd):
                print("SUCCESS: Healthcheck uses curl (should be installed in Dockerfile)")
            else:
                print("INFO: Healthcheck doesn't use curl")
        else:
            print("INFO: No healthcheck configured")
        
        print("\nSUCCESS: docker-compose.yml configuration looks good!")
        return True
        
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in docker-compose.yml: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to analyze docker-compose.yml: {e}")
        return False

def test_volume_permissions():
    """Test if volume files exist and have correct permissions"""
    print("\nVOLUME FILES CHECK")
    print("=" * 20)
    
    files_to_check = {
        'token.json': 'OAuth tokens (should be writable)',
        'credentials.json': 'Google API credentials (can be read-only)',
        '.env': 'Environment variables (not mounted, good)'
    }
    
    for file, description in files_to_check.items():
        if os.path.exists(file):
            try:
                # Test read access
                with open(file, 'r') as f:
                    content = f.read()
                print(f"SUCCESS: {file} - {description} - readable")
                
                # Test write access for token.json
                if file == 'token.json':
                    try:
                        with open(file, 'a') as f:
                            pass  # Just test if we can open for writing
                        print(f"SUCCESS: {file} is writable (good for credential refresh)")
                    except PermissionError:
                        print(f"WARNING: {file} is not writable (credential refresh will fail)")
                        
            except Exception as e:
                print(f"ERROR: Cannot read {file}: {e}")
        else:
            print(f"INFO: {file} not found (normal for fresh setup)")

if __name__ == '__main__':
    config_ok = test_docker_compose_config()
    test_volume_permissions()
    
    if config_ok:
        print("\nSUCCESS: Docker Compose configuration is ready for deployment!")
    else:
        print("\nWARNING: Please fix Docker Compose configuration issues.")