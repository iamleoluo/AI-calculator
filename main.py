"""
Vercel entry point - imports FastAPI app from backend
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import the FastAPI app
from app.main import app

# Vercel will automatically detect this
__all__ = ["app"]
