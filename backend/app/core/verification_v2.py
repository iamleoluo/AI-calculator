"""
Refactored Verification Engine for function-level numerical comparison
"""
import numpy as np
from typing import Dict, Any, Callable
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class VerificationEngineV2:
    """
    Verifies AI-generated functions by numerical comparison.

    Instead of comparing coefficients, this engine executes both
    the original function and the Fourier reconstruction function,
    then compares their outputs at multiple test points.
    """

    def __init__(self, error_threshold: float = None):
        """
        Initialize verification engine.

        Args:
            error_threshold: Maximum acceptable relative error (default from settings)
        """
        self.error_threshold = error_threshold or settings.ERROR_THRESHOLD
        logger.info(f"VerificationEngineV2 initialized with threshold: {self.error_threshold}")

    def verify_coefficients(
        self,
        original_function_code: str,
        coefficients: Dict[str, Any],
        period: float,
        test_periods: int = 2,
        test_points: int = 500
    ) -> Dict[str, Any]:
        """
        Verify Fourier coefficients by comparing original function with reconstruction.

        This method generates the reconstruction function from coefficients and verifies
        it against the original function.

        Args:
            original_function_code: Complete Python code for original function
            coefficients: Dictionary with a0, an, bn
            period: Period of the function
            test_periods: Number of periods to test (default: 2)
            test_points: Number of test points (default: 500)

        Returns:
            Verification result dictionary with error metrics and visualization data
        """
        logger.info("Starting coefficient-based verification")

        try:
            # Execute original function code
            f_original = self._execute_function_code(
                original_function_code,
                expected_function_name="f"
            )

            # Extract coefficients
            a0 = float(coefficients["a0"])
            an = [float(a) for a in coefficients["an"]]
            bn = [float(b) for b in coefficients["bn"]]

            # Generate reconstruction function
            omega0 = 2 * np.pi / period
            n_terms = len(an)

            def reconstruct(t):
                """Generated Fourier reconstruction function"""
                result = a0 / 2.0
                for n in range(1, n_terms + 1):
                    result += an[n-1] * np.cos(n * omega0 * t)
                    result += bn[n-1] * np.sin(n * omega0 * t)
                return result

            # Generate test points
            t_points = np.linspace(0, test_periods * period, test_points)

            # Compute function values
            try:
                original_values = np.array([f_original(t) for t in t_points])
                reconstruction_values = np.array([reconstruct(t) for t in t_points])
            except Exception as e:
                logger.error(f"Error computing function values: {e}")
                return {
                    "is_verified": False,
                    "error_type": "code_execution_error",
                    "error_message": f"Error evaluating functions: {str(e)}"
                }

            # Compute errors
            error_metrics = self._compute_error_metrics(
                original_values,
                reconstruction_values,
                t_points
            )

            # Check if verified
            is_verified = error_metrics["max_relative_error"] < self.error_threshold

            result = {
                "is_verified": is_verified,
                "error_metrics": error_metrics,
                "coefficients": {"a0": a0, "an": an, "bn": bn},
                "test_points": t_points.tolist(),
                "original_values": original_values.tolist(),
                "reconstructed_values": reconstruction_values.tolist(),
                "pointwise_errors": error_metrics["pointwise_absolute_errors"]
            }

            logger.info(
                f"Verification {'PASSED' if is_verified else 'FAILED'} - "
                f"Max relative error: {error_metrics['max_relative_error']:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Verification failed with exception: {e}")
            return {
                "is_verified": False,
                "error_type": "verification_exception",
                "error_message": str(e)
            }

    def verify_functions(
        self,
        original_function_code: str,
        reconstruction_function_code: str,
        period: float,
        test_periods: int = 2,
        test_points: int = 500
    ) -> Dict[str, Any]:
        """
        Verify AI-generated functions by numerical comparison.

        Args:
            original_function_code: Complete Python code for original function
            reconstruction_function_code: Complete Python code for Fourier reconstruction
            period: Period of the function
            test_periods: Number of periods to test (default: 2)
            test_points: Number of test points (default: 500)

        Returns:
            Verification result dictionary with error metrics and visualization data
        """
        logger.info("Starting function-level verification")

        try:
            # Execute codes and get functions
            f_original = self._execute_function_code(
                original_function_code,
                expected_function_name="f"
            )
            f_reconstruction = self._execute_function_code(
                reconstruction_function_code,
                expected_function_name="reconstruct"
            )

            # Generate test points
            t_points = np.linspace(0, test_periods * period, test_points)

            # Compute function values
            try:
                original_values = np.array([f_original(t) for t in t_points])
                reconstruction_values = np.array([f_reconstruction(t) for t in t_points])
            except Exception as e:
                logger.error(f"Error computing function values: {e}")
                return {
                    "is_verified": False,
                    "error_type": "code_execution_error",
                    "error_message": f"Error evaluating functions: {str(e)}"
                }

            # Compute errors
            error_metrics = self._compute_error_metrics(
                original_values,
                reconstruction_values,
                t_points
            )

            # Check if verified
            is_verified = error_metrics["max_relative_error"] < self.error_threshold

            result = {
                "is_verified": is_verified,
                "error_metrics": error_metrics,
                "test_points": t_points.tolist(),
                "original_values": original_values.tolist(),
                "reconstructed_values": reconstruction_values.tolist(),
                "pointwise_errors": error_metrics["pointwise_absolute_errors"]
            }

            logger.info(
                f"Verification {'PASSED' if is_verified else 'FAILED'} - "
                f"Max relative error: {error_metrics['max_relative_error']:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Verification failed with exception: {e}")
            return {
                "is_verified": False,
                "error_type": "verification_exception",
                "error_message": str(e)
            }

    def _execute_function_code(
        self,
        code: str,
        expected_function_name: str
    ) -> Callable:
        """
        Execute Python code and extract the function.

        Args:
            code: Complete Python code including imports
            expected_function_name: Name of the function to extract

        Returns:
            Callable function

        Raises:
            ValueError: If code cannot be executed or function not found
        """
        # Create safe namespace
        namespace = {
            "__builtins__": __builtins__,
        }

        try:
            # Execute code
            exec(code, namespace)

            # Extract function
            if expected_function_name not in namespace:
                raise ValueError(
                    f"Function '{expected_function_name}' not found in executed code. "
                    f"Available: {[k for k in namespace.keys() if not k.startswith('_')]}"
                )

            func = namespace[expected_function_name]

            if not callable(func):
                raise ValueError(f"'{expected_function_name}' is not callable")

            return func

        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            raise ValueError(f"Syntax error in generated code: {e}")
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            raise ValueError(f"Error executing code: {e}")

    def _compute_error_metrics(
        self,
        original_values: np.ndarray,
        reconstruction_values: np.ndarray,
        t_points: np.ndarray
    ) -> Dict[str, Any]:
        """
        Compute comprehensive error metrics.

        Args:
            original_values: Values from original function
            reconstruction_values: Values from reconstruction function
            t_points: Time points

        Returns:
            Dictionary with various error metrics
        """
        # Absolute errors
        absolute_errors = np.abs(original_values - reconstruction_values)

        # Relative errors (handle division by zero with safe threshold)
        # Use 1e-6 threshold instead of 1e-10 to avoid numerical precision issues
        zero_threshold = 1e-6

        # Calculate relative errors safely
        with np.errstate(divide='ignore', invalid='ignore'):
            relative_errors = np.where(
                np.abs(original_values) > zero_threshold,
                absolute_errors / np.abs(original_values),
                absolute_errors  # Use absolute error when original value is near zero
            )

        # Handle any inf or nan values that might have appeared
        relative_errors = np.nan_to_num(relative_errors, nan=0.0, posinf=0.0, neginf=0.0)

        # Find maximum error location
        max_error_idx = np.argmax(absolute_errors)

        # Detect error pattern
        error_pattern = self._detect_error_pattern(absolute_errors, original_values)

        metrics = {
            "max_relative_error": float(np.max(relative_errors)),
            "mean_relative_error": float(np.mean(relative_errors)),
            "max_absolute_error": float(np.max(absolute_errors)),
            "mean_absolute_error": float(np.mean(absolute_errors)),
            "max_error_location": float(t_points[max_error_idx]),
            "max_error_original_value": float(original_values[max_error_idx]),
            "max_error_reconstruction_value": float(reconstruction_values[max_error_idx]),
            "pointwise_absolute_errors": absolute_errors.tolist(),
            "error_pattern": error_pattern
        }

        return metrics

    def _detect_error_pattern(
        self,
        absolute_errors: np.ndarray,
        original_values: np.ndarray
    ) -> str:
        """
        Detect the pattern of errors to help identify the cause.

        Args:
            absolute_errors: Array of absolute errors
            original_values: Original function values

        Returns:
            Error pattern description
        """
        mean_error = np.mean(absolute_errors)
        max_error = np.max(absolute_errors)
        std_error = np.std(absolute_errors)

        # Check for uniform errors (all errors similar)
        if std_error < 0.1 * mean_error:
            return "uniform"  # Likely precision or insufficient terms

        # Check for peak errors (few large errors, most small)
        if max_error > 3 * mean_error:
            # Check if original function has discontinuities
            original_diff = np.diff(original_values)
            if np.any(np.abs(original_diff) > 2 * np.std(original_diff)):
                return "peak_at_discontinuities"  # Likely Gibbs phenomenon
            else:
                return "peak"  # Isolated large errors

        # Check for systematic errors (gradual increase/decrease)
        if len(absolute_errors) > 10:
            # Simple trend detection
            first_half_mean = np.mean(absolute_errors[:len(absolute_errors)//2])
            second_half_mean = np.mean(absolute_errors[len(absolute_errors)//2:])
            if abs(second_half_mean - first_half_mean) > 0.5 * mean_error:
                return "systematic"  # Gradual drift

        return "mixed"  # Complex error pattern
