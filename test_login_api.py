#!/usr/bin/env python3

import requests
import json

# Test the login API
API_URL = "https://rxnorm-portal-nscs.onrender.com/users/login"

def test_login():
    """Test the login API for ayushi"""
    
    login_data = {
        "username": "ayushi@turmerik.ai",
        "password": "ayushi"
    }
    
    print(f"🔍 Testing login API: {API_URL}")
    print(f"📋 Login data: {login_data}")
    
    try:
        response = requests.post(API_URL, json=login_data, headers={
            'Content-Type': 'application/json'
        })
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful!")
            print(f"📋 Full response: {json.dumps(data, indent=2)}")
            
            # Check if assigned_folder is in the response
            user_data = data.get('user', {})
            assigned_folder = user_data.get('assigned_folder')
            assignment_order = user_data.get('assignment_order')
            
            print(f"\n🎯 Key fields:")
            print(f"   assigned_folder: {assigned_folder}")
            print(f"   assignment_order: {assignment_order}")
            
            if assigned_folder is None:
                print("❌ ISSUE: assigned_folder is missing from API response!")
            else:
                print(f"✅ assigned_folder is correctly returned: {assigned_folder}")
                
        else:
            print(f"❌ Login failed!")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login()