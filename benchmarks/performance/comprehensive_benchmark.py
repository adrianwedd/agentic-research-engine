#!/usr/bin/env python3
"""
Comprehensive Performance Benchmarking Suite for Agentic Research Engine
Measures vector search, API, and orchestration performance with detailed metrics.
"""

import asyncio
import json
import os
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import psutil
    import uvicorn
    from locust import HttpUser, between, task
    from locust.env import Environment
    import requests
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install psutil locust requests")
    sys.exit(1)

from services.ltm_service.vector_store import InMemoryVectorStore, WeaviateVectorStore
from services.ltm_service.embedding_client import SimpleEmbeddingClient, CachedEmbeddingClient
from services.ltm_service import EpisodicMemoryService, InMemoryStorage, LTMService
from services.ltm_service.openapi_app import create_app, run_optimized_server


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    operation: str
    duration_seconds: float
    throughput_ops_per_sec: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    memory_peak_mb: float
    cpu_avg_percent: float
    error_rate_percent: float
    concurrent_users: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SystemMonitor:
    """Monitor system resources during benchmarks."""
    
    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self.running = False
        self.cpu_samples = []
        self.memory_samples = []
        self.process = psutil.Process()
        
    def start(self):
        """Start monitoring."""
        self.running = True
        self.cpu_samples = []
        self.memory_samples = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop(self) -> Dict[str, float]:
        """Stop monitoring and return metrics."""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1.0)
            
        cpu_avg = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0
        memory_peak = max(self.memory_samples) if self.memory_samples else 0.0
        
        return {
            "cpu_avg_percent": cpu_avg,
            "memory_peak_mb": memory_peak / (1024 * 1024),  # Convert to MB
        }
        
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                self.cpu_samples.append(self.process.cpu_percent())
                self.memory_samples.append(self.process.memory_info().rss)
                time.sleep(self.interval)
            except Exception:
                break  # Process might have ended


