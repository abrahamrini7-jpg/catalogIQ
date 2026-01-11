#!/usr/bin/env python3
"""
Test WordPress REST API connectivity
"""

import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

WORDPRESS_URL = os.getenv("WORDPRESS_URL", "").rstrip("/")
WORDPRESS_USER = os.getenv("WORDPRESS_USER", "")
WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD", "")

print(f"🔍 Testing WordPress API...")
print(f"   URL: {WORDPRESS_URL}")
print(f"   User: {WORDPRESS_USER}")

if not WORDPRESS_URL or not WORDPRESS_USER or not WORDPRESS_PASSWORD:
    print("\n❌ Missing WordPress credentials in .env")
    print("   Required:")
    print("   WORDPRESS_URL=https://your-site.com")
    print("   WORDPRESS_USER=username")
    print("   WORDPRESS_PASSWORD=application_password")
    exit(1)

# Test basic API access
try:
    print("\n1️⃣  Testing basic API access...")
    response = requests.get(f"{WORDPRESS_URL}/wp-json/", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ API is accessible")
    else:
        print(f"   ⚠️  Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test authenticated access
try:
    print("\n2️⃣  Testing authenticated API access...")
    auth_string = base64.b64encode(f"{WORDPRESS_USER}:{WORDPRESS_PASSWORD}".encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_string}',
        'User-Agent': 'CatalogiQ/1.0'
    }
    
    response = requests.get(
        f"{WORDPRESS_URL}/wp-json/wp/v2/users/me",
        headers=headers,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"   ✅ Authenticated as: {user_data.get('name')}")
    else:
        print(f"   ❌ Authentication failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n⚠️  If you get 406 errors:")
print("   1. Contact your hosting provider")
print("   2. Ask them to whitelist /wp-json/wp/v2/media in Mod_Security")
print("   3. Or disable Mod_Security for REST API")
