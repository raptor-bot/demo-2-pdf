"""Configuration for the video recorder"""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RecorderConfig:
    backend_url: str = "http://localhost:8000"
    recordings_dir: Path = Path.home() / "Movies" / "Demo2PDF"
    video_quality: str = "high"  # "low", "medium", "high"

    @classmethod
    def from_env(cls) -> "RecorderConfig":
        return cls(
            backend_url=os.getenv("RECORDER_BACKEND_URL", "http://localhost:8000"),
            recordings_dir=Path(os.getenv("RECORDER_OUTPUT_DIR", str(Path.home() / "Movies" / "Demo2PDF"))),
        )

    def ensure_dirs(self):
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
