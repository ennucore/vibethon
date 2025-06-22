#!/usr/bin/env python3
"""
Entry point for running vibethon as a module: python -m vibethon
"""

import sys
import os

# Add parent directory to path to import vibethon_cli
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vibethon_cli import main

if __name__ == '__main__':
    sys.exit(main())