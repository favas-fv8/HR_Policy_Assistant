import sys, os
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cursor.fetchall()
    print('Tables:')
    for t in tables:
        print(f"  {t[0]}")
print("\nBackup file exists:", os.path.exists(r'D:\web projects\HR_Policy_Assistant\db_backup.json'))
print("Backup file size:", os.path.getsize(r'D:\web projects\HR_Policy_Assistant\db_backup.json'), "bytes")