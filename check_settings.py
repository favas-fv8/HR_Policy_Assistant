import os, sys
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
from django.conf import settings
print('DATABASES:', settings.DATABASES)
print("\nEnv vars check:")
print("POSTGRES_HOST:", os.getenv('POSTGRES_HOST', 'localhost'))
print("POSTGRES_PORT:", os.getenv('POSTGRES_PORT', '5432'))