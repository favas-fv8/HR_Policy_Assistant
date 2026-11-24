import sys
import os
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'

import django
django.setup()

from django.core.management import call_command
from io import StringIO

# Backup to stdout (we'll redirect to file)
backup = StringIO()
try:
    call_command('dumpdata', stdout=backup, indent=2)
    backup_text = backup.getvalue()
    print("=== DJANGA DATA BACKUP ===")
    print(f"Backup length: {len(backup_text)} characters")
    print("\n=== FIRST 500 CHARS ===")
    print(backup_text[:500])
    print("\n=== SUCCESS ===")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()