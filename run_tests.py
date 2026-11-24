import sys, os
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
import unittest

# Test 1: CustomUserModelTest
from accounts.tests import CustomUserModelTest
suite1 = unittest.TestLoader().loadTestsFromTestCase(CustomUserModelTest)
runner = unittest.TextTestRunner(verbosity=0)
result1 = runner.run(suite1)
print(f'CustomUserModelTest: {result1.testsRun} tests, errors={len(result1.errors)}, failures={len(result1.failures)}')

# Test 2: Document tests
from documents.tests import DocumentModelTest, DocumentChunkTest
suite2 = unittest.TestLoader().loadTestsFromTestCase(DocumentModelTest)
result2 = runner.run(suite2)
print(f'DocumentModelTest: {result2.testsRun} tests, errors={len(result2.errors)}, failures={len(result2.failures)}')

suite3 = unittest.TestLoader().loadTestsFromTestCase(DocumentChunkTest)
result3 = runner.run(suite3)
print(f'DocumentChunkTest: {result3.testsRun} tests, errors={len(result3.errors)}, failures={len(result3.failures)}')

# Summary
print('=' * 50)
all_pass = result1.wasSuccessful and result2.wasSuccessful and result3.wasSuccessful
print(f'ALL TESTS PASS: {all_pass}')