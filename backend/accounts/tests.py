"""Tests for HR Policy Assistant - Accounts app."""

from django.test import TestCase
from django.contrib.auth import get_user_model, authenticate
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser


class CustomUserModelTest(TestCase):
    """Test CustomUser model with role-based access."""

    def test_create_hr_admin(self):
        """HR Admin user can be created."""
        user = CustomUser.objects.create_user(
            username='hr_admin',
            email='hr@test.com',
            role='hr_admin',
            password='testpass123',
            employee_id='HR001'
        )
        self.assertEqual(user.role, 'hr_admin')
        self.assertTrue(user.is_hr_admin)
        self.assertFalse(user.is_employee)

    def test_create_employee(self):
        """Employee user can be created."""
        user = CustomUser.objects.create_user(
            username='employee',
            email='emp@test.com',
            role='employee',
            password='testpass123',
            employee_id='EMP001'
        )
        self.assertEqual(user.role, 'employee')
        self.assertFalse(user.is_hr_admin)
        self.assertTrue(user.is_employee)

    def test_default_role_is_employee(self):
        """Default role should be employee."""
        user = CustomUser.objects.create_user(
            username='default_user',
            email='default@test.com',
            password='testpass123',
            employee_id='EMP003'
        )
        self.assertEqual(user.role, 'employee')


class UserPermissionTest(TestCase):
    """Test user permission enforcement."""

    def setUp(self):
        self.hr_user = CustomUser.objects.create_user(
            username='test_hr',
            email='hr@test.com',
            role='hr_admin',
            password='testpass123',
            employee_id='HR002'
        )
        self.emp_user = CustomUser.objects.create_user(
            username='test_emp',
            email='emp@test.com',
            role='employee',
            password='testpass123',
            employee_id='EMP002'
        )

    def test_hr_is_hr_admin(self):
        """HR user has is_hr_admin=True."""
        self.assertTrue(self.hr_user.is_hr_admin)

    def test_emp_is_not_hr_admin(self):
        """Employee user has is_hr_admin=False."""
        self.assertFalse(self.emp_user.is_hr_admin)


