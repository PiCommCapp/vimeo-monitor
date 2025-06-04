#!/usr/bin/env python3

"""Comprehensive test suite for Prometheus metrics implementation.

This test suite validates the Prometheus metrics collection, HTTP server,
and integration with the existing performance monitoring system.
"""

import threading
import time

import requests
from prometheus_client import REGISTRY

from vimeo_monitor.metrics import PrometheusMetrics


def clear_prometheus_registry():
    """Clear the Prometheus registry to avoid duplicate metrics."""
    # Clear all collectors from the default registry
    collectors_to_remove = list(REGISTRY._collector_to_names.keys())
    for collector in collectors_to_remove:
        try:
            REGISTRY.unregister(collector)
        except KeyError:
            pass  # Already removed


def test_metrics_initialization():
    """Test Prometheus metrics initialization."""
    print("🧪 Testing metrics initialization...")

    # Test with metrics enabled
    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8001)
    assert metrics.enable_metrics is True
    assert metrics.metrics_port == 8001

    # Test with metrics disabled
    metrics_disabled = PrometheusMetrics(enable_metrics=False)
    assert metrics_disabled.enable_metrics is False

    print("✅ Metrics initialization test passed")


def test_metrics_server():
    """Test Prometheus metrics HTTP server."""
    print("🧪 Testing metrics HTTP server...")

    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8002)

    # Start server
    metrics.start_metrics_server()
    time.sleep(2)  # Allow server to start

    try:
        # Test metrics endpoint
        response = requests.get("http://localhost:8002/metrics", timeout=5)
        assert response.status_code == 200
        assert "vimeo_monitor" in response.text
        print(f"  ✅ Server responded with {len(response.text)} bytes of metrics")

        # Test that we get valid Prometheus format
        lines = response.text.split("\n")
        metric_lines = [line for line in lines if line and not line.startswith("#")]
        assert len(metric_lines) > 0
        print(f"  ✅ Found {len(metric_lines)} metric lines")

    finally:
        metrics.stop_metrics_server()

    print("✅ Metrics server test passed")


def test_api_metrics_recording():
    """Test API metrics recording."""
    print("🧪 Testing API metrics recording...")

    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8003)
    metrics.start_metrics_server()
    time.sleep(1)

    try:
        # Record various API metrics
        metrics.record_api_request("stream_data", 0.5, "success")
        metrics.record_api_request("stream_data", 1.2, "success")
        metrics.record_api_request("stream_data", 0.8, "error")

        # Record cache metrics
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()

        # Record failures
        metrics.record_api_failure("timeout")
        metrics.record_api_failure("connection_error")

        # Get metrics output
        exported = metrics.export_metrics()

        # Verify metrics are present
        assert "vimeo_monitor_api_requests_total" in exported
        assert "vimeo_monitor_api_response_time" in exported
        assert "vimeo_monitor_api_cache_hits_total" in exported
        assert "vimeo_monitor_api_failures_total" in exported

        print("  ✅ API request metrics recorded")
        print("  ✅ Cache metrics recorded")
        print("  ✅ Failure metrics recorded")

    finally:
        metrics.stop_metrics_server()

    print("✅ API metrics recording test passed")


def test_stream_and_network_metrics():
    """Test stream and network metrics recording."""
    print("🧪 Testing stream and network metrics...")

    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8004)
    metrics.start_metrics_server()
    time.sleep(1)

    try:
        # Record stream metrics
        metrics.record_stream_mode_change("holding", "live")
        metrics.update_stream_status("test_video_123", True)

        # Record network metrics
        metrics.update_network_metrics("vimeo.com", "https", True, 0.2)
        metrics.update_network_metrics("8.8.8.8", "icmp", False)
        metrics.record_network_recovery("cloudflare.com")

        # Get metrics output
        exported = metrics.export_metrics()

        # Verify stream metrics
        assert "vimeo_monitor_stream_mode" in exported
        assert "vimeo_monitor_stream_mode_changes_total" in exported
        assert "vimeo_monitor_stream_status" in exported

        # Verify network metrics
        assert "vimeo_monitor_network_connectivity" in exported
        assert "vimeo_monitor_network_response_time" in exported
        assert "vimeo_monitor_network_recovery_total" in exported

        print("  ✅ Stream metrics recorded")
        print("  ✅ Network metrics recorded")

    finally:
        metrics.stop_metrics_server()

    print("✅ Stream and network metrics test passed")


