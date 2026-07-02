import os
import sys

# Ensure project root is at the head of Python's search path for pytest imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
