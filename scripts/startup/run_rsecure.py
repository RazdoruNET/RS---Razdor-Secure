#!/usr/bin/env python3
"""
RSecure Launcher Script
Simple launcher for RSecure security system
"""

import sys
import os
import time
from pathlib import Path

# Add rsecure directory to Python path
rsecure_path = Path(__file__).parent / "rsecure"
sys.path.insert(0, str(rsecure_path))

try:
    from rsecure_main import RSecureMain
    
    def main():
        """Main entry point"""
        print("🛡️  Starting RSecure Security System...")
        print("=" * 50)
        
        # Create and start RSecure
        rsecure = RSecureMain()
        
        try:
            rsecure.start()
            print("\n✅ RSecure is running!")
            print("Press Ctrl+C to stop")
            
            # Keep the main thread alive
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping RSecure...")
            rsecure.stop()
            print("✅ RSecure stopped successfully")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            rsecure.stop()
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all dependencies are installed and the rsecure directory exists")
    sys.exit(1)
