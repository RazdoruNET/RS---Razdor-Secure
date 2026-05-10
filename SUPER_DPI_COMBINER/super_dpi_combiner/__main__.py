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

from super_dpi_combiner.main import main

if __name__ == "__main__":
    main()
