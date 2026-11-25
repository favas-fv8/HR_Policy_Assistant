from django.test import TestCase
from chat.utils import generate_chat_title

class ChatTitleGenerationTests(TestCase):
    def test_examples(self):
        cases = {
            'What is the leave policy?': 'Leave Policy',
            'What skills does this candidate have?': 'Candidate Skills',
            'Explain maternity leave eligibility': 'Maternity Leave Eligibility',
            'Summarize this HR policy document': 'HR Policy Document',
            'How many years of experience does this candidate have?': 'Candidate Experience',
        }
        for msg, expected in cases.items():
            self.assertEqual(generate_chat_title(msg), expected)

    def test_fallback(self):
        self.assertEqual(generate_chat_title('   '), 'New Chat')
        self.assertEqual(generate_chat_title('hello!!!'), 'New Chat')
