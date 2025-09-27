#!/usr/bin/env python3
"""
Startup script for AI Role-Playing Chat Application

This is the main entry point that should be run from the project root.
It redirects to the scripts/run.py with proper path handling.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main startup script
from scripts.run import main

if __name__ == "__main__":
    main()