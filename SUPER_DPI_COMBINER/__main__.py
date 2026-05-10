#!/usr/bin/env python3
"""
Super DPI Combiner - Package entry point
Allows running with: python -m super_dpi_combiner
"""

import sys
from pathlib import Path

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from main import main

if __name__ == "__main__":
    main()
