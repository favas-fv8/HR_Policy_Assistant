"""Tests for vector similarity retrieval."""

from django.test import SimpleTestCase
from vector.similarity import cosine_similarity, retrieve_top_chunks


class VectorSimilarityTests(SimpleTestCase):
    """Tests for the Python cosine similarity fallback."""

    def test_cosine_similarity_identical_vectors(self):
        v = [0.1, 0.2, 0.3, 0.4]
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0, places=5)

    def test_cosine_similarity_empty(self):
        self.assertEqual(cosine_similarity([], [0.1, 0.2]), 0.0)

    def test_cosine_similarity_dimension_mismatch(self):
        with self.assertRaises(ValueError):
            cosine_similarity([0.1, 0.2], [0.1, 0.2, 0.3])

    def test_retrieve_top_chunks_filters_by_threshold(self):
        embeddings = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ]
        metadata = [
            {'document_id': 1, 'chunk_index': 0, 'page_number': 1, 'chunk_text': 'first'},
            {'document_id': 2, 'chunk_index': 0, 'page_number': 2, 'chunk_text': 'second'},
        ]
        results = retrieve_top_chunks(
            query_embedding=[0.9, 0, 0, 0],
            chunk_embeddings=embeddings,
            chunk_metadata=metadata,
            similarity_threshold=0.5,
            retrieval_limit=5,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['chunk_index'], 0)

    def test_retrieve_top_chunks_no_matches(self):
        embeddings = [[1, 0, 0, 0]]
        metadata = [{'document_id': 1, 'chunk_index': 0, 'page_number': 1, 'chunk_text': 'low'}]
        results = retrieve_top_chunks(
            query_embedding=[0, 0, 0, 1],
            chunk_embeddings=embeddings,
            chunk_metadata=metadata,
            similarity_threshold=0.5,
            retrieval_limit=5,
        )
        self.assertEqual(results, [])
