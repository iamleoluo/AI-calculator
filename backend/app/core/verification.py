"""
Numerical verification engine for validating AI-generated Fourier coefficients
"""
import numpy as np
from scipy import integrate
from typing import Dict, Any, Tuple, Callable
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class VerificationEngine:
    """Verifies AI-generated Fourier coefficients using numerical integration"""

    def __init__(self, error_threshold: float = None):
        """
        Initialize verification engine.

        Args:
            error_threshold: Maximum acceptable relative error (default from settings)
        """
        self.error_threshold = error_threshold or settings.ERROR_THRESHOLD

    def verify(
        self,
        ai_coefficients: Dict[str, Any],
        function_expr: str,
        period: float,
        n_terms: int,
    ) -> Dict[str, Any]:
        """
        Verify AI-generated coefficients against numerical computation.

        Args:
            ai_coefficients: Coefficients from AI (a0, an, bn)
            function_expr: Python expression for the function
            period: Period of the function
            n_terms: Number of terms

        Returns:
            Verification result dictionary
        """
        logger.info("Starting numerical verification")

        try:
            # Create function from expression
            func = self._create_function(function_expr)

            # Compute coefficients numerically
            numerical_coeffs = self.compute_coefficients_numerical(
                func, period, n_terms
            )

            # Compare coefficients
            errors = self._compare_coefficients(ai_coefficients, numerical_coeffs)

            # Determine if verification passed
            is_verified = errors["max_error"] < self.error_threshold

            # Generate error report if needed
            error_report = None
            if not is_verified:
                error_report = self._generate_error_report(
                    errors, ai_coefficients, numerical_coeffs
                )

            result = {
                "is_verified": is_verified,
                "error_metrics": errors,
                "numerical_coefficients": numerical_coeffs,
                "error_report": error_report,
            }

            logger.info(
                f"Verification {'PASSED' if is_verified else 'FAILED'} - "
                f"Max error: {errors['max_error']:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Verification failed with error: {e}")
            raise

    def compute_coefficients_numerical(
        self, func: Callable, period: float, n_terms: int
    ) -> Dict[str, Any]:
        """
        Compute Fourier coefficients using numerical integration.

        Args:
            func: Function to analyze
            period: Period of the function
            n_terms: Number of terms to compute

        Returns:
            Dictionary with a0, an, bn coefficients
        """
        omega0 = 2 * np.pi / period

        # Compute a0
        a0_integrand = lambda t: func(t)
        a0, _ = integrate.quad(a0_integrand, 0, period)
        a0 = (2 / period) * a0

        # Compute an and bn
        an = []
        bn = []

        for n in range(1, n_terms + 1):
            # an coefficient
            an_integrand = lambda t, n=n: func(t) * np.cos(n * omega0 * t)
            an_val, _ = integrate.quad(an_integrand, 0, period)
            an.append((2 / period) * an_val)

            # bn coefficient
            bn_integrand = lambda t, n=n: func(t) * np.sin(n * omega0 * t)
            bn_val, _ = integrate.quad(bn_integrand, 0, period)
            bn.append((2 / period) * bn_val)

        return {"a0": float(a0), "an": [float(x) for x in an], "bn": [float(x) for x in bn]}

    def compute_reconstruction(
        self, coefficients: Dict[str, Any], period: float, t_points: np.ndarray
    ) -> np.ndarray:
        """
        Reconstruct function from Fourier coefficients.

        Args:
            coefficients: Dictionary with a0, an, bn
            period: Period of the function
            t_points: Time points for evaluation

        Returns:
            Reconstructed function values
        """
        omega0 = 2 * np.pi / period
        n_terms = len(coefficients["an"])

        # Start with a0/2
        reconstruction = (coefficients["a0"] / 2) * np.ones_like(t_points)

        # Add cosine and sine terms
        for n in range(1, n_terms + 1):
            reconstruction += coefficients["an"][n - 1] * np.cos(n * omega0 * t_points)
            reconstruction += coefficients["bn"][n - 1] * np.sin(n * omega0 * t_points)

        return reconstruction

    def _create_function(self, function_expr: str) -> Callable:
        """
        Create a callable function from string expression.

        Args:
            function_expr: Python expression (e.g., "np.sin(t)")

        Returns:
            Callable function
        """
        # Create safe namespace
        safe_namespace = {
            "np": np,
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "exp": np.exp,
            "log": np.log,
            "sqrt": np.sqrt,
            "abs": np.abs,
            "pi": np.pi,
        }

        # Create function
        func_code = f"lambda t: {function_expr}"
        func = eval(func_code, safe_namespace)

        return func

    def _compare_coefficients(
        self, ai_coeffs: Dict[str, Any], numerical_coeffs: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Compare AI coefficients with numerical ones.

        Returns:
            Dictionary with error metrics
        """
        errors = []

        # Compare a0
        a0_error = self._relative_error(ai_coeffs["a0"], numerical_coeffs["a0"])
        errors.append(a0_error)

        # Compare an
        an_errors = [
            self._relative_error(ai_val, num_val)
            for ai_val, num_val in zip(ai_coeffs["an"], numerical_coeffs["an"])
        ]
        errors.extend(an_errors)

        # Compare bn
        bn_errors = [
            self._relative_error(ai_val, num_val)
            for ai_val, num_val in zip(ai_coeffs["bn"], numerical_coeffs["bn"])
        ]
        errors.extend(bn_errors)

        return {
            "a0_error": a0_error,
            "an_errors": an_errors,
            "bn_errors": bn_errors,
            "max_error": max(errors),
            "mean_error": np.mean(errors),
        }

    def _relative_error(self, ai_value: float, numerical_value: float) -> float:
        """
        Calculate relative error between AI and numerical values.

        Uses absolute error for values close to zero.
        """
        # Use absolute error for near-zero values (both values < 1e-6)
        if abs(numerical_value) < 1e-6 and abs(ai_value) < 1e-6:
            # Both are essentially zero, treat as match
            return abs(ai_value - numerical_value)
        elif abs(numerical_value) < 1e-6:
            # Numerical value is zero but AI value isn't - use absolute error
            return abs(ai_value - numerical_value)
        else:
            # Use relative error for significant values
            return abs(ai_value - numerical_value) / abs(numerical_value)

    def _generate_error_report(
        self,
        errors: Dict[str, Any],
        ai_coeffs: Dict[str, Any],
        numerical_coeffs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate detailed error report for feedback"""
        # Find problematic terms
        problematic_terms = []

        if errors["a0_error"] > self.error_threshold:
            problematic_terms.append(
                {
                    "term": "a0",
                    "ai_value": ai_coeffs["a0"],
                    "correct_value": numerical_coeffs["a0"],
                    "error": errors["a0_error"],
                }
            )

        for n, (an_error, ai_val, num_val) in enumerate(
            zip(errors["an_errors"], ai_coeffs["an"], numerical_coeffs["an"]), 1
        ):
            if an_error > self.error_threshold:
                problematic_terms.append(
                    {
                        "term": f"a{n}",
                        "ai_value": ai_val,
                        "correct_value": num_val,
                        "error": an_error,
                    }
                )

        for n, (bn_error, ai_val, num_val) in enumerate(
            zip(errors["bn_errors"], ai_coeffs["bn"], numerical_coeffs["bn"]), 1
        ):
            if bn_error > self.error_threshold:
                problematic_terms.append(
                    {
                        "term": f"b{n}",
                        "ai_value": ai_val,
                        "correct_value": num_val,
                        "error": bn_error,
                    }
                )

        return {
            "summary": f"驗證失敗：最大誤差 {errors['max_error']:.2%}",
            "problematic_terms": problematic_terms,
            "suggestions": [
                "檢查積分邊界是否正確",
                "確認傅立葉係數公式",
                "注意 a₀ 的係數是 2/T",
                "檢查是否正確使用了週期 T",
            ],
        }
