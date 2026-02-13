# monitoring.py: Chapter 3 - Chief Engineer Oversight System
# Refactored for Clean Architecture (v2.7)

import os
from datetime import datetime as dt
from pathlib import Path
from Core.System.lifecycle import state
async def run_chapter_3_oversight():
    """
    Chapter 3: Chief Engineer Monitoring.
    Runs health checks and returns status.
    """
    print("\n   [Chapter 3] Chief Engineer performing oversight...")
    
    health_status = perform_health_check()
    # report = generate_oversight_report(health_status)
    
    # Telegram Disabled v2.8
    # print("   [Chapter 3] Oversight report generated.")
    
    return health_status

def perform_health_check():
    """Checks various system components for issues."""
    issues = []
    
    # 1. Check Data Store integrity
    store_path = Path("Data/Store")
    if not store_path.exists():
        issues.append("❌ Data store directory missing.")
    else:
        # Check if predictions.csv exists and has been updated recently
        pred_file = store_path / "predictions.csv"
        if pred_file.exists():
            import time
            mtime = os.path.getmtime(pred_file)
            if (time.time() - mtime) > 86400: # 24 hours
                issues.append("⚠️ `predictions.csv` hasn't been updated in 24h.")
        else:
            issues.append("❌ `predictions.csv` missing.")

    # 2. Check Error Log
    error_count = len(state.get("error_log", []))
    if error_count > 0:
        issues.append(f"⚠️ {error_count} errors logged this cycle.")

    # 3. Check Balance Stagnation (Simple check)
    if state.get("current_balance", 0) <= 0:
         issues.append("⚠️ Account balance is zero or unknown.")

    return issues if issues else ["✅ System is healthy and operational."]

def generate_oversight_report(health_status):
    """Formats the oversight findings into a readable string."""
    status_summary = "\n".join(health_status)
    
    report = (
        f"Cycle Count: #{state.get('cycle_count', 0)}\n"
        f"Uptime: {dt.now() - state.get('cycle_start_time', dt.now())}\n"
        f"Current Balance: ₦{state.get('current_balance', 0):,.2f}\n"
        f"Booked: {state.get('booked_this_cycle', 0)}\n"
        f"Failed: {state.get('failed_this_cycle', 0)}\n\n"
        f"**Health Check:**\n{status_summary}"
    )
    return report
