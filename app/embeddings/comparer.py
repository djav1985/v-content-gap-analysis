"""Compare embeddings and compute similarities."""
import numpy as np
from typing import List, Tuple, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from app.utils.logger import get_logger

logger = get_logger(__name__)


def compute_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score between 0 and 1
    """
    # Reshape for sklearn
    emb1 = embedding1.reshape(1, -1)
    emb2 = embedding2.reshape(1, -1)
    
    similarity = cosine_similarity(emb1, emb2)[0][0]
    return float(similarity)


def find_most_similar(
    query_embedding: np.ndarray,
    embeddings: List[np.ndarray],
    top_k: int = 5
) -> List[Tuple[int, float]]:
    """
    Find most similar embeddings to query.
    
    Args:
        query_embedding: Query embedding
        embeddings: List of embeddings to compare
        top_k: Number of top results to return
        
    Returns:
        List of tuples (index, similarity_score)
    """
    if not embeddings:
        return []
    
    query = query_embedding.reshape(1, -1)
    embedding_matrix = np.array(embeddings)
    
    similarities = cosine_similarity(query, embedding_matrix)[0]
    
    # Get top k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = [(int(idx), float(similarities[idx])) for idx in top_indices]
    return results


def cluster_embeddings(
    embeddings: List[np.ndarray],
    eps: float = 0.3,
    min_samples: int = 2
) -> np.ndarray:
    """
    Cluster embeddings using DBSCAN.
    
    Args:
        embeddings: List of embedding vectors
        eps: Maximum distance between samples
        min_samples: Minimum samples in a cluster
        
    Returns:
        Cluster labels array
    """
    if not embeddings or len(embeddings) < min_samples:
        return np.array([])
    
    embedding_matrix = np.array(embeddings)
    
    # Use DBSCAN for clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering.fit_predict(embedding_matrix)
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    logger.info(f"Found {n_clusters} clusters and {n_noise} noise points")
    
    return labels


def compute_similarity_matrix(
    embeddings1: List[np.ndarray],
    embeddings2: List[np.ndarray]
) -> np.ndarray:
    """
    Compute similarity matrix between two sets of embeddings.
    
    Args:
        embeddings1: First set of embeddings
        embeddings2: Second set of embeddings
        
    Returns:
        Similarity matrix
    """
    if not embeddings1 or not embeddings2:
        return np.array([])
    
    matrix1 = np.array(embeddings1)
    matrix2 = np.array(embeddings2)
    
    similarity_matrix = cosine_similarity(matrix1, matrix2)
    
    return similarity_matrix


def find_content_gaps(
    primary_embeddings: List[Tuple[int, np.ndarray, str]],
    competitor_embeddings: List[Tuple[int, np.ndarray, str]],
    threshold: float = 0.45
) -> List[Dict]:
    """
    Find content gaps by comparing embeddings.
    
    Args:
        primary_embeddings: List of (id, embedding, url) for primary site
        competitor_embeddings: List of (id, embedding, url) for competitors
        threshold: Similarity threshold
        
    Returns:
        List of gap dictionaries
    """
    gaps = []
    
    if not primary_embeddings:
        logger.warning("No primary embeddings found")
        return gaps
    
    primary_embs = [emb for _, emb, _ in primary_embeddings]
    
    for comp_id, comp_emb, comp_url in competitor_embeddings:
        # Find most similar primary content
        similarities = [
            compute_similarity(comp_emb, prim_emb)
            for prim_emb in primary_embs
        ]
        
        if similarities:
            max_similarity = max(similarities)
            max_idx = similarities.index(max_similarity)
            closest_url = primary_embeddings[max_idx][2]
            
            if max_similarity < threshold:
                gaps.append({
                    'competitor_url': comp_url,
                    'closest_match_url': closest_url,
                    'similarity_score': max_similarity,
                    'gap_type': 'missing_content'
                })
    
    logger.info(f"Found {len(gaps)} potential content gaps")
    return gaps
