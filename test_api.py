import os, sys
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
from django.test.client import Client

# Test the backend API endpoints
client = Client()

# 1. Test token obtain
print("=" * 60)
print("TEST 1: Obtain auth token")
print("=" * 60)
import json
resp = client.post('/api/v1/auth/token/', {'username': 'test', 'password': 'test'})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.content[:200]}")

# 2. Test documents list (requires auth)
print("\n" + "=" * 60)
print("TEST 2: Documents list (unauthenticated)")
print("=" * 60)
resp = client.get('/api/v1/documents/')
print(f"Status: {resp.status_code}")

# 3. Test chat conversations (requires auth)
print("\n" + "=" * 60)
print("TEST 3: Chat conversations (unauthenticated)")
print("=" * 60)
resp = client.get('/api/v1/chat/conversations/')
print(f"Status: {resp.status_code}")

# 4. Test rag ask (requires auth)
print("\n" + "=" * 60)
print("TEST 4: RAG ask (unauthenticated)")
print("=" * 60)
resp = client.post('/api/v1/rag/ask/', {'question': 'test'})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.content[:200]}")

print("\n" + "=" * 60)
print("All basic API connectivity tests complete")
print("=" * 60)