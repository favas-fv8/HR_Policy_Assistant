import sys, os
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
from django.db import connection

cursor = connection.cursor()
# Check django_migrations table structure
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'django_migrations' ORDER BY ordinal_position")
print('django_migrations columns:')
for r in cursor.fetchall():
    print('  ', r[0])

# Get all migration names
cursor.execute("SELECT * FROM django_migrations ORDER BY id")
print('\nAll migrations:')
for r in cursor.fetchall():
    print('  ', r)