import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import transaction
from django.test import TransactionTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import Document, DocumentChunk
from documents.tasks import process_document_task
from rag.pipeline import RAGPipeline


class DocumentDeletionFocusedTest(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="del_focus",
            email="del_focus@test.com",
            password="Pass123!",
            employee_id="DELF1",
        )

    def _create_doc(self):
        return Document.objects.create(
            title="TmpDoc",
            filename="tmp.pdf",
            uploaded_by=self.user,
            file=SimpleUploadedFile(name="tmp.pdf", content=b"%PDF-1.4 tmp", content_type="application/pdf"),
            file_size=12,
            status="ready",
            page_count=1,
        )

    def test_instance_delete_removes_db_chunks_and_file_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                path = Path(tmp) / doc.file.name
                self.assertTrue(path.exists())
                DocumentChunk.objects.create(
                    document=doc,
                    chunk_index=0,
                    chunk_text="hi",
                    page_number=1,
                    embedding=[0.1] * 3072,
                )
                doc_id = doc.id
                doc.delete()
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertEqual(DocumentChunk.objects.filter(document_id=doc_id).count(), 0)
                self.assertFalse(path.exists())

    def test_queryset_delete_removes_file_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                path = Path(tmp) / doc.file.name
                self.assertTrue(path.exists())
                doc_id = doc.id
                Document.objects.filter(pk=doc_id).delete()
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertFalse(path.exists())

    def test_admin_bulk_queryset_delete_removes_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                first = self._create_doc()
                second = self._create_doc()
                paths = [Path(tmp) / first.file.name, Path(tmp) / second.file.name]
                ids = [first.id, second.id]
                self.assertTrue(all(p.exists() for p in paths))
                Document.objects.filter(pk__in=ids).delete()
                self.assertEqual(Document.objects.filter(pk__in=ids).count(), 0)
                self.assertTrue(all(not p.exists() for p in paths))

    def test_all_queryset_delete_removes_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                first = self._create_doc()
                second = self._create_doc()
                paths = [Path(tmp) / first.file.name, Path(tmp) / second.file.name]
                Document.objects.all().delete()
                self.assertEqual(Document.objects.count(), 0)
                self.assertTrue(all(not p.exists() for p in paths))

    def test_transaction_rollback_preserves_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                path = Path(tmp) / doc.file.name
                self.assertTrue(path.exists())
                doc_id = doc.id
                try:
                    with transaction.atomic():
                        doc.delete()
                        raise RuntimeError("rollback")
                except RuntimeError:
                    pass
                self.assertTrue(Document.objects.filter(pk=doc_id).exists())
                self.assertTrue(path.exists())

    def test_nested_inner_rollback_preserves_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                path = Path(tmp) / doc.file.name
                doc_id = doc.id
                try:
                    with transaction.atomic():
                        with transaction.atomic():
                            doc.delete()
                            raise RuntimeError("inner rollback")
                except RuntimeError:
                    pass
                self.assertTrue(Document.objects.filter(pk=doc_id).exists())
                self.assertTrue(path.exists())

    def test_nested_both_commits_delete_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                path = Path(tmp) / doc.file.name
                doc_id = doc.id
                with transaction.atomic():
                    with transaction.atomic():
                        doc.delete()
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertFalse(path.exists())

    def test_missing_file_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                path = Path(tmp) / doc.file.name
                if path.exists():
                    path.unlink()
                doc_id = doc.id
                doc.delete()
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())

    def test_storage_delete_failure_logs_and_db_still_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                doc_id = doc.id
                storage = doc.file.storage
                orig_exists = storage.exists

                def exists_side(name):
                    return orig_exists(name)

                def del_side(name):
                    raise OSError("disk full")

                with mock.patch.object(storage, "exists", side_effect=exists_side), \
                     mock.patch.object(storage, "delete", side_effect=del_side), \
                     self.assertLogs("documents.models", level="ERROR") as cm:
                    doc.delete()
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertTrue(any("Failed to cleanup document file" in m for m in cm.output))


