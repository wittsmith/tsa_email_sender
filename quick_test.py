#!/usr/bin/env python3
"""
Quick test script to send a mock TSA report at 11:47 AM EST
"""

import schedule
import time
from datetime import datetime
from production_tsa_report import ProductionTSAReporter

def quick_test():
    """Run a quick test of the production system."""
    print("🚀 Quick TSA Report Test")
    print("=" * 40)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    print("Scheduling test report for 11:47 AM EST...")
    
    try:
        # Create reporter instance
        reporter = ProductionTSAReporter()
        print("✅ Production reporter initialized successfully")
        
        # Schedule the test for 11:47 AM
        schedule.every().day.at("10:48").do(reporter.run_daily_report)
        
        print("⏰ Test scheduled for 11:47 AM EST")
        print("⏳ Waiting for scheduled time...")
        print("Press Ctrl+C to cancel")
        
        # Wait for the scheduled time
        while True:
            schedule.run_pending()
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    quick_test() 