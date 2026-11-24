import os
import sys

# Add backend directory to path
sys.path.insert(0, "D:/web projects/HR_Policy_Assistant/backend")

os.environ["DJANGO_SETTINGS_MODULE"] = "hrproject.settings"

import django
django.setup()

import accounts
print("accounts imported successfully")
print("Package location:", accounts.__path__)
print("Package file:", accounts.__file__ if hasattr(accounts, '__file__') else 'No __file__')
print("Submodules:")
for item in dir(accounts):
    if not item.startswith('_'):
        print(f"  - {item}")