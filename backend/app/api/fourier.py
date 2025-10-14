"""
API endpoints for Fourier series computation
"""
from fastapi import APIRouter, HTTPException
import logging

from app.schemas.fourier import FourierRequest, FourierResponse
from app.services.fourier_service import FourierSeriesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["fourier"])

# Initialize service
fourier_service = FourierSeriesService()


@router.post("/fourier-series", response_model=FourierResponse)
async def compute_fourier_series(request: FourierRequest):
    """
    Compute Fourier series for a given function.

    This endpoint:
    1. Uses AI (Claude) to derive the Fourier series
    2. Verifies the result using numerical integration
    3. Iterates if verification fails (max 3 attempts)
    4. Returns visualization data for plotting

    Args:
        request: FourierRequest with function expression, period, and number of terms

    Returns:
        FourierResponse with derivation, verification, and visualization data

    Raises:
        HTTPException: If computation fails
    """
    try:
        logger.info(
            f"Received request: f(t)={request.function_expr}, "
            f"T={request.period}, n={request.n_terms}"
        )

        result = await fourier_service.compute_with_verification(
            function_expr=request.function_expr,
            period=request.period,
            n_terms=request.n_terms,
        )

        # Format response (works for both success and failure cases)
        response_data = {
            "success": result["success"],
            "iterations": result["iterations"],
            "visualization": result.get("visualization"),
        }

        if result["success"]:
            # Success case - include full details
            response_data.update({
                "thinking_process": result["thinking_process"],
                "coefficients": result["coefficients"],
                "final_result": result["final_result"],
                "verification": {
                    "is_verified": result["verification"]["is_verified"],
                    "max_error": result["verification"]["error_metrics"]["max_error"],
                    "mean_error": result["verification"]["error_metrics"]["mean_error"],
                    "numerical_coefficients": result["verification"][
                        "numerical_coefficients"
                    ],
                },
            })
        else:
            # Failure case - still include what we have for visualization
            last_verif = result.get("last_verification")
            response_data.update({
                "error": result.get("error"),
                "coefficients": result.get("coefficients"),
                "verification": {
                    "is_verified": False,
                    "max_error": last_verif["error_metrics"]["max_error"] if last_verif else 1.0,
                    "mean_error": last_verif["error_metrics"]["mean_error"] if last_verif else 1.0,
                    "numerical_coefficients": last_verif["numerical_coefficients"] if last_verif else None,
                } if last_verif else None,
            })

        return FourierResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Calculator - Fourier Series"}
