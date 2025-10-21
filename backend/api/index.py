"""
Vercel Serverless Function Entry Point
"""
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app

# Export app directly for Vercel (Vercel supports ASGI natively)
# No need for Mangum wrapper
