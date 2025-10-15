"""
Refactored Fourier Series Service with three-stage computation flow
"""
import logging
from typing import Dict, Any, AsyncIterator

from app.core.session_manager import SessionManager
from app.core.ai_engine_v2 import AIEngineV2
from app.core.verification_v2 import VerificationEngineV2
from app.services.prompt_builder_v2 import PromptBuilderV2
from app.core.config import settings

logger = logging.getLogger(__name__)


class FourierSeriesServiceV2:
    """
    Main service for Fourier series computation with three-stage flow:
    1. Derivation (streaming Markdown)
    2. Code Translation (executable Python)
    3. Verification + Error Analysis
    """

    def __init__(self):
        self.session_manager = SessionManager()
        self.ai_engine = AIEngineV2()
        self.verification_engine = VerificationEngineV2()
        self.prompt_builder = PromptBuilderV2()
        logger.info("FourierSeriesServiceV2 initialized")

    async def compute_with_streaming(
        self,
        function_expr: str,
        period: float,
        n_terms: int
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Compute Fourier series with streaming output.

        This is an async generator that yields events:
        - {"type": "session_created", "session_id": "..."}
        - {"type": "derivation_chunk", "content": "..."}
        - {"type": "derivation_complete", "full_text": "..."}
        - {"type": "code_generated", "code": {...}}
        - {"type": "verification_result", "result": {...}}
        - {"type": "error_analysis", "analysis": {...}}
        - {"type": "success", "result": {...}}
        - {"type": "failed", "reason": "..."}

        Args:
            function_expr: Python expression for the function
            period: Period of the function
            n_terms: Number of terms to compute

        Yields:
            Event dictionaries
        """
        # Create session
        user_input = {
            "function_expr": function_expr,
            "period": period,
            "n_terms": n_terms
        }
        session_id = self.session_manager.create_session(user_input)

        yield {
            "type": "session_created",
            "session_id": session_id
        }

        logger.info(f"Starting computation for session {session_id}")

        # Iteration loop
        retry_hint = None
        previous_derivation = None  # For code-only retries

        for iteration in range(1, settings.MAX_ITERATIONS + 1):
            logger.info(f"=== Iteration {iteration}/{settings.MAX_ITERATIONS} ===")

            yield {
                "type": "iteration_start",
                "iteration": iteration
            }

            try:
                # === STAGE 1: Derivation (or skip if code-only retry) ===
                if previous_derivation is None:
                    # Build Prompt 1
                    prompt_1 = self.prompt_builder.build_derivation_prompt(
                        function_expr=function_expr,
                        period=period,
                        n_terms=n_terms,
                        retry_hint=retry_hint
                    )

                    self.session_manager.save_iteration_data(
                        session_id, iteration, "prompt_1", prompt_1
                    )

                    # Stream derivation
                    derivation_chunks = []
                    async for chunk in self.ai_engine.stream_derivation(prompt_1):
                        derivation_chunks.append(chunk)
                        yield {
                            "type": "derivation_chunk",
                            "content": chunk,
                            "iteration": iteration
                        }

                    derivation_markdown = "".join(derivation_chunks)

                    self.session_manager.save_iteration_data(
                        session_id, iteration, "response_1", derivation_markdown
                    )

                    yield {
                        "type": "derivation_complete",
                        "full_text": derivation_markdown,
                        "iteration": iteration
                    }

                    logger.info(f"Derivation complete ({len(derivation_markdown)} chars)")
                else:
                    # Reuse previous derivation (code-only retry)
                    derivation_markdown = previous_derivation
                    logger.info("Reusing previous derivation for code-only retry")

                # === STAGE 2: Code Translation ===
                prompt_2 = self.prompt_builder.build_code_translation_prompt(
                    derivation_markdown=derivation_markdown,
                    function_expr=function_expr,
                    period=period,
                    n_terms=n_terms
                )

                self.session_manager.save_iteration_data(
                    session_id, iteration, "prompt_2", prompt_2
                )

                code_response = await self.ai_engine.translate_to_code(prompt_2)

                self.session_manager.save_iteration_data(
                    session_id, iteration, "response_2", code_response
                )

                yield {
                    "type": "code_generated",
                    "code": code_response,
                    "iteration": iteration
                }

                logger.info("Code translation complete")

                # === STAGE 3: Verification ===
                verification_result = self.verification_engine.verify_functions(
                    original_function_code=code_response["original_function"],
                    reconstruction_function_code=code_response["fourier_reconstruction"],
                    period=period
                )

                self.session_manager.save_iteration_data(
                    session_id, iteration, "verification", verification_result
                )

                yield {
                    "type": "verification_result",
                    "result": verification_result,
                    "iteration": iteration
                }

                # === Check Verification Result ===
                if verification_result["is_verified"]:
                    # ✅ SUCCESS!
                    logger.info(f"✅ Verification PASSED on iteration {iteration}")

                    # Prepare visualization data
                    visualization_data = {
                        "t_points": verification_result.get("test_points", []),
                        "original_values": verification_result.get("original_values", []),
                        "reconstructed_values": verification_result.get("reconstructed_values", []),
                        "pointwise_errors": verification_result.get("pointwise_errors", []),
                        "max_pointwise_error": verification_result.get("error_metrics", {}).get("max_absolute_error", 0)
                    }

                    final_result = {
                        "session_id": session_id,
                        "success": True,
                        "iterations": iteration,
                        "derivation": derivation_markdown,
                        "code": code_response,
                        "verification": verification_result,
                        "visualization": visualization_data
                    }

                    self.session_manager.save_final_result(session_id, final_result)

                    yield {
                        "type": "success",
                        "result": final_result
                    }

                    return  # Stop iteration

                # ❌ Verification failed - analyze error
                logger.warning(f"❌ Verification FAILED on iteration {iteration}")

                # === STAGE 4: Error Analysis (Prompt 3) ===
                prompt_3 = self.prompt_builder.build_error_analysis_prompt(
                    derivation_markdown=derivation_markdown,
                    code_response=code_response,
                    verification_result=verification_result,
                    function_expr=function_expr,
                    period=period,
                    n_terms=n_terms
                )

                self.session_manager.save_iteration_data(
                    session_id, iteration, "prompt_3", prompt_3
                )

                error_analysis = await self.ai_engine.analyze_error(prompt_3)

                self.session_manager.save_iteration_data(
                    session_id, iteration, "error_analysis", error_analysis
                )

                yield {
                    "type": "error_analysis",
                    "analysis": error_analysis,
                    "iteration": iteration
                }

                logger.info(f"Error analysis: {error_analysis['error_category']} / {error_analysis['severity']}")

                # === Decision Based on Error Analysis ===
                if error_analysis.get("auto_stop", False):
                    # AI decided to stop (e.g., Gibbs phenomenon)
                    logger.info("Auto-stop triggered by error analysis")

                    # Prepare visualization data even for acceptable errors
                    visualization_data = {
                        "t_points": verification_result.get("test_points", []),
                        "original_values": verification_result.get("original_values", []),
                        "reconstructed_values": verification_result.get("reconstructed_values", []),
                        "pointwise_errors": verification_result.get("pointwise_errors", []),
                        "max_pointwise_error": verification_result.get("error_metrics", {}).get("max_absolute_error", 0)
                    }

                    final_result = {
                        "session_id": session_id,
                        "success": False,
                        "status": "acceptable_error",
                        "iterations": iteration,
                        "derivation": derivation_markdown,
                        "code": code_response,
                        "verification": verification_result,
                        "error_analysis": error_analysis,
                        "visualization": visualization_data
                    }

                    self.session_manager.save_final_result(session_id, final_result)

                    yield {
                        "type": "success_with_warning",
                        "result": final_result
                    }

                    return  # Stop iteration

                if not error_analysis.get("need_recalculation", False):
                    # Don't recalculate but also not auto-stop
                    logger.error("Error analysis says no recalculation needed but also no auto-stop")

                    self.session_manager.mark_session_failed(
                        session_id,
                        "Error analysis inconclusive"
                    )

                    yield {
                        "type": "failed",
                        "reason": "Error analysis inconclusive",
                        "error_analysis": error_analysis
                    }

                    return

                # === Prepare for Next Iteration ===
                recalc_target = error_analysis.get("recalculation_target")

                if recalc_target == "code_only":
                    # Keep derivation, only regenerate code
                    previous_derivation = derivation_markdown
                    retry_hint = error_analysis.get("suggestion_to_ai")
                    logger.info("Next iteration: code-only retry")

                elif recalc_target == "derivation":
                    # Full retry with hint
                    previous_derivation = None
                    retry_hint = error_analysis.get("suggestion_to_ai")
                    logger.info("Next iteration: full derivation retry")

                else:
                    # Default: full retry
                    previous_derivation = None
                    retry_hint = error_analysis.get("suggestion_to_ai")
                    logger.info("Next iteration: full retry (default)")

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}", exc_info=True)

                yield {
                    "type": "iteration_error",
                    "iteration": iteration,
                    "error": str(e)
                }

                # Continue to next iteration
                continue

        # === Max Iterations Reached ===
        logger.error(f"Max iterations ({settings.MAX_ITERATIONS}) reached without success")

        self.session_manager.mark_session_failed(
            session_id,
            f"Max iterations ({settings.MAX_ITERATIONS}) reached"
        )

        yield {
            "type": "max_iterations_reached",
            "session_id": session_id,
            "iterations": settings.MAX_ITERATIONS
        }