class PasswordChangeAPITest(APITestCase):
    """Password change flow via dj_rest_auth password change endpoint."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='pw_user',
            email='pw@test.com',
            role='employee',
            password='OldPass123!',
            employee_id='EMPPW',
        )

    def test_change_own_password_success(self):
        """Correct current password allows changing to a new one."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/v1/auth/password/change/',
            {
                'old_password': 'OldPass123!',
                'new_password1': 'NewPass123!',
                'new_password2': 'NewPass123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.user.check_password('OldPass123!'))
        self.assertTrue(self.user.check_password('NewPass123!'))
        self.assertIsNone(authenticate(username='pw_user', password='OldPass123!'))
        self.assertIsNotNone(authenticate(username='pw_user', password='NewPass123!'))

    def test_change_password_wrong_current_password_rejected(self):
        """Wrong current password is rejected."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/v1/auth/password/change/',
            {
                'old_password': 'WrongOld123!',
                'new_password1': 'NewPass123!',
                'new_password2': 'NewPass123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch_rejected(self):
        """New password and confirmation mismatch is rejected."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/v1/auth/password/change/',
            {
                'old_password': 'OldPass123!',
                'new_password1': 'NewPass123!',
                'new_password2': 'Different123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmployeeCreateAPITest(APITestCase):
    """HR Admin employee creation flow."""

    def setUp(self):
        self.hr = CustomUser.objects.create_user(
            username='hr_admin',
            email='hr@test.com',
            role='hr_admin',
            password='HrPass123!',
            employee_id='HR001',
        )

    def test_hr_admin_can_create_employee(self):
        """HR Admin can create an employee account; username is generated from employee_id."""
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'emp001',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'password': 'Emp@12345',
                'confirm_password': 'Emp@12345',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'employee')
        self.assertEqual(response.data['employee_id'], 'emp001')
        self.assertEqual(response.data['username'], 'emp001')
        user = CustomUser.objects.get(username='emp001')
        self.assertEqual(user.employee_id, 'emp001')
        self.assertEqual(user.username, 'emp001')
        self.assertTrue(user.check_password('Emp@12345'))
        self.assertNotEqual(user.password, 'Emp@12345')

    def test_duplicate_employee_id_rejected(self):
        """Duplicate Employee ID/User ID is rejected."""
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'HR001',
                'email': 'dup@test.com',
                'password': 'NewPass123!',
                'confirm_password': 'NewPass123!',
                'full_name': 'Dup User',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('employee_id', response.data)

    def test_duplicate_username_rejected(self):
        """Duplicate generated username is rejected."""
        CustomUser.objects.create_user(
            username='EMP002', email='x@test.com', role='employee', password='Pass123!x', employee_id='E002'
        )
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'EMP002',
                'email': 'dup2@test.com',
                'password': 'NewPass123!',
                'confirm_password': 'NewPass123!',
                'full_name': 'Dup User',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('employee_id', response.data)

    def test_weak_password_rejected(self):
        """Weak passwords are rejected by Django password validators."""
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'EMPWEAK',
                'email': 'weak@test.com',
                'password': '123',
                'confirm_password': '123',
                'full_name': 'Weak Emp',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_password_mismatch_rejected(self):
        """Password and confirmation mismatch is rejected."""
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'EMPMISM',
                'email': 'mism@test.com',
                'password': 'NewPass123!',
                'confirm_password': 'OtherPass123!',
                'full_name': 'Mism Emp',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    def test_employee_cannot_create_user(self):
        """Employees cannot create accounts."""
        emp = CustomUser.objects.create_user(
            username='emp_cant',
            email='empc@test.com',
            role='employee',
            password='EmpPass123!',
            employee_id='EMPCANT',
        )
        self.client.force_authenticate(user=emp)
        response = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'EMPEVIL',
                'email': 'evil@test.com',
                'password': 'EvilPass123!',
                'confirm_password': 'EvilPass123!',
                'full_name': 'Evil Emp',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_cannot_create_hr_admin(self):
        """Client-supplied hr_admin role must not create HR Admin."""
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'EMPNOTADMIN',
                'email': 'na@test.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!',
                'full_name': 'Not Admin',
                'role': 'hr_admin',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'employee')
        user = CustomUser.objects.get(employee_id='EMPNOTADMIN')
        self.assertFalse(user.is_hr_admin)

    def test_employee_can_login_with_exact_employee_id(self):
        """Employee logs in using exact Employee ID/User ID and exact password."""
        self.client.force_authenticate(user=self.hr)
        create = self.client.post(
            '/api/v1/accounts/users/',
            {
                'employee_id': 'emp001',
                'email': 'login@test.com',
                'password': 'Emp@12345',
                'confirm_password': 'Emp@12345',
                'full_name': 'Login Emp',
            },
            format='json',
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(user=None)
        login = self.client.post('/api/v1/auth/login/', {'username': 'emp001', 'password': 'Emp@12345'}, format='json')
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn('key', login.data)

    def test_login_fails_with_wrong_employee_id_casing(self):
        self.client.force_authenticate(user=self.hr)
        self.client.post('/api/v1/accounts/users/', {
            'employee_id': 'emp001', 'email': 'casing@test.com',
            'password': 'Emp@12345', 'confirm_password': 'Emp@12345', 'full_name': 'Case Emp',
        }, format='json')
        self.client.force_authenticate(user=None)
        login = self.client.post('/api/v1/auth/login/', {'username': 'EMP001', 'password': 'Emp@12345'}, format='json')
        self.assertEqual(login.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_fails_with_wrong_password_casing(self):
        self.client.force_authenticate(user=self.hr)
        self.client.post('/api/v1/accounts/users/', {
            'employee_id': 'emp001', 'email': 'pcase@test.com',
            'password': 'Emp@12345', 'confirm_password': 'Emp@12345', 'full_name': 'Pwd Case',
        }, format='json')
        self.client.force_authenticate(user=None)
        for bad_pwd in ['emp@12345', 'EMP@12345']:
            login = self.client.post('/api/v1/auth/login/', {'username': 'emp001', 'password': bad_pwd}, format='json')
            self.assertEqual(login.status_code, status.HTTP_400_BAD_REQUEST)

    def test_uppercase_employee_id_preserved(self):
        self.client.force_authenticate(user=self.hr)
        response = self.client.post('/api/v1/accounts/users/', {
            'employee_id': 'EMP002', 'email': 'upper@test.com',
            'password': 'SecurePass123!', 'confirm_password': 'SecurePass123!', 'full_name': 'Upper Emp',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['employee_id'], 'EMP002')
        self.assertEqual(response.data['username'], 'EMP002')
        user = CustomUser.objects.get(username='EMP002')
        self.assertEqual(user.employee_id, 'EMP002')
        self.client.force_authenticate(user=None)
        ok = self.client.post('/api/v1/auth/login/', {'username': 'EMP002', 'password': 'SecurePass123!'}, format='json')
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        bad = self.client.post('/api/v1/auth/login/', {'username': 'emp002', 'password': 'SecurePass123!'}, format='json')
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)


class EmployeeStatusAPITest(APITestCase):
    """HR Admin deactivate / reactivate employee accounts."""

    def setUp(self):
        self.hr = CustomUser.objects.create_user(
            username='hr_admin2',
            email='hr2@test.com',
            role='hr_admin',
            password='HrPass123!',
            employee_id='HR003',
        )
        self.emp = CustomUser.objects.create_user(
            username='emp_stat',
            email='emps@test.com',
            role='employee',
            password='EmpPass123!',
            employee_id='EMPSTAT',
        )

    def test_hr_admin_can_deactivate_employee(self):
        """HR Admin can deactivate an employee."""
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            f'/api/v1/accounts/users/{self.emp.pk}/deactivate/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.emp.refresh_from_db()
        self.assertFalse(self.emp.is_active)

    def test_hr_admin_can_reactivate_employee(self):
        """HR Admin can reactivate a deactivated employee."""
        self.emp.is_active = False
        self.emp.save(update_fields=['is_active'])
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(
            f'/api/v1/accounts/users/{self.emp.pk}/reactivate/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.emp.refresh_from_db()
        self.assertTrue(self.emp.is_active)

    def test_employee_cannot_deactivate(self):
        """Employees cannot deactivate accounts."""
        self.client.force_authenticate(user=self.emp)
        response = self.client.post(
            f'/api/v1/accounts/users/{self.hr.pk}/deactivate/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
