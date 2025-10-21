"""
Vercel Serverless Function Entry Point
"""
from app.main import app
from mangum import Mangum

# Wrap FastAPI app for Vercel
handler = Mangum(app, lifespan="off")