class DocumentDeletionAPITest(APITestCase):
    def setUp(self):
        self.hr = get_user_model().objects.create_user(
            username="hrdel2",
            email="hrdel2@test.com",
            role="hr_admin",
            password="HrPass123!",
            employee_id="HRDEL2",
        )
        self.emp = get_user_model().objects.create_user(
            username="empdel2",
            email="empdel2@test.com",
            role="employee",
            password="EmpPass123!",
            employee_id="EMPDEL2",
        )

    def test_hr_api_delete_removes_record_and_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = Document.objects.create(
                    title="ApiDel",
                    filename="apid.pdf",
                    uploaded_by=self.hr,
                    file=SimpleUploadedFile(name="apid.pdf", content=b"%PDF-1.4 x", content_type="application/pdf"),
                    file_size=10,
                    status="ready",
                    page_count=1,
                )
                path = Path(tmp) / doc.file.name
                self.assertTrue(path.exists())
                self.client.force_authenticate(user=self.hr)
                with self.captureOnCommitCallbacks(execute=True):
                    r = self.client.delete(f"/api/v1/documents/{doc.id}/")
                self.assertEqual(r.status_code, status.HTTP_200_OK)
                self.assertFalse(Document.objects.filter(pk=doc.id).exists())
                self.assertFalse(path.exists())

    def test_employee_cannot_delete_via_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = Document.objects.create(
                    title="ApiDel2",
                    filename="apid2.pdf",
                    uploaded_by=self.hr,
                    file=SimpleUploadedFile(name="apid2.pdf", content=b"%PDF-1.4 x", content_type="application/pdf"),
                    file_size=10,
                    status="ready",
                    page_count=1,
                )
                path = Path(tmp) / doc.file.name
                self.client.force_authenticate(user=self.emp)
                r = self.client.delete(f"/api/v1/documents/{doc.id}/")
                self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
                self.assertTrue(Document.objects.filter(pk=doc.id).exists())
                self.assertTrue(path.exists())


