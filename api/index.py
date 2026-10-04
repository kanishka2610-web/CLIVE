import sys
import os

# Add repository root directory to sys.path so backend imports work on Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
