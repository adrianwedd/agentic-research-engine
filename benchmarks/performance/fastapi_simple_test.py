#!/usr/bin/env python3
"""
Simple FastAPI performance test.
"""

import json
import requests
import sys
import threading
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ltm_service import EpisodicMemoryService, InMemoryStorage, LTMService
from services.ltm_service.openapi_app import run_optimized_server

def start_test_server():
    """Start optimized FastAPI server for testing."""
    service = LTMService(EpisodicMemoryService(InMemoryStorage()), max_workers=4)
    
    # Start server in background thread
    def run_server():
        try:
            run_optimized_server(service, host="127.0.0.1", port=8083, log_level="error")
        except Exception as e:
            print(f"Server error: {e}")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start and test connection
    for _ in range(10):
        try:
            response = requests.get("http://127.0.0.1:8083/health", timeout=1)
            if response.status_code == 200:
                print("✅ FastAPI server started successfully")
                return server_thread
        except:
            time.sleep(0.5)
    
    raise Exception("Failed to start FastAPI server")

def test_api_performance():
    """Test FastAPI performance with basic operations."""
    print("🌐 Testing FastAPI Performance")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:8083"
    headers = {"Content-Type": "application/json", "X-Role": "editor"}
    
    # Test health endpoint
    print("Testing health endpoint...")
    start_time = time.perf_counter()
    response = requests.get(f"{base_url}/health")
    health_duration = time.perf_counter() - start_time
    
    if response.status_code == 200:
        print(f"✅ Health check: {health_duration*1000:.2f}ms")
        health_data = response.json()
        print(f"   Status: {health_data.get('status')}")
        print(f"   Uptime: {health_data.get('uptime', 0):.2f}s")
    else:
        print(f"❌ Health check failed: {response.status_code}")
    
    # Test memory operations
    print("\nTesting memory operations...")
    
    # Create memory records
    create_times = []
    record_ids = []
    
    for i in range(10):  # Small batch for speed
        record = {
            "task_context": {"query": f"test_query_{i}"},
            "execution_trace": {"step": f"test_step_{i}"},
            "outcome": {"success": True, "result": f"test_result_{i}"}
        }
        
        start_time = time.perf_counter()
        response = requests.post(
            f"{base_url}/memory",
            json={"record": record, "memory_type": "episodic"},
            headers=headers
        )
        create_time = time.perf_counter() - start_time
        create_times.append(create_time)
        
        if response.status_code == 201:
            record_ids.append(response.json()["id"])
        else:
            print(f"❌ Create memory failed: {response.status_code}")
    
    avg_create_time = sum(create_times) / len(create_times)
    print(f"✅ Create operations: {avg_create_time*1000:.2f}ms avg ({len(record_ids)} records)")
    
    # Retrieve memory records
    retrieve_times = []
    
    for i in range(10):
        query = {"query": {"query": f"test_query_{i % 5}"}}
        
        start_time = time.perf_counter()
        response = requests.get(
            f"{base_url}/memory?memory_type=episodic&limit=5",
            json=query,
            headers={"X-Role": "viewer", "Content-Type": "application/json"}
        )
        retrieve_time = time.perf_counter() - start_time
        retrieve_times.append(retrieve_time)
        
        if response.status_code != 200:
            print(f"❌ Retrieve memory failed: {response.status_code}")
    
    avg_retrieve_time = sum(retrieve_times) / len(retrieve_times)
    print(f"✅ Retrieve operations: {avg_retrieve_time*1000:.2f}ms avg")
    
    # Calculate throughput
    total_operations = len(create_times) + len(retrieve_times)
    total_time = sum(create_times) + sum(retrieve_times)
    throughput = total_operations / total_time if total_time > 0 else 0
    
    print(f"\n🎯 Performance Summary")
    print("=" * 40)
    print(f"Average create latency: {avg_create_time*1000:.2f}ms")
    print(f"Average retrieve latency: {avg_retrieve_time*1000:.2f}ms")
    print(f"Overall throughput: {throughput:.1f} ops/sec")
    
    # Performance targets
    target_latency_ms = 100  # 100ms target
    target_throughput = 50   # 50 ops/sec target
    
    success = True
    if avg_create_time * 1000 > target_latency_ms:
        print(f"⚠️  Create latency above target ({target_latency_ms}ms)")
        success = False
    
    if avg_retrieve_time * 1000 > target_latency_ms:
        print(f"⚠️  Retrieve latency above target ({target_latency_ms}ms)")
        success = False
    
    if throughput < target_throughput:
        print(f"⚠️  Throughput below target ({target_throughput} ops/sec)")
        success = False
    
    if success:
        print("🎉 All performance targets met!")
    
    return {
        "avg_create_latency_ms": avg_create_time * 1000,
        "avg_retrieve_latency_ms": avg_retrieve_time * 1000,
        "throughput_ops_per_sec": throughput,
        "targets_met": success
    }

def main():
    """Run FastAPI performance test."""
    try:
        # Start server
        server_thread = start_test_server()
        
        # Wait a moment for full startup
        time.sleep(1.0)
        
        # Run tests
        results = test_api_performance()
        
        print(f"\n📊 Test Results: {json.dumps(results, indent=2)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()