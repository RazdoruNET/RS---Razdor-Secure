#!/usr/bin/env python3
"""
Main entry point for super_dpi_combiner package
Allows running with: python -m super_dpi_combiner
"""

import sys
import os
from pathlib import Path

# Add the package root to Python path to enable absolute imports
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

from super_dpi_combiner.main import SuperDPICombiner

def main():
    """Main entry point"""
    try:
        app = SuperDPICombiner()
        app.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
