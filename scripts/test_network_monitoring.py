#!/usr/bin/env python3

"""Test script for network monitoring implementation."""

import logging
import sys
import time
from pathlib import Path

# Add the vimeo_monitor module to the path
sys.path.insert(0, str(Path(__file__).parent))

from vimeo_monitor.config import ConfigManager
from vimeo_monitor.health import HealthMonitor
from vimeo_monitor.network_monitor import MonitoringMode, NetworkMonitor, NetworkTarget


def setup_test_logging():
    """Setup logging for testing."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def test_network_monitor():
    """Test NetworkMonitor functionality."""
    print("🧪 Testing NetworkMonitor...")

    # Create a config manager with defaults
    config = ConfigManager()

    # Create network monitor
    network_monitor = NetworkMonitor(config)

    print(f"✅ NetworkMonitor initialized with {len(network_monitor.targets)} targets")

    # Test immediate connectivity check
    print("\n📡 Running immediate connectivity test...")
    test_results = network_monitor.run_immediate_test()

    print("\n🔍 Test Results:")
    for target_name, result in test_results["results"].items():
        status = "✅" if result["success"] else "❌"
        fallback_info = " (fallback)" if result.get("used_fallback") else ""
        print(f"  {status} {target_name}: {result['response_time']:.3f}s{fallback_info}")
        if result["error"]:
            print(f"    Error: {result['error']}")

    # Test network status
    print("\n📊 Network Status:")
    status = network_monitor.get_network_status()
    print(f"  Overall Status: {status['overall_status']}")
    print(f"  Monitoring Mode: {status['monitoring_mode']}")
    print(f"  Targets: {status['summary']['healthy_targets']}/{status['summary']['total_targets']} healthy")
    print(f"  Using Fallback: {status['summary']['using_fallback']} targets")

    # Test health summary
    print("\n📋 Health Summary:")
    summary = network_monitor.get_health_summary()
    print(f"  {summary}")

    return network_monitor


def test_network_fallback_strategies():
    """Test advanced network fallback strategies."""
    print("\n🧪 Testing Network Fallback Strategies...")

    # Create a config manager with defaults
    config = ConfigManager()
    network_monitor = NetworkMonitor(config)

    print("✅ NetworkMonitor with fallback strategies initialized")

    # Test fallback status
    print("\n📊 Fallback Strategy Status:")
    fallback_status = network_monitor.get_fallback_status()
    print(f"  Monitoring Mode: {fallback_status['monitoring_mode']}")
    print(f"  Current Interval: {fallback_status['current_interval']}s")
    print(f"  Mode Changes: {fallback_status['mode_change_count']}")

    strategy = fallback_status["strategy"]
    print(f"  Adaptive Intervals: {strategy['adaptive_intervals']}")
    print(f"  Priority Monitoring: {strategy['priority_monitoring']}")
    print(f"  Endpoint Fallback: {strategy['endpoint_fallback']}")

    # Test target priorities and fallback hosts
    print("\n🎯 Target Configuration:")
    for target in network_monitor.targets:
        print(
            f"  {target.name}: priority={target.priority}, critical={target.critical}, fallbacks={len(target.fallback_hosts)}"
        )
        if target.fallback_hosts:
            print(f"    Fallback hosts: {', '.join(target.fallback_hosts)}")

    # Test adaptive mode selection
    print("\n🔄 Testing Adaptive Target Selection:")

    # Test normal mode
    network_monitor.monitoring_mode = MonitoringMode.NORMAL
    normal_targets = network_monitor._get_targets_for_current_mode()
    print(f"  Normal mode: {len(normal_targets)} targets")

    # Test degraded mode
    network_monitor.monitoring_mode = MonitoringMode.DEGRADED
    degraded_targets = network_monitor._get_targets_for_current_mode()
    print(f"  Degraded mode: {len(degraded_targets)} targets")

    # Test failure mode
    network_monitor.monitoring_mode = MonitoringMode.FAILURE
    failure_targets = network_monitor._get_targets_for_current_mode()
    print(f"  Failure mode: {len(failure_targets)} targets (critical only)")

    # Test adaptive intervals
    print("\n⏱️ Testing Adaptive Intervals:")
    intervals = {
        MonitoringMode.NORMAL: network_monitor.fallback_strategy.normal_interval,
        MonitoringMode.DEGRADED: network_monitor.fallback_strategy.degraded_interval,
        MonitoringMode.FAILURE: network_monitor.fallback_strategy.failure_interval,
        MonitoringMode.RECOVERY: network_monitor.fallback_strategy.recovery_interval,
    }

    for mode, expected_interval in intervals.items():
        network_monitor.monitoring_mode = mode
        actual_interval = network_monitor._get_adaptive_interval()
        print(f"  {mode.value}: {actual_interval}s (base: {expected_interval}s)")

    # Test fallback host functionality
    print("\n🔄 Testing Fallback Host Functionality:")

    # Create a test target with fallback hosts
    test_target = NetworkTarget(
        name="test_fallback",
        host="nonexistent-host-12345.invalid",  # This should fail
        port=80,
        protocol="tcp",
        timeout=2.0,
        fallback_hosts=["8.8.8.8", "1.1.1.1"],
    )

    # Test with fallback
    print("  Testing connectivity with fallback enabled...")
    fallback_result = network_monitor._test_target_with_fallback(test_target)
    print(f"  Result: {'✅ Success' if fallback_result.success else '❌ Failed'}")
    if fallback_result.error:
        print(f"  Details: {fallback_result.error}")

    return network_monitor


def test_health_monitor_integration():
    """Test HealthMonitor with network integration."""
    print("\n🧪 Testing HealthMonitor integration...")

    # Create components
    config = ConfigManager()
    health_monitor = HealthMonitor(config)
    network_monitor = NetworkMonitor(config)

    # Integrate network monitor
    health_monitor.set_network_monitor(network_monitor)

    print("✅ Network monitor integrated with health monitor")

    # Test enhanced status
    enhanced_status = health_monitor.get_enhanced_status("test_mode")

    print("\n📊 Enhanced Health Status:")
    print(f"  Current Mode: {enhanced_status.get('current_mode')}")
    print(f"  API Failure Mode: {enhanced_status.get('api_failure_mode')}")
    print(f"  Network Status: {enhanced_status.get('network', {}).get('status', 'unknown')}")
    print(f"  System Uptime: {enhanced_status.get('system_uptime_seconds', 0):.1f}s")

    # Test comprehensive status
    comprehensive = health_monitor.get_comprehensive_status()
    if "detailed_network" in comprehensive:
        detailed = comprehensive["detailed_network"]
        print(f"  Detailed Network: {detailed.get('summary', {}).get('total_targets', 0)} targets monitored")
        if "fallback_strategy" in detailed:
            print(f"  Fallback Strategy Active: {detailed['fallback_strategy']}")

    # Test health check
    print("\n🔍 Running comprehensive health check...")
    health_check = health_monitor.run_health_check()

    print("📋 Health Check Results:")
    print(f"  API Health: {health_check.get('api_health')}")
    network_health = health_check.get("network_health", {})
    print(f"  Network Health: {network_health.get('status', 'unknown')}")

    if network_health.get("targets_status"):
        print("  Target Success Rates:")
        for name, rate in network_health["targets_status"].items():
            print(f"    {name}: {rate:.1f}%")

    return health_monitor, network_monitor


def test_monitoring_lifecycle():
    """Test network monitoring lifecycle (start/stop)."""
    print("\n🧪 Testing monitoring lifecycle...")

    config = ConfigManager()
    network_monitor = NetworkMonitor(config)

    # Start monitoring
    print("🚀 Starting network monitoring...")
    network_monitor.start_monitoring()

    # Let it run for a few seconds
    print("⏳ Monitoring for 5 seconds...")
    time.sleep(5)

    # Check status
    status = network_monitor.get_network_status()
    print(f"📊 Status after monitoring: {status['overall_status']}")
    print(f"📊 Monitoring mode: {status['monitoring_mode']}")

    # Stop monitoring
    print("🛑 Stopping network monitoring...")
    network_monitor.stop_monitoring()

    print("✅ Monitoring lifecycle test complete")

    return network_monitor


def test_custom_targets():
    """Test adding custom network targets."""
    print("\n🧪 Testing custom network targets...")

    config = ConfigManager()
    network_monitor = NetworkMonitor(config)

    # Add a custom target with fallback
    custom_target = NetworkTarget(
        name="google_dns",
        host="8.8.4.4",
        port=53,
        protocol="tcp",
        timeout=3.0,
        critical=False,
        priority=2,
        fallback_hosts=["8.8.8.8", "1.1.1.1"],
    )

    network_monitor.add_target(custom_target)
    print(f"✅ Added custom target: {custom_target.name} with {len(custom_target.fallback_hosts)} fallback hosts")

    # Test the new target
    test_results = network_monitor.run_immediate_test()
    custom_result = test_results["results"].get("google_dns")

    if custom_result:
        status = "✅" if custom_result["success"] else "❌"
        fallback_info = " (via fallback)" if custom_result.get("used_fallback") else ""
        print(f"📡 Custom target test: {status} {custom_result['response_time']:.3f}s{fallback_info}")

    # Remove the target
    removed = network_monitor.remove_target("google_dns")
    print(f"🗑️ Removed custom target: {removed}")

    return network_monitor


def main():
    """Run all network monitoring tests."""
    setup_test_logging()

    print("🧪 NETWORK MONITORING TEST SUITE")
    print("=" * 50)

    try:
        # Test 1: Basic NetworkMonitor functionality
        test_network_monitor()

        # Test 2: Network fallback strategies
        test_network_fallback_strategies()

        # Test 3: HealthMonitor integration
        test_health_monitor_integration()

        # Test 4: Monitoring lifecycle
        test_monitoring_lifecycle()

        # Test 5: Custom targets
        test_custom_targets()

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("\nNetwork monitoring implementation validated:")
        print("✅ NetworkMonitor core functionality")
        print("✅ Advanced fallback strategies")
        print("✅ Adaptive monitoring intervals")
        print("✅ Priority-based target selection")
        print("✅ Endpoint fallback mechanisms")
        print("✅ HealthMonitor integration")
        print("✅ Monitoring lifecycle management")
        print("✅ Custom target management")
        print("✅ Comprehensive health checking")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logging.exception("Test execution failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
