import sys
import os

# Add project root to sys.path to allow imports from utils, managers etc.
# Assumes pytest is run from the project root directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
