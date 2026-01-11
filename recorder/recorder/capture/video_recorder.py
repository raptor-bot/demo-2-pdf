"""
Native macOS screen recording using ffmpeg.
Records the screen to a video file, similar to QuickTime or Loom.
"""
import subprocess
import signal
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import shutil


class VideoRecorder:
    """
    Records screen video using ffmpeg with AVFoundation.

    This approach:
    - Uses ffmpeg which is reliable and scriptable
    - Captures via AVFoundation (macOS native)
    - Can be stopped programmatically
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_recording: Optional[Path] = None
        self.process: Optional[subprocess.Popen] = None
        self.is_recording = False

        # Check if ffmpeg is available
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ffmpeg not found. Install with: brew install ffmpeg"
            )

    def _get_screen_device(self) -> str:
        """Get the AVFoundation screen capture device index."""
        # List devices to find screen capture
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            text=True
        )
        # Screen is typically device 1 for video, but we use "1:none" for screen only
        return "1"

    def start_recording(self, filename: Optional[str] = None) -> Path:
        """
        Start recording the screen.

        Args:
            filename: Optional filename, defaults to timestamp-based name

        Returns:
            Path to the output video file
        """
        if self.is_recording:
            raise RuntimeError("Already recording")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.mp4"

        self.current_recording = self.output_dir / filename

        # Use ffmpeg with AVFoundation for screen capture
        # -f avfoundation: use macOS AVFoundation
        # -i "1:none": capture screen (device 1), no audio
        # -r 30: 30 fps
        # -pix_fmt yuv420p: compatible pixel format
        cmd = [
            "ffmpeg",
            "-f", "avfoundation",
            "-framerate", "30",
            "-i", "1:none",  # Screen capture, no audio
            "-c:v", "libx264",
            "-preset", "ultrafast",  # Fast encoding for real-time
            "-pix_fmt", "yuv420p",
            "-y",  # Overwrite output
            str(self.current_recording)
        ]

        # Start recording process
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.is_recording = True

        return self.current_recording

    def stop_recording(self) -> Optional[Path]:
        """
        Stop the current recording.

        Returns:
            Path to the recorded video file, or None if not recording
        """
        if not self.is_recording or self.process is None:
            return None

        # Send 'q' to ffmpeg to stop gracefully
        try:
            self.process.stdin.write(b'q')
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

        try:
            # Wait for process to finish
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if needed
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

        self.is_recording = False
        recording_path = self.current_recording
        self.current_recording = None
        self.process = None

        # Verify file was created
        if recording_path and recording_path.exists() and recording_path.stat().st_size > 0:
            return recording_path
        return None

    def get_recording_duration(self) -> Optional[float]:
        """Get duration of current or last recording in seconds."""
        path = self.current_recording or self.last_recording
        if path and path.exists():
            try:
                result = subprocess.run(
                    [
                        "ffprobe", "-v", "quiet",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(path)
                    ],
                    capture_output=True,
                    text=True
                )
                return float(result.stdout.strip())
            except (subprocess.CalledProcessError, ValueError):
                return None
        return None
