"""API client for communicating with the Demo2PDF backend."""
import httpx
from pathlib import Path
from typing import Optional, Dict, Any


class BackendClient:
    """Async client for the Demo2PDF FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session_id: Optional[str] = None

    async def health_check(self) -> bool:
        """Check if backend is available."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5)
                return response.status_code == 200
        except httpx.RequestError:
            return False

    async def create_session(
        self,
        context: Optional[str] = None,
        capture_mode: str = "video"
    ) -> str:
        """
        Create a new recording session.

        Args:
            context: Description of what's being documented
            capture_mode: "video" for video recording mode

        Returns:
            Session ID
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/sessions",
                params={
                    "use_llm": True,
                    "context": context,
                    "capture_mode": capture_mode
                }
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data["session_id"]
            return self.session_id

    async def upload_video(
        self,
        video_path: Path,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a recorded video for AI analysis.

        Args:
            video_path: Path to the video file
            session_id: Session ID (uses current session if not provided)

        Returns:
            Response with generated steps
        """
        session_id = session_id or self.session_id
        if not session_id:
            raise ValueError("No session ID - create a session first")

        async with httpx.AsyncClient(timeout=300) as client:  # 5 min timeout for video
            with open(video_path, "rb") as f:
                files = {"video": (video_path.name, f, "video/quicktime")}
                response = await client.post(
                    f"{self.base_url}/api/sessions/{session_id}/video",
                    files=files
                )
            response.raise_for_status()
            return response.json()

    async def get_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get session details including generated steps."""
        session_id = session_id or self.session_id
        if not session_id:
            raise ValueError("No session ID")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/sessions/{session_id}")
            response.raise_for_status()
            return response.json()

    def get_viewer_url(self, session_id: Optional[str] = None) -> str:
        """Get URL to view the session in the web viewer."""
        session_id = session_id or self.session_id
        return f"{self.base_url}/viewer?session={session_id}"
