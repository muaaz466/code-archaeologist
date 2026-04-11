"""Root entry point for Render deployment"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the actual app from backend.api
from backend.api.main import app

# Re-export for uvicorn
__all__ = ['app']
