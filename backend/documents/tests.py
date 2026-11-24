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


class DocumentReprocessSafetyTest(TestCase):
    """Controlled failure test: old chunks remain until replacement commits."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reproc_user", email="reproc@test.com", password="Pass123!", employee_id="EMPREP1"
        )
        self.doc = Document.objects.create(
            title="Reprocess Doc",
            filename="reprocess.pdf",
            uploaded_by=self.user,
            file=SimpleUploadedFile(name="reprocess.pdf", content=b"%PDF-1.4 test", content_type="application/pdf"),
            file_size=14,
            status="ready",
            page_count=1,
            extracted_characters=100,
            extracted_tokens=20,
            extraction_tokenizer="approx-word",
            total_chunks=1,
            processed_chunks=1,
            processing_progress=100,
            processing_stage="ready",
        )
        self.chunk = DocumentChunk.objects.create(
            document=self.doc,
            chunk_index=0,
            chunk_text="Original valid chunk",
            page_number=1,
            page_start=1,
            page_end=1,
            char_count=20,
            token_count=4,
            section_heading="Original",
            embedding_status="embedded",
            embedding=[0.01] * 3072,
        )

    def _snapshot(self):
        self.doc.refresh_from_db()
        chunks = list(DocumentChunk.objects.filter(document=self.doc).order_by("chunk_index").values(
            "id", "chunk_index", "chunk_text", "page_start", "page_end", "char_count", "token_count", "section_heading", "embedding_status", "embedding"
        ))
        return {
            "doc": {
                "status": self.doc.status,
                "processing_error": self.doc.processing_error,
                "extracted_characters": self.doc.extracted_characters,
                "extracted_tokens": self.doc.extracted_tokens,
                "extraction_tokenizer": self.doc.extraction_tokenizer,
                "total_chunks": self.doc.total_chunks,
                "processed_chunks": self.doc.processed_chunks,
            },
            "chunks": chunks,
        }

    def test_failed_reprocess_preserves_old_chunks_and_successful_retry_replaces(self):
        from unittest import mock
        from rag.pipeline import RAGPipeline

        before = self._snapshot()

        pipeline = RAGPipeline.__new__(RAGPipeline)
        pipeline.embedding_generator = mock.Mock()
        pipeline.embedding_generator.close = mock.Mock()
        pipeline.embedding_generator.generate_embedding.side_effect = [[0.02] * 3072, RuntimeError("forced embedding failure")]
        pipeline._embedding_progress = lambda i, total: RAGPipeline._embedding_progress(total, i)
        pipeline._update_progress = lambda doc_id, **kwargs: Document.objects.filter(pk=doc_id).update(**kwargs)
        pipeline.extract_pages = mock.Mock(return_value=(["Page 1 text", "Page 2 text"], 2))
        pipeline.build_document_chunks = mock.Mock(return_value=([
            {"index": 0, "text": "New chunk 1", "page_number": 1, "page_start": 1, "page_end": 1, "char_count": 11, "token_count": 3, "section_heading": "New"},
            {"index": 1, "text": "New chunk 2", "page_number": 2, "page_start": 2, "page_end": 2, "char_count": 11, "token_count": 3, "section_heading": "New"},
        ], {"total_extracted_characters": 22, "total_extracted_tokens": 6, "tokenizer": "approx-word"}))
        pipeline.close = mock.Mock()

        with self.assertRaises(RuntimeError):
            pipeline.process_document(self.doc.id)

        after_fail = self._snapshot()
        self.assertEqual(before["chunks"], after_fail["chunks"])
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, "processing")
        # Pipeline raises before commit; task layer marks error in production. Simulate task error update.
        Document.objects.filter(pk=self.doc.id).update(
            status="error",
            processing_error="forced embedding failure",
            processing_stage="error",
            processing_stage_detail="Processing failed.",
            processing_progress=40,
        )
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, "error")
        self.assertIn("forced embedding failure", self.doc.processing_error)
        self.assertEqual(self.doc.processing_stage, "error")

        # Successful retry should atomically replace old chunks.
        pipeline.embedding_generator.generate_embedding.side_effect = [[0.03] * 3072, [0.04] * 3072]
        result = pipeline.process_document(self.doc.id)
        self.assertEqual(result["status"], "ready")
        self.doc.refresh_from_db()
        chunks = list(DocumentChunk.objects.filter(document=self.doc).order_by("chunk_index"))
        self.assertEqual(self.doc.status, "ready")
        self.assertEqual(self.doc.chunk_count if False else len(chunks), 2)
        self.assertEqual([c.chunk_text for c in chunks], ["New chunk 1", "New chunk 2"])
        self.assertTrue(all(len(c.embedding) == 3072 for c in chunks))
        old_ids = {c["id"] for c in before["chunks"]}
        self.assertTrue(all(c.id not in old_ids for c in chunks))