class DocumentProcessingDeletionTest(TransactionTestCase):
    """Deletion safeguards for in-flight processing (mocked embeddings, no Gemini)."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="proc_del",
            email="proc_del@test.com",
            password="Pass123!",
            employee_id="PROCD",
        )

    def _create_doc(self):
        return Document.objects.create(
            title="ProcDoc",
            filename="proc.pdf",
            uploaded_by=self.user,
            file=SimpleUploadedFile(name="proc.pdf", content=b"%PDF-1.4 tmp", content_type="application/pdf"),
            file_size=12,
            status="started",
            page_count=0,
        )

    def _pipeline(self):
        pipeline = RAGPipeline.__new__(RAGPipeline)
        pipeline.embedding_generator = mock.Mock()
        pipeline.embedding_generator.generate_embedding.return_value = [0.1] * 3072
        pipeline.embedding_generator.close = mock.Mock()
        pipeline.close = mock.Mock()
        pipeline._update_progress = lambda doc_id, **kw: Document.objects.filter(pk=doc_id).update(**kw)
        pipeline.extract_pages = mock.Mock(return_value=(["text"], 1))
        return pipeline

    def test_task_skips_document_deleted_before_processing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                doc_id = doc.id
                doc.delete()
                with mock.patch("rag.pipeline.RAGPipeline") as MockPipeline:
                    process_document_task(doc_id)
                MockPipeline.assert_not_called()
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertEqual(DocumentChunk.objects.filter(document_id=doc_id).count(), 0)

    def test_pipeline_aborts_if_deleted_during_chunking(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                doc_id = doc.id
                pipeline = self._pipeline()

                def build_and_delete(_pages):
                    Document.objects.filter(pk=doc_id).delete()
                    return (
                        [{"index": 0, "text": "new", "page_number": 1, "page_start": 1,
                          "page_end": 1, "char_count": 3, "token_count": 1, "section_heading": ""}],
                        {"total_extracted_characters": 3, "total_extracted_tokens": 1, "tokenizer": "approx"},
                    )

                pipeline.build_document_chunks = mock.Mock(side_effect=build_and_delete)
                result = pipeline.process_document(doc_id)
                self.assertEqual(result.get("status"), "deleted")
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertEqual(DocumentChunk.objects.filter(document_id=doc_id).count(), 0)

    def test_pipeline_aborts_if_deleted_during_embedding(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                doc_id = doc.id
                pipeline = self._pipeline()
                pipeline.build_document_chunks = mock.Mock(return_value=(
                    [{"index": 0, "text": "new", "page_number": 1, "page_start": 1,
                      "page_end": 1, "char_count": 3, "token_count": 1, "section_heading": ""}],
                    {"total_extracted_characters": 3, "total_extracted_tokens": 1, "tokenizer": "approx"},
                ))

                def generate_and_delete(_text):
                    Document.objects.filter(pk=doc_id).delete()
                    return [0.1] * 3072

                pipeline.embedding_generator.generate_embedding.side_effect = generate_and_delete
                result = pipeline.process_document(doc_id)
                self.assertEqual(result.get("status"), "deleted")
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertEqual(DocumentChunk.objects.filter(document_id=doc_id).count(), 0)

    def test_pipeline_aborts_if_deleted_before_final_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = self._create_doc()
                doc_id = doc.id
                pipeline = self._pipeline()
                pipeline.build_document_chunks = mock.Mock(return_value=(
                    [{"index": 0, "text": "new", "page_number": 1, "page_start": 1,
                      "page_end": 1, "char_count": 3, "token_count": 1, "section_heading": ""}],
                    {"total_extracted_characters": 3, "total_extracted_tokens": 1, "tokenizer": "approx"},
                ))

                def update_then_delete(document_id, **kw):
                    Document.objects.filter(pk=document_id).update(**kw)
                    if kw.get("processing_progress") == 90:
                        Document.objects.filter(pk=document_id).delete()

                pipeline._update_progress = update_then_delete
                result = pipeline.process_document(doc_id)
                self.assertEqual(result.get("status"), "deleted")
                self.assertFalse(Document.objects.filter(pk=doc_id).exists())
                self.assertEqual(DocumentChunk.objects.filter(document_id=doc_id).count(), 0)


class OrphanDocumentFileCommandTest(TransactionTestCase):
    def test_dry_run_reports_only_and_apply_deletes_only_upload_dir_orphans(self):
        user = get_user_model().objects.create_user(
            username="orphan_cmd", email="orphan_cmd@test.com",
            password="Pass123!", employee_id="ORPH"
        )
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                doc = Document.objects.create(
                    title="Keep", filename="keep.pdf", uploaded_by=user,
                    file=SimpleUploadedFile(name="keep.pdf", content=b"%PDF-1.4 keep", content_type="application/pdf"),
                    file_size=10, status="ready", page_count=1,
                )
                storage = doc.file.storage
                orphan_name = storage.save("hr_policies/orphan.pdf", ContentFile(b"%PDF-1.4 orphan"))
                outside = Path(tmp) / "outside.pdf"
                outside.write_bytes(b"outside")

                dry_out = StringIO()
                call_command("cleanup_orphan_document_files", stdout=dry_out)
                self.assertIn("DRY-RUN", dry_out.getvalue())
                self.assertTrue(storage.exists(orphan_name))

                apply_out = StringIO()
                call_command("cleanup_orphan_document_files", "--apply", stdout=apply_out)
                self.assertIn("Deleted 1 orphan file", apply_out.getvalue())
                self.assertFalse(storage.exists(orphan_name))
                self.assertTrue(storage.exists(doc.file.name))
                self.assertTrue(outside.exists())
