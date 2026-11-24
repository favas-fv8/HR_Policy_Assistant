"""Tests for HR Policy Assistant - Documents app."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import documents.models as doc_models
Document = doc_models.Document
DocumentChunk = doc_models.DocumentChunk


class DocumentModelTest(TestCase):
    """Test Document model."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            employee_id='EMP100'
        )

    def test_document_creation(self):
        """Test document model creation."""
        uploaded_file = SimpleUploadedFile(name='test_policy.pdf', content=b'PDF content')
        document = Document.objects.create(
            title='Test Policy',
            filename='test_policy.pdf',
            uploaded_by=self.user,
            file=uploaded_file,
            file_size=1024,
            status='ready',
            page_count=5
        )
        self.assertEqual(document.title, 'Test Policy')
        self.assertEqual(document.page_count, 5)
        self.assertEqual(document.uploaded_by, self.user)
        self.assertEqual(document.status, 'ready')

    def test_document_str(self):
        """Test document string representation."""
        uploaded_file = SimpleUploadedFile(name='test_policy.pdf', content=b'PDF content')
        document = Document.objects.create(
            title='Test Policy',
            filename='test_policy.pdf',
            uploaded_by=self.user,
            file=uploaded_file,
            file_size=1024,
            status='ready',
            page_count=1
        )
        expected = f"Test Policy ({document.uploaded_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(document), expected)


class DocumentChunkTest(TestCase):
    """Test DocumentChunk model."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            employee_id='EMP101'
        )
        uploaded_file = SimpleUploadedFile(name='test_policy.pdf', content=b'PDF content')
        self.document = Document.objects.create(
            title='Test Policy',
            filename='test_policy.pdf',
            uploaded_by=self.user,
            file=uploaded_file,
            file_size=1024,
            status='ready',
            page_count=5
        )

    def test_chunk_creation(self):
        """Test document chunk creation."""
        chunk = DocumentChunk.objects.create(
            document=self.document,
            chunk_index=0,
            chunk_text="This is test HR policy text about vacation policy.",
            page_number=1,
            embedding=[0.1] * 3072
        )
        self.assertEqual(chunk.document.title, 'Test Policy')
        self.assertEqual(chunk.chunk_index, 0)
        self.assertEqual(chunk.page_number, 1)
        self.assertEqual(len(chunk.embedding), 3072)

    def test_chunk_str(self):
        """Test chunk string representation."""
        chunk = DocumentChunk.objects.create(
            document=self.document,
            chunk_index=0,
            chunk_text="Test text.",
            page_number=1,
            embedding=[0.1] * 3072
        )
        expected = f"Chunk 0 of Test Policy (p.1)"
        self.assertEqual(str(chunk), expected)
from rest_framework.test import APITestCase
from rest_framework import status


class DocumentFileAccessAPITest(APITestCase):
    def setUp(self):
        self.hr = get_user_model().objects.create_user(
            username="hr_file", email="hrf@test.com", role="hr_admin", password="HrPass123!", employee_id="HRF1"
        )
        self.emp = get_user_model().objects.create_user(
            username="emp_file", email="empf@test.com", role="employee", password="EmpPass123!", employee_id="EMPF1"
        )
        self.doc = Document.objects.create(
            title="Policy PDF",
            filename="policy.pdf",
            uploaded_by=self.hr,
            file=SimpleUploadedFile(name="policy.pdf", content=b"%PDF-1.4 test pdf", content_type="application/pdf"),
            file_size=17,
            status="ready",
            page_count=1,
        )

    def test_authenticated_user_can_get_pdf_file(self):
        self.client.force_authenticate(user=self.emp)
        r = self.client.get(f"/api/v1/documents/{self.doc.id}/file/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("application/pdf", r.get("Content-Type", ""))
        self.assertIn("inline", r.get("Content-Disposition", ""))

    def test_unauthenticated_cannot_get_pdf_file(self):
        r = self.client.get(f"/api/v1/documents/{self.doc.id}/file/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_invalid_document_id_returns_404(self):
        self.client.force_authenticate(user=self.emp)
        r = self.client.get("/api/v1/documents/999999/file/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
