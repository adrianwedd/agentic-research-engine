#!/usr/bin/env python3
"""
Simple test to validate our performance optimizations.
"""

import os
import random
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ltm_service.vector_store import InMemoryVectorStore
from services.ltm_service.embedding_client import SimpleEmbeddingClient, CachedEmbeddingClient

def test_vector_optimizations():
    """Test core vector optimization improvements."""
    print("Testing Vector Search Optimizations...")
    
    # Small test dataset
    store_size = 500
    query_count = 100
    
    # Generate test data
    random.seed(42)
    store = InMemoryVectorStore()
    
    print(f"Adding {store_size} vectors...")
    for i in range(store_size):
        vector = [random.random() for _ in range(64)]  # Smaller vectors for speed
        store.add(vector, {"id": f"vec_{i}"})
    
    query_vectors = [[random.random() for _ in range(64)] for _ in range(query_count)]
    
    # Test single-threaded
    print("Testing single-threaded...")
    os.environ["VECTOR_SEARCH_WORKERS"] = "1"
    start_time = time.perf_counter()
    for query in query_vectors[:50]:  # Smaller batch for speed
        results = store.query(query, limit=5)
    single_duration = time.perf_counter() - start_time
    print(f"Single-threaded: {single_duration:.3f}s")
    
    # Test multi-threaded
    print("Testing multi-threaded...")
    os.environ["VECTOR_SEARCH_WORKERS"] = "4"
    start_time = time.perf_counter()
    for query in query_vectors[:50]:
        results = store.query(query, limit=5)
    multi_duration = time.perf_counter() - start_time
    print(f"Multi-threaded (4 workers): {multi_duration:.3f}s")
    
    improvement = ((single_duration - multi_duration) / single_duration) * 100
    print(f"Performance improvement: {improvement:.1f}%")
    
    store.close()
    return improvement

def test_embedding_cache():
    """Test embedding cache improvements."""
    print("\nTesting Embedding Cache...")
    
    # Generate test texts
    texts = [f"Test document {i}" for i in range(100)]
    
    base_client = SimpleEmbeddingClient()
    cached_client = CachedEmbeddingClient(base_client, cache_size=512)
    
    # First pass - populate cache
    print("First pass (populating cache)...")
    start_time = time.perf_counter()
    embeddings1 = cached_client.embed(texts)
    first_duration = time.perf_counter() - start_time
    print(f"First pass: {first_duration:.3f}s")
    
    # Second pass - should hit cache
    print("Second pass (cache hits)...")
    start_time = time.perf_counter()
    embeddings2 = cached_client.embed(texts)
    cached_duration = time.perf_counter() - start_time
    print(f"Cached pass: {cached_duration:.3f}s")
    
    cache_improvement = ((first_duration - cached_duration) / first_duration) * 100
    print(f"Cache improvement: {cache_improvement:.1f}%")
    
    cache_stats = cached_client.get_cache_stats()
    print(f"Cache hit rate: {cache_stats['hit_rate']*100:.1f}%")
    
    return cache_improvement

def main():
    """Run simple performance validation."""
    print("🚀 Simple Performance Validation")
    print("=" * 40)
    
    try:
        vector_improvement = test_vector_optimizations()
        cache_improvement = test_embedding_cache()
        
        print(f"\n🎯 Results Summary")
        print("=" * 40)
        print(f"Vector search improvement: {vector_improvement:.1f}%")
        print(f"Embedding cache improvement: {cache_improvement:.1f}%")
        
        # Check if optimizations are working
        if vector_improvement > 0:
            print("✅ Vector search optimizations: WORKING")
        else:
            print("⚠️  Vector search optimizations: NEEDS ATTENTION") 
            
        if cache_improvement > 50:
            print("✅ Embedding cache optimizations: WORKING")
        else:
            print("⚠️  Embedding cache optimizations: NEEDS ATTENTION")
            
        print("\n🎉 Performance validation completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()