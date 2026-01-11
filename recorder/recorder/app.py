"""
Demo2PDF Menu Bar App - Loom-like screen recorder with AI analysis.

Usage:
    python -m recorder.app

The app appears in your menu bar. Click to:
    - Start Recording: Begin capturing your screen
    - Stop Recording: End capture and upload for AI analysis
    - View Session: Open the web viewer with generated steps
"""
import rumps
import asyncio
import webbrowser
import threading
import traceback
from pathlib import Path

from .config import RecorderConfig
from .capture import VideoRecorder
from .api import BackendClient


class Demo2PDFApp(rumps.App):
    """Menu bar app for screen recording and documentation generation."""

    def __init__(self):
        super().__init__(
            "Demo2PDF",
            icon=None,
            title="📹",
            quit_button=None
        )

        self.config = RecorderConfig.from_env()
        self.config.ensure_dirs()

        self.recorder = None
        self.client = BackendClient(self.config.backend_url)

        self.session_id = None
        self.last_recording: Path = None

        # Build menu
        self.menu = [
            rumps.MenuItem("Start Recording", callback=self.start_recording),
            rumps.MenuItem("Stop Recording", callback=self.stop_recording),
            None,
            rumps.MenuItem("View Session", callback=self.view_session),
            rumps.MenuItem("Open Recordings Folder", callback=self.open_folder),
            None,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]

        # Set initial state
        self._reset_to_idle()

    def _reset_to_idle(self):
        """Reset UI to idle state."""
        self.title = "📹"
        self.menu["Start Recording"].set_callback(self.start_recording)
        self.menu["Stop Recording"].set_callback(None)

    def _set_recording_state(self):
        """Set UI to recording state."""
        self.title = "🔴"
        self.menu["Start Recording"].set_callback(None)
        self.menu["Stop Recording"].set_callback(self.stop_recording)

    def _set_processing_state(self):
        """Set UI to processing state."""
        self.title = "⏳"
        self.menu["Start Recording"].set_callback(None)
        self.menu["Stop Recording"].set_callback(None)

    def _set_complete_state(self):
        """Set UI to complete state."""
        self.title = "✅"
        self.menu["Start Recording"].set_callback(self.start_recording)
        self.menu["Stop Recording"].set_callback(None)
        self.menu["View Session"].set_callback(self.view_session)

    def start_recording(self, _):
        """Start screen recording."""
        try:
            # Initialize recorder (checks for ffmpeg)
            try:
                self.recorder = VideoRecorder(self.config.recordings_dir)
            except RuntimeError as e:
                rumps.alert("Missing Dependency", str(e))
                return

            # Create session
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                if not loop.run_until_complete(self.client.health_check()):
                    rumps.alert(
                        "Backend Unavailable",
                        "Start the backend first:\n\ncd backend && python main.py"
                    )
                    return

                self.session_id = loop.run_until_complete(
                    self.client.create_session(
                        context="User workflow documentation",
                        capture_mode="video"
                    )
                )
            finally:
                loop.close()

            # Start recording
            self.last_recording = self.recorder.start_recording()
            self._set_recording_state()

            rumps.notification(
                "Recording Started",
                "Demo2PDF",
                "Recording your screen. Click Stop when done."
            )

        except Exception as e:
            rumps.alert("Error", f"Failed to start: {e}")
            traceback.print_exc()
            self._reset_to_idle()

    def stop_recording(self, _):
        """Stop recording and upload for AI analysis."""
        if not self.recorder or not self.recorder.is_recording:
            rumps.alert("Not Recording", "No active recording to stop.")
            self._reset_to_idle()
            return

        try:
            # Stop recording
            video_path = self.recorder.stop_recording()

            if not video_path or not video_path.exists():
                rumps.alert("Error", "Recording failed - no video file created.")
                self._reset_to_idle()
                return

            self._set_processing_state()

            rumps.notification(
                "Processing...",
                "Demo2PDF",
                "Uploading video for AI analysis..."
            )

            # Upload in background
            def upload_and_notify():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    result = loop.run_until_complete(
                        self.client.upload_video(video_path, self.session_id)
                    )

                    step_count = result.get("step_count", 0)

                    rumps.notification(
                        "Analysis Complete!",
                        "Demo2PDF",
                        f"Generated {step_count} steps."
                    )
                    self._set_complete_state()

                except Exception as e:
                    rumps.notification(
                        "Upload Failed",
                        "Demo2PDF",
                        f"Error: {str(e)[:80]}"
                    )
                    traceback.print_exc()
                    self._reset_to_idle()
                finally:
                    loop.close()

            thread = threading.Thread(target=upload_and_notify, daemon=True)
            thread.start()

        except Exception as e:
            rumps.alert("Error", f"Failed to stop: {e}")
            traceback.print_exc()
            self._reset_to_idle()

    def view_session(self, _):
        """Open the session in the web viewer."""
        if self.session_id:
            url = self.client.get_viewer_url(self.session_id)
            webbrowser.open(url)
        else:
            rumps.alert("No Session", "Record something first!")

    def open_folder(self, _):
        """Open the recordings folder in Finder."""
        import subprocess
        subprocess.run(["open", str(self.config.recordings_dir)])

    def quit_app(self, _):
        """Clean quit."""
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop_recording()
        rumps.quit_application()


def main():
    """Run the menu bar app."""
    app = Demo2PDFApp()
    app.run()


if __name__ == "__main__":
    main()
