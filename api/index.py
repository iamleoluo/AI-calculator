"""
Vercel serverless function entry point
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import app

# Export app directly for Vercel
# Vercel will automatically detect this
__all__ = ["app"]
