#!/usr/bin/env python3
"""
Quick Vector Search Performance Benchmark
Tests optimized vector search implementations.
"""

import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ltm_service.vector_store import InMemoryVectorStore
from services.ltm_service.embedding_client import SimpleEmbeddingClient, CachedEmbeddingClient


def benchmark_vector_search_improvements() -> Dict:
    """Benchmark vector search performance improvements."""
    print("🚀 Vector Search Performance Benchmark")
    print("=" * 50)
    
    results = {
        "timestamp": time.time(),
        "optimizations_tested": [],
        "performance_metrics": {}
    }
    
    # Test configurations
    store_size = 2000
    query_count = 500
    vector_dim = 128
    
    print(f"Configuration: {store_size} vectors, {query_count} queries, {vector_dim}D")
    
    # Generate test data
    random.seed(42)
    print("Generating test data...")
    vectors = []
    for i in range(store_size):
        vector = [random.random() for _ in range(vector_dim)]
        metadata = {"id": f"vec_{i}", "category": f"cat_{i % 10}", "text": f"document_{i}"}
        vectors.append((vector, metadata))
    
    query_vectors = [[random.random() for _ in range(vector_dim)] for _ in range(query_count)]
    
    # Test 1: Original single-threaded performance
    print("\n📊 Test 1: Single-threaded baseline")
    os.environ["VECTOR_SEARCH_WORKERS"] = "1"
    
    store_single = InMemoryVectorStore()
    for vector, metadata in vectors:
        store_single.add(vector, metadata)
    
    start_time = time.perf_counter()
    for query in query_vectors:
        results_batch = store_single.query(query, limit=5)
    single_duration = time.perf_counter() - start_time
    single_rps = query_count / single_duration
    
    print(f"  Duration: {single_duration:.3f}s")
    print(f"  Throughput: {single_rps:.2f} queries/sec")
    
    results["performance_metrics"]["single_threaded"] = {
        "duration": single_duration,
        "throughput_rps": single_rps,
        "workers": 1
    }
    
    # Test 2: Multi-threaded with optimizations
    print(f"\n⚡ Test 2: Multi-threaded optimized")
    worker_configs = [2, 4, 8]
    
    for workers in worker_configs:
        os.environ["VECTOR_SEARCH_WORKERS"] = str(workers)
        
        store_multi = InMemoryVectorStore()
        for vector, metadata in vectors:
            store_multi.add(vector, metadata)
        
        start_time = time.perf_counter()
        for query in query_vectors:
            results_batch = store_multi.query(query, limit=5)
        multi_duration = time.perf_counter() - start_time
        multi_rps = query_count / multi_duration
        
        improvement = ((single_duration - multi_duration) / single_duration) * 100
        rps_improvement = ((multi_rps - single_rps) / single_rps) * 100
        
        print(f"  {workers} workers:")
        print(f"    Duration: {multi_duration:.3f}s (improvement: {improvement:+.1f}%)")
        print(f"    Throughput: {multi_rps:.2f} queries/sec (improvement: {rps_improvement:+.1f}%)")
        
        results["performance_metrics"][f"{workers}_workers"] = {
            "duration": multi_duration,
            "throughput_rps": multi_rps,
            "workers": workers,
            "improvement_percent": improvement,
            "rps_improvement_percent": rps_improvement
        }
        
        store_multi.close()
    
    store_single.close()
    
    # Test 3: Embedding client caching
    print(f"\n🧠 Test 3: Embedding Cache Performance")
    
    # Generate test texts
    test_texts = [f"This is test document number {i} with unique content about topic {i % 10}" for i in range(1000)]
    
    # Test uncached client
    base_client = SimpleEmbeddingClient()
    start_time = time.perf_counter()
    embeddings_1 = base_client.embed(test_texts[:100])
    uncached_duration = time.perf_counter() - start_time
    
    # Test cached client - first pass (populate cache)
    cached_client = CachedEmbeddingClient(base_client, cache_size=2048, ttl_seconds=3600)
    start_time = time.perf_counter()
    embeddings_2 = cached_client.embed(test_texts[:100])
    first_pass_duration = time.perf_counter() - start_time
    
    # Test cached client - second pass (hit cache)
    start_time = time.perf_counter()
    embeddings_3 = cached_client.embed(test_texts[:100])
    cached_duration = time.perf_counter() - start_time
    
    cache_stats = cached_client.get_cache_stats()
    cache_improvement = ((first_pass_duration - cached_duration) / first_pass_duration) * 100
    
    print(f"  Uncached: {uncached_duration:.3f}s")
    print(f"  First pass (populating cache): {first_pass_duration:.3f}s")
    print(f"  Cached: {cached_duration:.3f}s (improvement: {cache_improvement:.1f}%)")
    print(f"  Cache hit rate: {cache_stats['hit_rate']*100:.1f}%")
    print(f"  Cache sizes: LRU={cache_stats['lru_cache_size']}, TTL={cache_stats['ttl_cache_size']}")
    
    results["performance_metrics"]["embedding_cache"] = {
        "uncached_duration": uncached_duration,
        "first_pass_duration": first_pass_duration,
        "cached_duration": cached_duration,
        "cache_improvement_percent": cache_improvement,
        "cache_hit_rate": cache_stats['hit_rate'],
        "cache_stats": cache_stats
    }
    
    # Summary
    print(f"\n🎯 Performance Summary")
    print("=" * 50)
    
    best_workers = max(worker_configs, key=lambda w: results["performance_metrics"][f"{w}_workers"]["throughput_rps"])
    best_rps = results["performance_metrics"][f"{best_workers}_workers"]["throughput_rps"]
    total_improvement = ((best_rps - single_rps) / single_rps) * 100
    
    print(f"✅ Best vector search configuration: {best_workers} workers")
    print(f"✅ Peak throughput: {best_rps:.2f} queries/sec")  
    print(f"✅ Total performance improvement: {total_improvement:.1f}%")
    print(f"✅ Embedding cache improvement: {cache_improvement:.1f}%")
    
    # Check if we addressed the performance issues
    performance_target = 500  # Target queries per second
    if best_rps >= performance_target:
        print(f"🎉 SUCCESS: Achieved target performance ({performance_target} q/s)")
        results["performance_target_achieved"] = True
    else:
        print(f"⚠️  WARNING: Below target performance ({performance_target} q/s)")
        results["performance_target_achieved"] = False
    
    results["optimizations_tested"] = [
        "Multi-threaded vector search with ThreadPoolExecutor",
        "Optimized cosine similarity with caching", 
        "Batch processing for parallel execution",
        "Enhanced embedding client with LRU + TTL caching",
        "Resource management and cleanup"
    ]
    
    results["summary"] = {
        "single_threaded_rps": single_rps,
        "best_optimized_rps": best_rps,
        "total_improvement_percent": total_improvement,
        "optimal_workers": best_workers,
        "cache_improvement_percent": cache_improvement
    }
    
    return results


def main():
    """Run quick vector benchmark."""
    try:
        results = benchmark_vector_search_improvements()
        
        # Save results
        output_file = Path("benchmarks/performance/quick_vector_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()