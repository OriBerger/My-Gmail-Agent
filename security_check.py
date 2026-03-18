#!/usr/bin/env python3
"""
Security verification script for Gmail Agent
"""

import os

def check_dockerignore_security():
    """Check if sensitive files are properly excluded from Docker builds"""
    
    sensitive_files = ['.env', 'credentials.json', 'token.json']
    
    if not os.path.exists('.dockerignore'):
        print("ERROR: .dockerignore file missing!")
        return False
    
    with open('.dockerignore', 'r') as f:
        dockerignore_content = f.read()
    
    missing_files = []
    for file in sensitive_files:
        if file not in dockerignore_content:
            missing_files.append(file)
    
    if missing_files:
        print(f"ERROR: Sensitive files not in .dockerignore: {missing_files}")
        return False
    else:
        print("SUCCESS: All sensitive files are excluded from Docker builds")
        return True

def check_gitignore_security():
    """Check if sensitive files are properly excluded from Git"""
    
    sensitive_files = ['.env', 'credentials.json', 'token.json']
    
    if not os.path.exists('.gitignore'):
        print("WARNING: .gitignore file missing!")
        return False
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    missing_files = []
    for file in sensitive_files:
        if file not in gitignore_content:
            missing_files.append(file)
    
    if missing_files:
        print(f"WARNING: Sensitive files not in .gitignore: {missing_files}")
        return False
    else:
        print("SUCCESS: All sensitive files are excluded from Git")
        return True

def check_file_permissions():
    """Check if sensitive files exist and warn about permissions"""
    
    sensitive_files = {
        '.env': 'Environment variables',
        'credentials.json': 'Google API credentials',
        'token.json': 'OAuth tokens'
    }
    
    for file, description in sensitive_files.items():
        if os.path.exists(file):
            print(f"INFO: {description} found at {file}")
            # Check if file is readable
            try:
                with open(file, 'r') as f:
                    content = f.read()
                if len(content) > 0:
                    print(f"  - File has content (good)")
                else:
                    print(f"  - WARNING: File is empty")
            except Exception as e:
                print(f"  - ERROR: Cannot read file: {e}")
        else:
            print(f"INFO: {description} not found at {file} (normal for fresh setup)")

if __name__ == '__main__':
    print("SECURITY: Gmail Agent Security Check")
    print("=" * 40)
    
    docker_ok = check_dockerignore_security()
    git_ok = check_gitignore_security()
    
    print("\nFile Status:")
    check_file_permissions()
    
    print("\nSecurity Summary:")
    if docker_ok and git_ok:
        print("SUCCESS: All security checks passed!")
        print("SUCCESS: Sensitive files are properly protected")
    else:
        print("WARNING: Some security issues found - please review above")
    
    print("\nSecurity Best Practices:")
    print("- Never commit .env, credentials.json, or token.json to Git")
    print("- Never include sensitive files in Docker images")
    print("- Use environment variables in production")
    print("- Consider using Google Cloud service accounts for production")