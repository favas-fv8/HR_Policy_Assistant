import sys, os
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE']='hrproject.settings'
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT migration_name FROM django_migrations WHERE app = 'documents' ORDER BY id")
rows = cursor.fetchall()
print('Documents migrations:')
for r in rows:
    print(f'  {r[0]}')
print()
print('Applied migrations:')
cursor.execute("SELECT name FROM django_migrations WHERE app = 'documents' ORDER BY id")
applied = [r[0] for r in cursor.fetchall()]
for r in rows:
    status = 'APPLIED' if r[0] in applied else 'PENDING'
    print(f'  {r[0]}: {status}')
" 2>&1 | head -20