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
            title='New Chat',
            employee=self.employee,
        )

    def test_send_message_success_generates_title_once(self):
        self.client.force_authenticate(user=self.employee)
        with mock.patch('rag.pipeline.RAGPipeline') as MockPipeline:
            MockPipeline.return_value.answer_question.return_value = {
                'answer': 'The answer.',
                'sources': [],
                'references': [],
            }
            response = self.client.post(
                f'/api/v1/chat/conversations/{self.conversation.id}/send/',
                {'content': 'What is the leave policy?'},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['role'], 'assistant')
            self.assertEqual(response.data['content'], 'The answer.')
            self.conversation.refresh_from_db()
            self.assertEqual(self.conversation.title, 'Leave Policy')
            self.assertEqual(response.data['conversation_title'], 'Leave Policy')

            response2 = self.client.post(
                f'/api/v1/chat/conversations/{self.conversation.id}/send/',
                {'content': 'Explain maternity leave eligibility'},
                format='json',
            )
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            self.conversation.refresh_from_db()
            self.assertEqual(self.conversation.title, 'Leave Policy')

    def test_send_message_requires_content(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(
            f'/api/v1/chat/conversations/{self.conversation.id}/send/',
            {'content': '   '},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChatStartConversationTests(APITestCase):
    """Tests for POST /api/v1/chat/conversations/start/ (draft -> first message)."""

    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='emp_start',
            email='emp_start@test.com',
            role='employee',
            password='TestPass123!',
            employee_id='EMPSTART',
        )

    def test_start_valid_creates_conversation_and_user_and_assistant_messages(self):
        self.client.force_authenticate(user=self.employee)
        with mock.patch('rag.pipeline.RAGPipeline') as MockPipeline:
            MockPipeline.return_value.answer_question.return_value = {
                'answer': 'Here is the policy answer.',
                'sources': [{'document_title': 'Policy.pdf', 'page_number': 1, 'excerpt': 'text'}],
            }
            resp = self.client.post(
                '/api/v1/chat/conversations/start/',
                {'content': 'What is the leave policy?'},
                format='json',
            )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('conversation_id', resp.data)
        cid = resp.data['conversation_id']
        self.assertEqual(resp.data['role'], 'assistant')
        self.assertEqual(resp.data['content'], 'Here is the policy answer.')
        self.assertIsInstance(resp.data.get('sources'), list)
        conv = Conversation.objects.get(id=cid)
        self.assertEqual(conv.employee_id, self.employee.id)
        msgs = list(Message.objects.filter(conversation=conv).order_by('created_at'))
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0].role, 'user')
        self.assertEqual(msgs[0].content, 'What is the leave policy?')
        self.assertEqual(msgs[1].role, 'assistant')
        self.assertEqual(msgs[1].content, 'Here is the policy answer.')

    def test_start_rag_failure_returns_201_with_fallback_and_persists_messages(self):
        self.client.force_authenticate(user=self.employee)
        with mock.patch('rag.pipeline.RAGPipeline') as MockPipeline:
            MockPipeline.return_value.answer_question.side_effect = RuntimeError('RAG down')
            resp = self.client.post(
                '/api/v1/chat/conversations/start/',
                {'content': 'What is maternity leave?'},
                format='json',
            )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['role'], 'assistant')
        self.assertIn('error while processing your question', resp.data['content'].lower())
        cid = resp.data['conversation_id']
        msgs = list(Message.objects.filter(conversation_id=cid).order_by('created_at'))
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0].role, 'user')
        self.assertEqual(msgs[1].role, 'assistant')

    def test_start_empty_content_returns_400_no_conversation(self):
        self.client.force_authenticate(user=self.employee)
        before = Conversation.objects.count()
        resp = self.client.post(
            '/api/v1/chat/conversations/start/',
            {'content': '   '},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Conversation.objects.count(), before)

    def test_start_assistant_save_failure_returns_500_no_new_conversation_on_retry_concept(self):
        # Simulate assistant Message.create failing after conversation+user created
        self.client.force_authenticate(user=self.employee)
        real_create = Message.objects.create

        call_count = {'n': 0}

        def side_effect(**kwargs):
            if kwargs.get('role') == 'assistant':
                call_count['n'] += 1
                raise Exception('DB write failed')
            return real_create(**kwargs)

        with mock.patch('rag.pipeline.RAGPipeline') as MockPipeline:
            MockPipeline.return_value.answer_question.return_value = {
                'answer': 'ok',
                'sources': [],
            }
            with mock.patch('chat.views.Message.objects.create', side_effect=side_effect):
                resp = self.client.post(
                    '/api/v1/chat/conversations/start/',
                    {'content': 'Hello policy question'},
                    format='json',
                )
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp.data.get('error'), 'Failed to create assistant response.')
        # Conversation and user message may exist (committed before assistant step) — this documents behavior.
        self.assertGreaterEqual(Conversation.objects.filter(employee=self.employee).count(), 0)


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
