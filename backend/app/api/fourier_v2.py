"""
Refactored API endpoints for Fourier series with SSE streaming support
"""
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.fourier_service_v2 import FourierSeriesServiceV2

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["fourier-v2"])


class FourierSeriesRequest(BaseModel):
    """Request model for Fourier series computation"""
    function_expr: str = Field(..., description="Python expression for the function (e.g., 'np.sin(t)')")
    period: float = Field(..., gt=0, description="Period of the function")
    n_terms: int = Field(..., ge=1, le=20, description="Number of terms to compute (1-20)")

    class Config:
        json_schema_extra = {
            "example": {
                "function_expr": "np.sin(t)",
                "period": 6.283185,
                "n_terms": 5
            }
        }


@router.options("/fourier-series/stream")
async def fourier_series_stream_options():
    """Handle CORS preflight request"""
    from fastapi import Response
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
            "Access-Control-Max-Age": "86400",
        }
    )


@router.post("/fourier-series/stream")
async def compute_fourier_series_stream(request: FourierSeriesRequest):
    """
    Compute Fourier series with Server-Sent Events (SSE) streaming.

    This endpoint streams the computation process in real-time:
    1. Derivation process (Markdown chunks)
    2. Code generation
    3. Verification results
    4. Error analysis (if needed)
    5. Final result

    Returns:
        StreamingResponse with text/event-stream content type

    Event format:
        data: {"type": "...", ...}\\n\\n
    """
    logger.info(f"Received streaming request: {request.function_expr}, T={request.period}, n={request.n_terms}")

    service = FourierSeriesServiceV2()

    async def event_generator():
        """Generate SSE events from service"""
        try:
            async for event in service.compute_with_streaming(
                function_expr=request.function_expr,
                period=request.period,
                n_terms=request.n_terms
            ):
                # Format as SSE event
                event_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming computation: {e}", exc_info=True)
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.options("/fourier-series")
async def fourier_series_sync_options():
    """Handle CORS preflight for sync endpoint"""
    from fastapi import Response
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
            "Access-Control-Max-Age": "86400",
        }
    )


@router.post("/fourier-series")
async def compute_fourier_series_sync(request: FourierSeriesRequest):
    """
    Compute Fourier series synchronously (non-streaming).

    This endpoint collects all events and returns the final result.
    Useful for testing or clients that don't support SSE.

    Returns:
        Complete computation result
    """
    logger.info(f"Received sync request: {request.function_expr}, T={request.period}, n={request.n_terms}")

    from fastapi import Response
    import json as json_module

    service = FourierSeriesServiceV2()

    # Collect all events
    events = []
    derivation_chunks = []
    final_result = None

    try:
        async for event in service.compute_with_streaming(
            function_expr=request.function_expr,
            period=request.period,
            n_terms=request.n_terms
        ):
            events.append(event)

            # Collect derivation chunks
            if event.get("type") == "derivation_chunk":
                derivation_chunks.append(event["content"])

            # Capture final result
            if event.get("type") in ["success", "success_with_warning", "failed", "max_iterations_reached"]:
                final_result = event

        # Build complete response
        if final_result:
            response_data = {
                "status": final_result["type"],
                "derivation": "".join(derivation_chunks),
                "events": events,
                **final_result.get("result", {})
            }

            # Return with explicit CORS headers
            return Response(
                content=json_module.dumps(response_data, ensure_ascii=False),
                media_type="application/json",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Computation did not complete properly")

    except Exception as e:
        logger.error(f"Error in sync computation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0",
        "message": "Fourier Series API V2 (Three-stage flow with streaming)"
    }
