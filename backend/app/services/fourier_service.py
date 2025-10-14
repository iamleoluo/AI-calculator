"""
Main Fourier series service coordinating AI derivation and verification
"""
import logging
from typing import Dict, Any
import numpy as np

from app.core.ai_engine import SimpleAIEngine
from app.core.verification import VerificationEngine
from app.services.prompt_builder import PromptBuilder
from app.core.config import settings

logger = logging.getLogger(__name__)


class FourierSeriesService:
    """Main service for Fourier series computation with verification"""

    def __init__(self):
        self.ai_engine = SimpleAIEngine()
        self.verification_engine = VerificationEngine()
        self.prompt_builder = PromptBuilder()

    async def compute_with_verification(
        self, function_expr: str, period: float, n_terms: int
    ) -> Dict[str, Any]:
        """
        Compute Fourier series with iterative verification.

        Args:
            function_expr: Python expression for the function
            period: Period of the function
            n_terms: Number of terms to compute

        Returns:
            Complete result with derivation, verification, and visualization data
        """
        logger.info(
            f"Starting Fourier series computation: "
            f"f(t)={function_expr}, T={period}, n={n_terms}"
        )

        history = []

        for iteration in range(settings.MAX_ITERATIONS):
            logger.info(f"Iteration {iteration + 1}/{settings.MAX_ITERATIONS}")

            try:
                # Build prompt
                if iteration == 0:
                    prompt = self.prompt_builder.build_initial_prompt(
                        function_expr, period, n_terms
                    )
                else:
                    prompt = self.prompt_builder.build_feedback_prompt(
                        function_expr,
                        period,
                        n_terms,
                        previous_ai_coeffs,
                        numerical_coeffs,
                        verification_result["error_metrics"]["max_error"] * 100,
                    )

                # Get AI derivation
                ai_response = await self.ai_engine.derive_fourier_series(prompt)

                # Extract coefficients
                ai_coefficients = ai_response["executable_code"]["coefficients"]

                # Verify
                verification_result = self.verification_engine.verify(
                    ai_coefficients, function_expr, period, n_terms
                )

                numerical_coeffs = verification_result["numerical_coefficients"]

                # Record history
                history.append(
                    {
                        "iteration": iteration + 1,
                        "ai_coefficients": ai_coefficients,
                        "numerical_coefficients": numerical_coeffs,
                        "verification": verification_result,
                    }
                )

                # Check if verified
                if verification_result["is_verified"]:
                    logger.info(f"Verification PASSED on iteration {iteration + 1}")

                    # Generate visualization data
                    viz_data = self._generate_visualization_data(
                        function_expr, ai_coefficients, period, n_terms
                    )

                    return {
                        "success": True,
                        "iterations": iteration + 1,
                        "thinking_process": ai_response.get("thinking_process", {}),
                        "coefficients": ai_coefficients,
                        "final_result": ai_response.get("final_result", {}),
                        "verification": verification_result,
                        "visualization": viz_data,
                        "history": history,
                    }

                # Prepare for next iteration
                previous_ai_coeffs = ai_coefficients
                logger.warning(
                    f"Verification FAILED on iteration {iteration + 1} - "
                    f"Max error: {verification_result['error_metrics']['max_error']:.4f}"
                )

            except Exception as e:
                logger.error(f"Error in iteration {iteration + 1}: {e}")
                # Continue to next iteration
                continue

        # Max iterations reached without passing verification
        logger.error("Max iterations reached without successful verification")

        # Still generate visualization with the last attempt
        last_coeffs = history[-1]["ai_coefficients"] if history else None
        viz_data = None
        if last_coeffs:
            try:
                viz_data = self._generate_visualization_data(
                    function_expr, last_coeffs, period, n_terms
                )
            except Exception as e:
                logger.error(f"Failed to generate visualization: {e}")

        return {
            "success": False,
            "iterations": settings.MAX_ITERATIONS,
            "error": "達到最大迭代次數，仍無法通過驗證",
            "history": history,
            "last_verification": history[-1]["verification"] if history else None,
            "coefficients": last_coeffs,
            "visualization": viz_data,
        }

    def _generate_visualization_data(
        self, function_expr: str, coefficients: Dict[str, Any], period: float, n_terms: int
    ) -> Dict[str, Any]:
        """
        Generate data for visualization.

        Returns data for plotting original function vs Fourier reconstruction.
        """
        # Generate time points
        t_points = np.linspace(0, 2 * period, 500)

        # Compute original function
        func = self.verification_engine._create_function(function_expr)
        original_values = np.array([func(t) for t in t_points])

        # Compute Fourier reconstruction
        reconstructed_values = self.verification_engine.compute_reconstruction(
            coefficients, period, t_points
        )

        # Compute pointwise error
        pointwise_error = np.abs(original_values - reconstructed_values)

        return {
            "t_points": t_points.tolist(),
            "original_values": original_values.tolist(),
            "reconstructed_values": reconstructed_values.tolist(),
            "pointwise_error": pointwise_error.tolist(),
            "max_pointwise_error": float(np.max(pointwise_error)),
            "mean_pointwise_error": float(np.mean(pointwise_error)),
        }