def test_health_and_cache_metrics():
    """Test health and cache metrics recording."""
    print("🧪 Testing health and cache metrics...")

    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8005)
    metrics.start_metrics_server()
    time.sleep(1)

    try:
        # Record health metrics
        metrics.update_health_status(True, {"api": True, "network": False, "stream": True})

        # Record failure mode
        metrics.update_failure_mode("api_failure", True)

        # Record cache metrics
        metrics.update_cache_metrics("api", 45, 0.75)  # 75% hit rate

        # Record performance metrics
        metrics.record_gc_collection(0, 0.05)  # 50ms GC
        metrics.record_performance_optimization()

        # Get metrics output
        exported = metrics.export_metrics()

        # Verify health metrics
        assert "vimeo_monitor_health_status" in exported
        assert "vimeo_monitor_component_health" in exported
        assert "vimeo_monitor_failure_mode" in exported

        # Verify cache metrics
        assert "vimeo_monitor_cache_size" in exported
        assert "vimeo_monitor_cache_hit_rate" in exported

        # Verify performance metrics
        assert "vimeo_monitor_gc_collections_total" in exported
        assert "vimeo_monitor_performance_optimization_runs_total" in exported

        print("  ✅ Health metrics recorded")
        print("  ✅ Cache metrics recorded")
        print("  ✅ Performance metrics recorded")

    finally:
        metrics.stop_metrics_server()

    print("✅ Health and cache metrics test passed")


def test_system_metrics_collection():
    """Test automatic system metrics collection."""
    print("🧪 Testing system metrics collection...")

    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8006)
    metrics.start_metrics_server()

    try:
        # Wait for background collection
        time.sleep(6)  # Collection runs every 5 seconds

        # Get metrics output
        exported = metrics.export_metrics()

        # Verify system metrics are being collected
        assert "vimeo_monitor_cpu_usage_percent" in exported
        assert "vimeo_monitor_memory_usage_bytes" in exported
        assert "vimeo_monitor_thread_count" in exported
        assert "vimeo_monitor_uptime_seconds" in exported

        print("  ✅ CPU metrics collected")
        print("  ✅ Memory metrics collected")
        print("  ✅ Thread metrics collected")
        print("  ✅ Uptime metrics collected")

    finally:
        metrics.stop_metrics_server()

    print("✅ System metrics collection test passed")


def test_metrics_summary():
    """Test metrics summary functionality."""
    print("🧪 Testing metrics summary...")

    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8007)

    # Test summary
    summary = metrics.get_metrics_summary()
    assert "system" in summary
    assert "metrics_server" in summary
    assert summary["metrics_server"]["enabled"] is True
    assert summary["metrics_server"]["port"] == 8007

    # Test with disabled metrics
    metrics_disabled = PrometheusMetrics(enable_metrics=False)
    summary_disabled = metrics_disabled.get_metrics_summary()
    assert "error" in summary_disabled

    print("  ✅ Metrics summary generated")
    print("  ✅ Disabled metrics handled")

    print("✅ Metrics summary test passed")


def test_concurrent_metrics_recording():
    """Test concurrent metrics recording (thread safety)."""
    print("🧪 Testing concurrent metrics recording...")

    metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8008)
    metrics.start_metrics_server()
    time.sleep(1)

    def record_metrics(worker_id: int):
        """Worker function to record metrics concurrently."""
        for i in range(10):
            metrics.record_api_request(f"endpoint_{worker_id}", 0.1 * i, "success")
            metrics.record_cache_hit()
            time.sleep(0.01)

    try:
        # Start multiple workers
        workers = []
        for i in range(5):
            worker = threading.Thread(target=record_metrics, args=(i,))
            workers.append(worker)
            worker.start()

        # Wait for all workers to complete
        for worker in workers:
            worker.join()

        # Verify metrics were recorded
        exported = metrics.export_metrics()
        assert "vimeo_monitor_api_requests_total" in exported
        assert "vimeo_monitor_api_cache_hits_total" in exported

        print("  ✅ Concurrent metrics recording completed")

    finally:
        metrics.stop_metrics_server()

    print("✅ Concurrent metrics test passed")


def main():
    """Run all Prometheus metrics tests."""
    print("🚀 Starting Prometheus Metrics Test Suite")
    print("=" * 60)

    tests = [
        test_metrics_initialization,
        test_metrics_server,
        test_api_metrics_recording,
        test_stream_and_network_metrics,
        test_health_and_cache_metrics,
        test_system_metrics_collection,
        test_metrics_summary,
        test_concurrent_metrics_recording,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1
            print()

    print("=" * 60)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All Prometheus metrics tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
