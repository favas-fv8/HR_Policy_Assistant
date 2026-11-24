"""Tests for the HR Policy Assistant chat API."""

from unittest import mock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser
from chat.models import Conversation, Message


class ChatSendMessageTests(APITestCase):
    """Chat send message endpoint behavior."""

    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='emp_chat',
            email='emp_chat@test.com',
            role='employee',
            password='TestPass123!',
            employee_id='EMPCHAT',
        )
        self.hr_admin = CustomUser.objects.create_user(
            username='hr_chat',
            email='hr_chat@test.com',
            role='hr_admin',
            password='TestPass123!',
            employee_id='HRCHAT',
        )
        self.conversation = Conversation.objects.create(
            title='Test Conv',
            employee=self.employee,
        )

    def test_send_message_success(self):
        self.client.force_authenticate(user=self.employee)
        with mock.patch('rag.pipeline.RAGPipeline') as MockPipeline:
            MockPipeline.return_value.answer_question.return_value = {
                'answer': 'The answer.',
                'sources': [],
                'references': [],
            }
            response = self.client.post(
                f'/api/v1/chat/conversations/{self.conversation.id}/send/',
                {'content': 'What is the vacation policy?'},
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'assistant')
        self.assertEqual(response.data['content'], 'The answer.')

    def test_send_message_requires_content(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(
            f'/api/v1/chat/conversations/{self.conversation.id}/send/',
            {'content': '   '},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChatHistoryIsolationTests(APITestCase):
    """Message history is only visible to owner or HR admin."""

    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='emp_iso',
            email='emp_iso@test.com',
            role='employee',
            password='TestPass123!',
            employee_id='EMPISO',
        )
        self.hr_admin = CustomUser.objects.create_user(
            username='hr_iso',
            email='hr_iso@test.com',
            role='hr_admin',
            password='TestPass123!',
            employee_id='HRISO',
        )
        self.conversation = Conversation.objects.create(
            title='Iso Conv',
            employee=self.employee,
        )

    def test_employee_cannot_read_others_conversation_messages(self):
        other = CustomUser.objects.create_user(
            username='emp_iso2',
            email='emp_iso2@test.com',
            role='employee',
            password='TestPass123!',
            employee_id='EMPISO2',
        )
        self.client.force_authenticate(user=other)
        response = self.client.get(
            f'/api/v1/chat/conversations/{self.conversation.id}/messages/',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hr_admin_can_read_any_conversation_messages(self):
        self.client.force_authenticate(user=self.hr_admin)
        response = self.client.get(
            f'/api/v1/chat/conversations/{self.conversation.id}/messages/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
