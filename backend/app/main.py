"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.fourier import router as fourier_router
from app.api.fourier_v2 import router as fourier_router_v2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Calculator - Fourier Series",
    description="AI-powered mathematical derivation platform with transparent reasoning",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(fourier_router)  # V1 API (legacy)
app.include_router(fourier_router_v2)  # V2 API (three-stage flow with streaming)


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting AI Calculator API")
    try:
        settings.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Calculator - Fourier Series API",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
