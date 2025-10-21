"""
Session manager for storing computation sessions in filesystem
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages computation sessions using filesystem storage.

    Each session creates a directory structure:
    sessions/
    └── session_{timestamp}_{id}/
        ├── metadata.json
        ├── user_input.json
        ├── iteration_1/
        │   ├── prompt_1.txt
        │   ├── response_1.md
        │   ├── prompt_2.txt
        │   ├── response_2.json
        │   ├── verification.json
        │   └── error_analysis.json (if failed)
        └── final_result.json (if successful)
    """

    def __init__(self, base_dir: str = None):
        """
        Initialize session manager.

        Args:
            base_dir: Base directory for storing sessions (relative to backend root)
                     If None, uses /tmp/sessions for serverless environments
        """
        if base_dir is None:
            # Use /tmp for serverless environments (e.g., Vercel, AWS Lambda)
            import os
            if os.path.exists('/tmp'):
                base_dir = "/tmp/sessions"
            else:
                base_dir = "sessions"

        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"SessionManager initialized with base_dir: {self.base_dir.absolute()}")

    def create_session(self, user_input: Dict[str, Any]) -> str:
        """
        Create a new session.

        Args:
            user_input: Dictionary with function_expr, period, n_terms

        Returns:
            session_id: Unique session identifier
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        session_id = f"session_{timestamp}_{unique_id}"

        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "status": "running"
        }
        self._save_json(session_dir / "metadata.json", metadata)

        # Save user input
        self._save_json(session_dir / "user_input.json", user_input)

        logger.info(f"Created session: {session_id}")
        return session_id

    def save_iteration_data(
        self,
        session_id: str,
        iteration: int,
        data_type: str,
        content: Any
    ):
        """
        Save data for a specific iteration.

        Args:
            session_id: Session identifier
            iteration: Iteration number (1-indexed)
            data_type: Type of data (prompt_1, response_1, prompt_2, response_2,
                       verification, error_analysis, prompt_3, response_3)
            content: Content to save (string, dict, or list)
        """
        session_dir = self.base_dir / session_id
        iteration_dir = session_dir / f"iteration_{iteration}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        # Determine file extension and save method
        if data_type in ["prompt_1", "prompt_2", "prompt_3"]:
            file_path = iteration_dir / f"{data_type}.txt"
            self._save_text(file_path, content)
        elif data_type == "response_1":
            file_path = iteration_dir / "response_1.md"
            self._save_text(file_path, content)
        elif data_type in ["response_2", "response_3", "verification", "error_analysis"]:
            file_path = iteration_dir / f"{data_type}.json"
            self._save_json(file_path, content)
        else:
            raise ValueError(f"Unknown data_type: {data_type}")

        logger.debug(f"Saved {data_type} for session {session_id}, iteration {iteration}")

    def save_final_result(self, session_id: str, result: Dict[str, Any]):
        """
        Save final successful result.

        Args:
            session_id: Session identifier
            result: Final result dictionary
        """
        session_dir = self.base_dir / session_id
        self._save_json(session_dir / "final_result.json", result)

        # Update metadata
        metadata_path = session_dir / "metadata.json"
        metadata = self._load_json(metadata_path)
        metadata["status"] = "completed"
        metadata["completed_at"] = datetime.now().isoformat()
        self._save_json(metadata_path, metadata)

        logger.info(f"Saved final result for session {session_id}")

    def mark_session_failed(self, session_id: str, reason: str):
        """
        Mark session as failed.

        Args:
            session_id: Session identifier
            reason: Failure reason
        """
        session_dir = self.base_dir / session_id
        metadata_path = session_dir / "metadata.json"
        metadata = self._load_json(metadata_path)
        metadata["status"] = "failed"
        metadata["failed_at"] = datetime.now().isoformat()
        metadata["failure_reason"] = reason
        self._save_json(metadata_path, metadata)

        logger.warning(f"Session {session_id} marked as failed: {reason}")

    def load_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Load complete session context (for AI analysis).

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with all session data
        """
        session_dir = self.base_dir / session_id

        if not session_dir.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        context = {
            "session_id": session_id,
            "metadata": self._load_json(session_dir / "metadata.json"),
            "user_input": self._load_json(session_dir / "user_input.json"),
            "iterations": []
        }

        # Load all iterations
        for iteration_dir in sorted(session_dir.glob("iteration_*")):
            iteration_num = int(iteration_dir.name.split("_")[1])
            iteration_data = {
                "iteration": iteration_num,
                "files": {}
            }

            # Load all files in iteration
            for file_path in iteration_dir.iterdir():
                file_type = file_path.stem
                if file_path.suffix == ".json":
                    iteration_data["files"][file_type] = self._load_json(file_path)
                else:
                    iteration_data["files"][file_type] = self._load_text(file_path)

            context["iterations"].append(iteration_data)

        # Load final result if exists
        final_result_path = session_dir / "final_result.json"
        if final_result_path.exists():
            context["final_result"] = self._load_json(final_result_path)

        return context

    def get_latest_iteration_data(
        self,
        session_id: str,
        data_type: str
    ) -> Optional[Any]:
        """
        Get data from the latest iteration.

        Args:
            session_id: Session identifier
            data_type: Type of data to retrieve

        Returns:
            Data content or None if not found
        """
        session_dir = self.base_dir / session_id
        iteration_dirs = sorted(session_dir.glob("iteration_*"))

        if not iteration_dirs:
            return None

        latest_iteration = iteration_dirs[-1]

        # Try different file extensions
        for ext in [".txt", ".md", ".json"]:
            file_path = latest_iteration / f"{data_type}{ext}"
            if file_path.exists():
                if ext == ".json":
                    return self._load_json(file_path)
                else:
                    return self._load_text(file_path)

        return None

    def _save_text(self, file_path: Path, content: str):
        """Save text content to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _save_json(self, file_path: Path, content: Any):
        """Save JSON content to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

    def _load_text(self, file_path: Path) -> str:
        """Load text content from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_json(self, file_path: Path) -> Any:
        """Load JSON content from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def cleanup_old_sessions(self, days: int = 7):
        """
        Clean up sessions older than specified days.

        Args:
            days: Number of days to keep sessions
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cleaned = 0

        for session_dir in self.base_dir.iterdir():
            if session_dir.is_dir():
                if session_dir.stat().st_mtime < cutoff_time:
                    import shutil
                    shutil.rmtree(session_dir)
                    cleaned += 1
                    logger.info(f"Cleaned up old session: {session_dir.name}")

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old sessions")
