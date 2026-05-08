#!/usr/bin/env python3
"""
QUICK START - Ready to run STORM-COMPLIANCE system
Just configure your API credentials and run!
"""

import asyncio
import os
from main_executor import StormComplianceSystem

# CONFIGURE THESE VALUES
API_ID = 12345678  # Replace with your Telegram API ID
API_HASH = "your_api_hash_here"  # Replace with your Telegram API hash
TARGET_CHANNEL = "@example_channel"  # Replace with target channel

async def quick_start():
    """Quick start - single run"""
    print("🚀 STORM-COMPLIANCE QUICK START")
    print("="*50)
    
    # Initialize system
    system = StormComplianceSystem(API_ID, API_HASH)
    
    try:
        # Initialize components
        if not await system.initialize():
            print("❌ System initialization failed")
            print("Make sure you have:")
            print("1. Valid API credentials")
            print("2. Session files in sessions/ directory")
            return
        
        print(f"✅ System initialized successfully")
        print(f"📡 Target: {TARGET_CHANNEL}")
        print(f"🔍 Starting analysis and reporting...")
        
        # Run complete workflow
        results = await system.analyze_and_report(
            TARGET_CHANNEL, 
            scan_limit=100, 
            auto_report=True
        )
        
        # Display results
        print("\n📊 RESULTS:")
        print("-" * 30)
        
        if results['analysis']:
            total_violations = sum(len(v) for v in results['analysis']['violations'].values())
            print(f"🔍 Violations Found: {total_violations}")
            
            for category, violations in results['analysis']['violations'].items():
                if violations:
                    print(f"  • {category}: {len(violations)}")
        
        if results['reporting']:
            if 'successful_reports' in results['reporting']:
                success_rate = (results['reporting']['successful_reports']/results['reporting']['total_reports']*100)
                print(f"📤 Reports Sent: {results['reporting']['successful_reports']}/{results['reporting']['total_reports']}")
                print(f"✅ Success Rate: {success_rate:.1f}%")
        
        print(f"⏱️  Duration: {results['duration_seconds']:.2f} seconds")
        
        if results['errors']:
            print(f"❌ Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  • {error}")
        
        print("\n✅ COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await system.cleanup()

async def continuous_mode():
    """Continuous monitoring mode"""
    print("🔄 STORM-COMPLIANCE CONTINUOUS MODE")
    print("="*50)
    
    system = StormComplianceSystem(API_ID, API_HASH)
    
    try:
        if not await system.initialize():
            print("❌ System initialization failed")
            return
        
        print(f"📡 Target: {TARGET_CHANNEL}")
        print(f"⏰ Scanning every 30 minutes...")
        print("Press Ctrl+C to stop")
        
        await system.continuous_monitoring(
            TARGET_CHANNEL, 
            interval_minutes=30, 
            scan_limit=50
        )
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    finally:
        await system.cleanup()

if __name__ == "__main__":
    print("Choose mode:")
    print("1. Quick start (single run)")
    print("2. Continuous monitoring")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(quick_start())
    elif choice == "2":
        asyncio.run(continuous_mode())
    else:
        print("Invalid choice")
