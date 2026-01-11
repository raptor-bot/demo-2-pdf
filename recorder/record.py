#!/usr/bin/env python3
"""
Upload a screen recording for AI analysis.

Usage:
    python record.py                    # Interactive mode - guides you through recording
    python record.py /path/to/video.mov # Upload an existing video file
"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path
from datetime import datetime

import httpx

# Config
BACKEND_URL = os.getenv("RECORDER_BACKEND_URL", "http://localhost:8000")
OUTPUT_DIR = Path.home() / "Movies" / "Demo2PDF"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def check_backend():
    try:
        r = httpx.get(f"{BACKEND_URL}/health", timeout=3)
        return r.status_code == 200
    except:
        return False


def create_session():
    r = httpx.post(
        f"{BACKEND_URL}/api/sessions",
        params={"use_llm": True, "context": "User workflow documentation"}
    )
    r.raise_for_status()
    return r.json()["session_id"]


def upload_video(session_id: str, video_path: Path):
    with open(video_path, "rb") as f:
        files = {"video": (video_path.name, f, "video/quicktime")}
        r = httpx.post(
            f"{BACKEND_URL}/api/sessions/{session_id}/video",
            files=files,
            timeout=300
        )
    r.raise_for_status()
    return r.json()


def find_latest_recording():
    search_dirs = [
        Path.home() / "screenshots" / "demo2pdf",  # Your custom location
        Path.home() / "screenshots",
        Path.home() / "Desktop",
        Path.home() / "Movies",
        OUTPUT_DIR,
    ]

    recent_files = []
    for d in search_dirs:
        if d.exists():
            for f in d.glob("*.mov"):
                # Look for files modified in the last hour (3600 seconds)
                if time.time() - f.stat().st_mtime < 3600:
                    recent_files.append(f)

    if recent_files:
        return max(recent_files, key=lambda f: f.stat().st_mtime)
    return None


def main():
    print("")
    print("Demo2PDF - Video to Documentation")
    print("=" * 40)
    print("")

    video_path = None
    if len(sys.argv) > 1:
        video_path = Path(sys.argv[1])
        if not video_path.exists():
            print("ERROR: File not found: " + str(video_path))
            sys.exit(1)

    sys.stdout.write("Checking backend... ")
    sys.stdout.flush()
    if not check_backend():
        print("FAILED")
        print("")
        print("Backend not running at " + BACKEND_URL)
        print("Start it with: cd backend && python main.py")
        sys.exit(1)
    print("OK")

    if not video_path:
        print("")
        print("=" * 40)
        print("STEP 1: Record your screen")
        print("=" * 40)
        print("")
        print("Press Cmd+Shift+5 to open screen recording")
        print("")
        print("1. Select the area to record")
        print("2. Click Record")
        print("3. Do your workflow")
        print("4. Click STOP in the menu bar")
        print("5. Save the file")
        print("")
        input("Press ENTER when done recording...")

        print("")
        print("Looking for recent recordings...")
        video_path = find_latest_recording()

        if not video_path:
            print("ERROR: No recent .mov file found")
            print("")
            print("Run with path: python record.py /path/to/video.mov")
            sys.exit(1)

        print("Found: " + video_path.name)
        confirm = input("Use this file? [Y/n]: ").strip().lower()
        if confirm == 'n':
            print("Run with path: python record.py /path/to/video.mov")
            sys.exit(0)

    sys.stdout.write("Creating session... ")
    sys.stdout.flush()
    try:
        session_id = create_session()
        print("OK (" + session_id[:8] + "...)")
    except Exception as e:
        print("FAILED: " + str(e))
        sys.exit(1)

    size_mb = video_path.stat().st_size / (1024 * 1024)
    print("")
    print("Video: " + video_path.name + " (" + str(round(size_mb, 1)) + " MB)")

    print("")
    print("Uploading for AI analysis...")
    print("(This may take 1-2 minutes)")
    try:
        result = upload_video(session_id, video_path)
        step_count = result.get("step_count", 0)
        print("")
        print("SUCCESS: Generated " + str(step_count) + " steps!")

        if step_count > 0:
            print("")
            print("Steps preview:")
            for step in result.get("steps", [])[:5]:
                ts = step.get('timestamp', '')
                desc = step.get('description', '')
                print("  [" + ts + "] " + desc)
            if step_count > 5:
                print("  ... and " + str(step_count - 5) + " more")

    except Exception as e:
        print("FAILED: " + str(e))
        sys.exit(1)

    viewer_url = BACKEND_URL + "/viewer?session=" + session_id
    print("")
    print("Opening viewer...")
    webbrowser.open(viewer_url)

    print("")
    print("Done!")
    print("View at: " + viewer_url)


if __name__ == "__main__":
    main()
