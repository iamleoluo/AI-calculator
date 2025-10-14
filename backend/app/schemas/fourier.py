"""
Pydantic schemas for Fourier series API
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class FourierRequest(BaseModel):
    """Request schema for Fourier series computation"""

    function_expr: str = Field(
        ...,
        description="Python expression for the function (e.g., 'np.sin(t)', 't**2')",
        examples=["np.sin(t)", "np.cos(2*t)", "t**2"],
    )
    period: float = Field(
        ..., gt=0, description="Period of the function", examples=[6.283185, 2.0]
    )
    n_terms: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of Fourier terms to compute",
        examples=[5, 10],
    )


class CoefficientsResponse(BaseModel):
    """Fourier coefficients"""

    a0: float
    an: List[float]
    bn: List[float]


class VerificationResponse(BaseModel):
    """Verification results"""

    is_verified: bool
    max_error: float
    mean_error: float
    numerical_coefficients: CoefficientsResponse


class VisualizationData(BaseModel):
    """Data for visualization"""

    t_points: List[float]
    original_values: List[float]
    reconstructed_values: List[float]
    pointwise_error: List[float]
    max_pointwise_error: float
    mean_pointwise_error: float


class FourierResponse(BaseModel):
    """Response schema for Fourier series computation"""

    success: bool
    iterations: int
    thinking_process: Optional[Dict[str, Any]] = None
    coefficients: Optional[CoefficientsResponse] = None
    final_result: Optional[Dict[str, Any]] = None
    verification: Optional[VerificationResponse] = None
    visualization: Optional[VisualizationData] = None
    error: Optional[str] = None
