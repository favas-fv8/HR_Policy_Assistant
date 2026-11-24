import os, sys
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
from django.db import connection

# Try to create the vector extension
with connection.cursor() as cursor:
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("SUCCESS: pgvector extension created!")
    except Exception as e:
        print(f"ERROR creating extension: {e}")