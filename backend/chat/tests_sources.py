"""Tests for historical chat source serialization after document deletion."""
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from chat.models import Conversation, Message
from documents.models import Document


class DeletedSourceSerializationTest(APITestCase):
    def setUp(self):
        self.employee = get_user_model().objects.create_user(
            username="src_del",
            email="src_del@test.com",
            role="employee",
            password="Pass123!",
            employee_id="SRCDEL",
        )

    def test_deleted_source_marked_unavailable_valid_source_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                deleted_doc = Document.objects.create(
                    title="Deleted Policy",
                    filename="deleted.pdf",
                    uploaded_by=self.employee,
                    file=SimpleUploadedFile(name="deleted.pdf", content=b"%PDF-1.4 d", content_type="application/pdf"),
                    file_size=10, status="ready", page_count=1,
                )
                valid_doc = Document.objects.create(
                    title="Valid Policy",
                    filename="valid.pdf",
                    uploaded_by=self.employee,
                    file=SimpleUploadedFile(name="valid.pdf", content=b"%PDF-1.4 v", content_type="application/pdf"),
                    file_size=10, status="ready", page_count=1,
                )
                conversation = Conversation.objects.create(title="C", employee=self.employee)
                Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content="answer",
                    sources=[
                        {
                            "document_id": deleted_doc.id,
                            "document_title": "Deleted Policy",
                            "page_number": 7,
                            "excerpt": "secret excerpt",
                        },
                        {
                            "document_id": valid_doc.id,
                            "document_title": "Valid Policy",
                            "page_number": 2,
                            "excerpt": "kept excerpt",
                        },
                    ],
                )
                deleted_doc.delete()
                self.client.force_authenticate(user=self.employee)
                response = self.client.get(f"/api/v1/chat/conversations/{conversation.id}/messages/")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                sources = response.data[0]["sources"]
                self.assertEqual(len(sources), 2)

                deleted = next(s for s in sources if s["document_title"] == "Deleted Policy")
                self.assertTrue(deleted["document_deleted"])
                self.assertIsNone(deleted["document_id"])
                self.assertIsNone(deleted["page_number"])
                self.assertEqual(deleted["excerpt"], "")

                valid = next(s for s in sources if s["document_title"] == "Valid Policy")
                self.assertFalse(valid["document_deleted"])
                self.assertEqual(valid["document_id"], valid_doc.id)
                self.assertEqual(valid["page_number"], 2)
                self.assertEqual(valid["excerpt"], "kept excerpt")
