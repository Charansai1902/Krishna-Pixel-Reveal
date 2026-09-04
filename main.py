#!/usr/bin/env python3
"""
Root-level wrapper for pixel-reveal project.
Allows running `python main.py` directly from workspace root.
"""
import sys
from pathlib import Path

# Add pixel-reveal directory to sys.path
PROJECT_DIR = Path(__file__).resolve().parent / "pixel-reveal"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from main import main

if __name__ == "__main__":
    main()
