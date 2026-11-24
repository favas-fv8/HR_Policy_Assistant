import sys, os
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT migration_name FROM django_migrations WHERE app = 'documents' ORDER BY applied_timestamp")
print('Documents migrations:')
for r in cursor.fetchall():
    print('  ', r[0])