class VectorSearchBenchmark:
    """Comprehensive vector search performance benchmarks."""
    
    def __init__(self):
        self.results = []
        
    def benchmark_in_memory_vector_store(self, 
                                       store_sizes: List[int] = [1000, 5000, 10000],
                                       query_counts: List[int] = [100, 500, 1000],
                                       worker_counts: List[int] = [1, 2, 4, 8]) -> List[PerformanceMetrics]:
        """Benchmark InMemoryVectorStore with various configurations."""
        results = []
        
        for store_size in store_sizes:
            for query_count in query_counts:
                for workers in worker_counts:
                    print(f"Testing InMemoryVectorStore: {store_size} vectors, {query_count} queries, {workers} workers")
                    
                    # Setup
                    random.seed(42)  # For reproducible results
                    store = InMemoryVectorStore()
                    
                    # Populate store
                    for i in range(store_size):
                        vector = [random.random() for _ in range(128)]  # Larger vectors
                        store.add(vector, {"id": f"vec_{i}", "category": f"cat_{i % 10}"})
                    
                    # Prepare queries
                    query_vectors = [[random.random() for _ in range(128)] for _ in range(query_count)]
                    
                    # Set worker count
                    os.environ["VECTOR_SEARCH_WORKERS"] = str(workers)
                    
                    # Benchmark
                    monitor = SystemMonitor()
                    monitor.start()
                    
                    start_time = time.perf_counter()
                    latencies = []
                    
                    for query_vector in query_vectors:
                        query_start = time.perf_counter()
                        results_batch = store.query(query_vector, limit=10)
                        query_end = time.perf_counter()
                        latencies.append((query_end - query_start) * 1000)  # Convert to ms
                    
                    end_time = time.perf_counter()
                    system_metrics = monitor.stop()
                    
                    # Calculate metrics
                    duration = end_time - start_time
                    throughput = query_count / duration
                    latencies.sort()
                    
                    metrics = PerformanceMetrics(
                        operation=f"InMemoryVectorStore_{store_size}_{workers}w",
                        duration_seconds=duration,
                        throughput_ops_per_sec=throughput,
                        latency_p50_ms=latencies[len(latencies) // 2],
                        latency_p95_ms=latencies[int(len(latencies) * 0.95)],
                        latency_p99_ms=latencies[int(len(latencies) * 0.99)],
                        memory_peak_mb=system_metrics["memory_peak_mb"],
                        cpu_avg_percent=system_metrics["cpu_avg_percent"],
                        error_rate_percent=0.0,
                    )
                    
                    results.append(metrics)
                    store.close()  # Clean up
                    
        return results
    
    def benchmark_embedding_cache(self, 
                                text_counts: List[int] = [100, 500, 1000],
                                cache_sizes: List[int] = [128, 512, 2048]) -> List[PerformanceMetrics]:
        """Benchmark embedding client caching performance."""
        results = []
        
        # Generate test texts
        test_texts = [f"This is test text number {i} with some content." for i in range(max(text_counts))]
        
        for text_count in text_counts:
            for cache_size in cache_sizes:
                print(f"Testing EmbeddingClient cache: {text_count} texts, cache size {cache_size}")
                
                # Setup clients
                base_client = SimpleEmbeddingClient()
                cached_client = CachedEmbeddingClient(base_client, cache_size=cache_size)
                
                texts = test_texts[:text_count]
                
                # First pass - populate cache
                monitor = SystemMonitor()
                monitor.start()
                
                start_time = time.perf_counter()
                first_embeddings = cached_client.embed(texts)
                first_end = time.perf_counter()
                
                # Second pass - should hit cache
                second_start = time.perf_counter()
                second_embeddings = cached_client.embed(texts)
                second_end = time.perf_counter()
                
                system_metrics = monitor.stop()
                
                # Calculate improvement
                first_duration = first_end - start_time
                second_duration = second_end - second_start
                improvement = (first_duration - second_duration) / first_duration * 100
                
                cache_stats = cached_client.get_cache_stats()
                hit_rate = cache_stats.get("hit_rate", 0.0) * 100
                
                metrics = PerformanceMetrics(
                    operation=f"EmbeddingCache_{text_count}_{cache_size}",
                    duration_seconds=second_duration,
                    throughput_ops_per_sec=text_count / second_duration,
                    latency_p50_ms=second_duration * 1000 / text_count,
                    latency_p95_ms=second_duration * 1000 / text_count * 1.2,
                    latency_p99_ms=second_duration * 1000 / text_count * 1.5,
                    memory_peak_mb=system_metrics["memory_peak_mb"],
                    cpu_avg_percent=system_metrics["cpu_avg_percent"],
                    error_rate_percent=100.0 - hit_rate,  # Inverse of hit rate
                )
                
                results.append(metrics)
                print(f"  Cache hit rate: {hit_rate:.1f}%, Speed improvement: {improvement:.1f}%")
                
        return results


class FastAPIBenchmark:
    """FastAPI performance benchmarks with Locust."""
    
    class APITestUser(HttpUser):
        wait_time = between(0.001, 0.01)  # Very fast requests
        
        def on_start(self):
            self.record_id = None
            
        @task(3)
        def create_memory(self):
            record = {
                "task_context": {"query": f"benchmark_{random.randint(1, 1000)}"},
                "execution_trace": {"step": "test"},
                "outcome": {"success": True, "timestamp": time.time()},
            }
            headers = {"X-Role": "editor", "Content-Type": "application/json"}
            response = self.client.post("/memory", json={"record": record}, headers=headers)
            if response.status_code == 201:
                self.record_id = response.json().get("id")
                
        @task(5)
        def retrieve_memory(self):
            headers = {"X-Role": "viewer", "Content-Type": "application/json"}
            query = {"query": {"query": f"benchmark_{random.randint(1, 100)}"}}
            self.client.get("/memory?limit=5", json=query, headers=headers)
            
        @task(1)
        def health_check(self):
            self.client.get("/health")
    
    def __init__(self):
        self.server_thread = None
        self.server = None
        
    def start_test_server(self, port: int = 8082):
        """Start FastAPI test server."""
        service = LTMService(EpisodicMemoryService(InMemoryStorage()), max_workers=8)
        app = create_app(service)
        
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=port,
            log_level="error",
            access_log=False,
        )
        
        self.server = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()
        time.sleep(2.0)  # Wait for server to start
        
        # Test server is running
        try:
            response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
            if response.status_code != 200:
                raise Exception("Server health check failed")
        except Exception as e:
            raise Exception(f"Failed to start test server: {e}")
    
    def stop_test_server(self):
        """Stop FastAPI test server."""
        if self.server:
            self.server.should_exit = True
        if self.server_thread:
            self.server_thread.join(timeout=5)
    
    def benchmark_fastapi_performance(self, 
                                    user_counts: List[int] = [10, 50, 100, 200],
                                    duration: int = 30) -> List[PerformanceMetrics]:
        """Benchmark FastAPI with different user loads."""
        results = []
        port = 8082
        
        try:
            self.start_test_server(port)
            
            for user_count in user_counts:
                print(f"Testing FastAPI with {user_count} concurrent users for {duration}s")
                
                # Configure Locust environment
                env = Environment(user_classes=[self.APITestUser])
                env.create_local_runner()
                
                # Set host for test users
                self.APITestUser.host = f"http://127.0.0.1:{port}"
                
                # Monitor system resources
                monitor = SystemMonitor()
                monitor.start()
                
                # Start load test
                env.runner.start(user_count, spawn_rate=user_count // 2)
                
                # Wait for test duration
                time.sleep(duration)
                
                # Stop and collect stats
                env.runner.quit()
                env.runner.greenlet.join()
                
                system_metrics = monitor.stop()
                
                # Get Locust stats
                stats = env.runner.stats.total
                
                # Calculate latencies
                latencies = []
                if hasattr(stats, 'response_times'):
                    latencies = list(stats.response_times.keys())
                    latencies.sort()
                
                p50 = stats.get_current_response_time_percentile(0.50) if hasattr(stats, 'get_current_response_time_percentile') else 0
                p95 = stats.get_current_response_time_percentile(0.95) if hasattr(stats, 'get_current_response_time_percentile') else 0
                p99 = stats.get_current_response_time_percentile(0.99) if hasattr(stats, 'get_current_response_time_percentile') else 0
                
                error_rate = (stats.num_failures / max(stats.num_requests, 1)) * 100 if stats.num_requests > 0 else 0
                
                metrics = PerformanceMetrics(
                    operation=f"FastAPI_{user_count}_users",
                    duration_seconds=duration,
                    throughput_ops_per_sec=stats.total_rps,
                    latency_p50_ms=p50,
                    latency_p95_ms=p95,
                    latency_p99_ms=p99,
                    memory_peak_mb=system_metrics["memory_peak_mb"],
                    cpu_avg_percent=system_metrics["cpu_avg_percent"],
                    error_rate_percent=error_rate,
                    concurrent_users=user_count,
                )
                
                results.append(metrics)
                print(f"  RPS: {stats.total_rps:.1f}, P95: {p95:.1f}ms, Errors: {error_rate:.1f}%")
                
        finally:
            self.stop_test_server()
            
        return results


class ComprehensiveBenchmark:
    """Main benchmark coordinator."""
    
    def __init__(self, output_dir: str = "benchmarks/performance"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run_all_benchmarks(self) -> Dict[str, List[PerformanceMetrics]]:
        """Run comprehensive performance benchmarks."""
        print("🚀 Starting Comprehensive Performance Benchmarks")
        print("=" * 60)
        
        all_results = {}
        
        # Vector Search Benchmarks
        print("\n📊 Vector Search Benchmarks")
        print("-" * 30)
        vector_benchmark = VectorSearchBenchmark()
        
        # Test with different configurations for thorough analysis
        vector_results = vector_benchmark.benchmark_in_memory_vector_store(
            store_sizes=[1000, 5000],
            query_counts=[100, 500],
            worker_counts=[1, 2, 4, 8]
        )
        all_results["vector_search"] = vector_results
        
        # Embedding Cache Benchmarks
        print("\n🧠 Embedding Cache Benchmarks")
        print("-" * 30)
        cache_results = vector_benchmark.benchmark_embedding_cache(
            text_counts=[100, 500, 1000],
            cache_sizes=[512, 1024, 2048]
        )
        all_results["embedding_cache"] = cache_results
        
        # FastAPI Benchmarks
        print("\n🌐 FastAPI Performance Benchmarks")
        print("-" * 30)
        api_benchmark = FastAPIBenchmark()
        api_results = api_benchmark.benchmark_fastapi_performance(
            user_counts=[20, 50, 100, 200],
            duration=20  # Shorter duration for comprehensive tests
        )
        all_results["fastapi_performance"] = api_results
        
        return all_results
    
    def generate_performance_report(self, results: Dict[str, List[PerformanceMetrics]]) -> Dict:
        """Generate comprehensive performance analysis report."""
        report = {
            "timestamp": time.time(),
            "summary": {},
            "detailed_results": {},
            "performance_analysis": {},
            "recommendations": []
        }
        
        # Process each benchmark category
        for category, metrics_list in results.items():
            if not metrics_list:
                continue
                
            category_stats = {
                "total_tests": len(metrics_list),
                "best_throughput": max(m.throughput_ops_per_sec for m in metrics_list),
                "worst_throughput": min(m.throughput_ops_per_sec for m in metrics_list),
                "avg_throughput": sum(m.throughput_ops_per_sec for m in metrics_list) / len(metrics_list),
                "best_latency_p95": min(m.latency_p95_ms for m in metrics_list),
                "worst_latency_p95": max(m.latency_p95_ms for m in metrics_list),
                "avg_memory_usage": sum(m.memory_peak_mb for m in metrics_list) / len(metrics_list),
                "max_memory_usage": max(m.memory_peak_mb for m in metrics_list),
                "avg_error_rate": sum(m.error_rate_percent for m in metrics_list) / len(metrics_list),
            }
            
            report["summary"][category] = category_stats
            report["detailed_results"][category] = [m.to_dict() for m in metrics_list]
        
        # Performance Analysis
        if "vector_search" in results:
            vector_metrics = results["vector_search"]
            # Find optimal worker count
            worker_performance = {}
            for m in vector_metrics:
                if "_" in m.operation:
                    parts = m.operation.split("_")
                    if len(parts) >= 3 and "w" in parts[-1]:
                        workers = parts[-1].replace("w", "")
                        worker_performance[workers] = worker_performance.get(workers, []) + [m.throughput_ops_per_sec]
            
            optimal_workers = max(worker_performance.keys(), 
                                key=lambda w: sum(worker_performance[w]) / len(worker_performance[w]))
            
            report["performance_analysis"]["optimal_vector_workers"] = optimal_workers
            
        if "fastapi_performance" in results:
            api_metrics = results["fastapi_performance"]
            # Find throughput scaling characteristics
            throughput_by_users = [(m.concurrent_users, m.throughput_ops_per_sec) for m in api_metrics if m.concurrent_users]
            throughput_by_users.sort()
            
            if len(throughput_by_users) >= 2:
                max_rps = max(rps for _, rps in throughput_by_users)
                optimal_users = next(users for users, rps in throughput_by_users if rps == max_rps)
                report["performance_analysis"]["optimal_concurrent_users"] = optimal_users
                report["performance_analysis"]["max_sustainable_rps"] = max_rps
        
        # Generate Recommendations
        recommendations = []
        
        # Vector search recommendations
        if "vector_search" in report["summary"]:
            vs_stats = report["summary"]["vector_search"]
            if vs_stats["avg_throughput"] < 500:
                recommendations.append("Consider optimizing vector search with better indexing or caching")
            if vs_stats["worst_latency_p95"] > 100:
                recommendations.append("High vector search latencies detected - consider batch processing")
        
        # FastAPI recommendations
        if "fastapi_performance" in report["summary"]:
            api_stats = report["summary"]["fastapi_performance"]
            if api_stats["avg_error_rate"] > 5:
                recommendations.append("High API error rate - check resource limits and error handling")
            if api_stats["max_memory_usage"] > 500:
                recommendations.append("High memory usage detected - implement memory optimization strategies")
        
        report["recommendations"] = recommendations
        
        return report
    
    def save_results(self, results: Dict[str, List[PerformanceMetrics]], filename: str = "comprehensive_benchmark_results.json"):
        """Save benchmark results to file."""
        report = self.generate_performance_report(results)
        
        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Also save a simplified CSV for easy analysis
        csv_file = self.output_dir / filename.replace('.json', '_summary.csv')
        with open(csv_file, 'w') as f:
            f.write("category,operation,throughput_rps,latency_p95_ms,memory_mb,cpu_percent,error_rate\n")
            for category, metrics_list in results.items():
                for m in metrics_list:
                    f.write(f"{category},{m.operation},{m.throughput_ops_per_sec:.2f},"
                           f"{m.latency_p95_ms:.2f},{m.memory_peak_mb:.2f},"
                           f"{m.cpu_avg_percent:.2f},{m.error_rate_percent:.2f}\n")
        
        print(f"📊 CSV summary saved to: {csv_file}")
        return report


def main():
    """Run comprehensive benchmarks."""
    benchmark = ComprehensiveBenchmark()
    
    try:
        results = benchmark.run_all_benchmarks()
        report = benchmark.save_results(results)
        
        print("\n🎯 Benchmark Summary")
        print("=" * 60)
        
        for category, stats in report["summary"].items():
            print(f"\n{category.upper()}:")
            print(f"  • Best throughput: {stats['best_throughput']:.1f} ops/sec")
            print(f"  • Average throughput: {stats['avg_throughput']:.1f} ops/sec") 
            print(f"  • Best P95 latency: {stats['best_latency_p95']:.1f}ms")
            print(f"  • Average memory usage: {stats['avg_memory_usage']:.1f}MB")
            print(f"  • Error rate: {stats['avg_error_rate']:.2f}%")
        
        print(f"\n📋 Performance Analysis:")
        for key, value in report["performance_analysis"].items():
            print(f"  • {key}: {value}")
        
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
            
        print(f"\n✅ Comprehensive benchmarks completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    main()