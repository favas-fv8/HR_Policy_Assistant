import math


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec_a: First vector as list of floats
        vec_b: Second vector as list of floats
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    if not vec_a or not vec_b:
        return 0.0
    
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same dimension")
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    
    # Calculate magnitudes
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))
    
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    return dot_product / (magnitude_a * magnitude_b)


def hamming_distance(vec_a: list, vec_b: list) -> int:
    """Calculate Hamming distance between two binary vectors."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same length")
    return sum(el_a != el_b for el_a, el_b in zip(vec_a, vec_b))


def filter_by_threshold(similarities: list, threshold: float) -> list:
    """
    Filter similarity results by threshold.
    
    Args:
        similarities: List of (score, index) tuples
        threshold: Minimum similarity score (0-1)
        
    Returns:
        Filtered list of (score, index) tuples above threshold
    """
    return [(score, idx) for score, idx in similarities if score >= threshold]


def sort_by_similarity(similarities: list, descending: bool = True) -> list:
    """
    Sort similarity results by score.
    
    Args:
        similarities: List of (score, index) tuples
        descending: Sort in descending order (highest first)
        
    Returns:
        Sorted list
    """
    return sorted(similarities, key=lambda x: x[0], reverse=descending)


def calculate_cosine_distance(vec_a: list, vec_b: list) -> float:
    """
    Calculate cosine DISTANCE between two vectors.
    Cosine distance = 1 - cosine_similarity, ranges from 0 to 2.
    
    When pgvector is available, this can be computed as:
    - Python: 1 - cosine_similarity(vec_a, vec_b)
    - PostgreSQL: 1 - (embedding <=> query_embedding)
    
    Args:
        vec_a: First vector as list of floats
        vec_b: Second vector as list of floats
        
    Returns:
        Cosine distance value
    """
    similarity = cosine_similarity(vec_a, vec_b)
    return 1.0 - similarity


def retrieve_top_chunks(
    query_embedding: list,
    chunk_embeddings: list,
    chunk_metadata: list,
    similarity_threshold: float = 0.7,
    retrieval_limit: int = 5,
    use_pgvector: bool = False,
    pg_connection=None,
):
    """
    Retrieve the most relevant document chunks based on cosine similarity.
    
    Args:
        query_embedding: Embedding of the query vector (3072 dimensions)
        chunk_embeddings: List of stored chunk embeddings (3072 dimensions each)
        chunk_metadata: List of chunk metadata dicts (with document_id, chunk_index, etc.)
        similarity_threshold: Minimum similarity score to consider (0-1)
        retrieval_limit: Maximum number of chunks to return
        use_pgvector: If True, try to use pgvector SQL directly
        pg_connection: PostgreSQL connection object (if use_pgvector=True)
        
    Returns:
        List of dicts with similarity score and chunk metadata, sorted by relevance
    """
    # Try pgvector SQL first if requested and available
    if use_pgvector and pg_connection is not None:
        try:
            return _retrieve_with_pgvector(
                query_embedding, chunk_embeddings, chunk_metadata,
                similarity_threshold, retrieval_limit, pg_connection
            )
        except Exception as e:
            # Fall back to Python calculation if pgvector fails
            import warnings
            warnings.warn(f"pgvector SQL failed, falling back to Python: {e}")
    
    # Python-based calculation (fallback or default)
    if not chunk_embeddings:
        return []
    
    # Calculate similarities
    similarities = []
    for i, chunk_emb in enumerate(chunk_embeddings):
        score = cosine_similarity(query_embedding, chunk_emb)
        similarities.append((score, i))
    
    # Sort by similarity (highest first)
    similarities = sort_by_similarity(similarities, descending=True)
    
    # Filter by threshold
    filtered = filter_by_threshold(similarities, similarity_threshold)
    
    # Return top N results
    top_n = filtered[:retrieval_limit]
    
    # Build results with metadata
    results = []
    for score, idx in top_n:
        if idx < len(chunk_metadata):
            result = dict(chunk_metadata[idx])
            result["similarity_score"] = score
            results.append(result)
    
    return results


def _retrieve_with_pgvector(
    query_embedding: list,
    chunk_embeddings: list,
    chunk_metadata: list,
    similarity_threshold: float,
    retrieval_limit: int,
    pg_connection,
):
    """
    Retrieve chunks using PostgreSQL pgvector cosine distance operator (<=>).
    
    pgvector cosine distance: 1 - cosine_similarity
    So similarity = 1 - distance = 1 - (embedding <=> query_embedding)
    
    Args:
        query_embedding: 3072-dimensional query vector
        chunk_embeddings: List of stored chunk embeddings (already in DB)
        chunk_metadata: List of chunk metadata dicts
        similarity_threshold: Minimum similarity (0-1) to consider
        retrieval_limit: Maximum chunks to return
        pg_connection: Open PostgreSQL connection
        
    Returns:
        List of result dicts with similarity_score and metadata
    """
    import psycopg2
    
    if not chunk_embeddings:
        return []
    
    # Build CASE expression to convert JSONB to vector for comparison
    # Since embedding is stored as JSONB, we cast it: embedding::vector
    # The query embedding needs to be converted too
    
    # Create a temp table or use a subquery with the query embedding as vector
    with pg_connection.cursor() as cursor:
        # First, ensure pgvector extension is available
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception:
            pass  # Extension may already be enabled
        
        # Build query: select all chunks with cosine distance
        # similarity = 1 - (embedding <=> %s::vector)
        placeholders = []
        values = [query_embedding]
        
        # Since we have multiple chunk_embeddings, we need to compare each one
        # Use a subquery approach: calculate distance for each chunk
        query = """
        SELECT 
            id,
            chunk_index,
            chunk_text,
            page_number,
            document_id,
            1 - (embedding <=> %s::vector) AS similarity_score
        FROM documents_documentchunk
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        
        cursor.execute(query, [query_embedding, query_embedding, retrieval_limit])
        results = cursor.fetchall()
    
    # Convert results to expected format
    final_results = []
    for row in results:
        chunk_id, chunk_index, chunk_text, page_number, document_id, similarity_score = row
        
        # Find matching metadata
        metadata = None
        for md in chunk_metadata:
            if md.get("document_id") == document_id and md.get("chunk_index") == chunk_index:
                metadata = md
                break
        
        if metadata is not None and similarity_score is not None:
            # Convert pgvector distance to similarity (0-1 range)
            # pgvector cosine distance ranges 0-2, similarity = 1 - distance
            # But pgvector already returns 1 - cosine_similarity, so similarity_score is already in 0-1 range
            # Clamp to valid range
            sim = max(0.0, min(1.0, float(similarity_score)))
            
            result = dict(metadata)
            result["similarity_score"] = sim
            final_results.append(result)
    
    # Filter by threshold
    if similarity_threshold > 0:
        final_results = [r for r in final_results if r.get("similarity_score", 0) >= similarity_threshold]
    
    # Sort by similarity (highest first)
    final_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
    
    # Return top results
    return final_results[:retrieval_limit]