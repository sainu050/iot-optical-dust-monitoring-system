"""
Automated Data Flow Verification & Test Suite
Course: 24MCAT213 - INTERNET OF THINGS | Amal Jyothi College of Engineering
Tests Requirement 6: Demonstrate complete data flow (Sensor -> Backend -> DB -> Dashboard)
"""

import sys
import os
from datetime import datetime

def run_tests():
    print("=" * 65)
    print("  RUNNING IOT DUST SYSTEM AUTOMATED DATA FLOW VERIFICATION")
    print("  Course: 24MCAT213 - Internet of Things | Amal Jyothi College")
    print("=" * 65)

    passed_tests = 0
    total_tests = 5

    try:
        from app.main import (
            app, 
            health_check, 
            receive_sensor_data, 
            get_latest_readings, 
            get_sensor_summary,
            SensorPayload, 
            SessionLocal, 
            SensorRecord
        )
    except Exception as e:
        print(f"CRITICAL ERROR importing application backend: {e}")
        return 1

    # Test 1: Health Check Endpoint
    print("\n[Test 1/5] Checking Backend Health Endpoint (/api/health)...")
    health = health_check()
    if health.get("status") == "healthy" and health.get("service") == "iot-dust-backend":
        print(f"  -> PASS: Backend is healthy and operational. (Timestamp: {health.get('timestamp')})")
        passed_tests += 1
    else:
        print(f"  -> FAIL: Health check unexpected response: {health}")

    # Test 2: Ingest Sensor Data (ESP32 POST Telemetry Ingestion)
    print("\n[Test 2/5] Simulating Sensor Telemetry Ingestion (POST /api/sensor-data)...")
    payload = SensorPayload(
        device_id="ESP32_Dust_01",
        voltage=1.35,
        dust_density=94.50
    )
    result = receive_sensor_data(payload)
    saved_id = result.get("id")
    if result.get("status") == "success" and saved_id:
        print(f"  -> PASS: Sensor reading accepted and stored with Record ID #{saved_id}.")
        passed_tests += 1
    else:
        print(f"  -> FAIL: Failed to store sensor reading: {result}")

    # Test 3: Verify SQLite Database Persistence
    print("\n[Test 3/5] Verifying SQLite Database Storage & Persistence...")
    db = SessionLocal()
    try:
        record = db.query(SensorRecord).filter(SensorRecord.id == saved_id).first()
        if record and record.voltage == 1.35 and record.dust_density == 94.50:
            print(f"  -> PASS: Record #{record.id} successfully queried from SQLite table 'dust_readings'.")
            print(f"           Device: {record.device_id} | Vo: {record.voltage}V | Density: {record.dust_density} ug/m3")
            passed_tests += 1
        else:
            print("  -> FAIL: Record not found in SQLite database or values do not match.")
    finally:
        db.close()

    # Test 4: Dashboard Telemetry API Readout (GET /api/sensor-data/latest)
    print("\n[Test 4/5] Checking Dashboard Real-Time API Endpoint (/api/sensor-data/latest)...")
    latest_list = get_latest_readings(limit=10)
    if isinstance(latest_list, list) and len(latest_list) > 0:
        latest_item = latest_list[-1]
        print(f"  -> PASS: Dashboard API returned {len(latest_list)} records. Latest: {latest_item}")
        passed_tests += 1
    else:
        print(f"  -> FAIL: Telemetry query failed: {latest_list}")

    # Test 5: Verify Static Dashboard Files & Summary Endpoint
    print("\n[Test 5/5] Verifying Static Dashboard UI Files & Summary Metrics...")
    html_path = os.path.join(os.path.dirname(__file__), "app", "static", "index.html")
    summary = get_sensor_summary()
    if os.path.exists(html_path) and summary.get("count", 0) > 0:
        file_size = os.path.getsize(html_path)
        print(f"  -> PASS: 'index.html' verified ({file_size} bytes). Total records in DB: {summary.get('count')}, Avg Dust: {summary.get('avg_dust')} ug/m3.")
        passed_tests += 1
    else:
        print(f"  -> FAIL: Static file missing or summary check failed.")

    print("\n" + "=" * 65)
    print(f"  TEST SUMMARY: {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)")
    print("=" * 65)

    if passed_tests == total_tests:
        print("\nALL SYSTEM REQUIREMENTS FULLY VERIFIED AND OPERATIONAL!\n")
        return 0
    else:
        print("\nSome tests failed. Please review the output above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
