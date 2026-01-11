"""
Video Analysis Service - Analyzes screen recordings using AI vision.

Uses Gemini 2.0 Flash for direct video analysis (supports video natively),
or falls back to Claude/GPT-4V with extracted frames.
"""
import os
import base64
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass


@dataclass
class Step:
    """A single step extracted from video analysis."""
    number: int
    timestamp: str
    description: str
    screenshot_path: Optional[str] = None


class VideoAnalysisService:
    """
    Analyze screen recording videos and extract step-by-step instructions.

    Supports:
    - Gemini 1.5 Pro: Direct video analysis (best quality, native video support)
    - Claude/GPT-4V: Frame extraction + image analysis (fallback)
    """

    def __init__(
        self,
        provider: Literal["gemini", "anthropic", "openai"] = "gemini",
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key or self._get_api_key(provider)
        self._init_client()

    def _get_api_key(self, provider: str) -> str:
        """Get API key from environment."""
        key_map = {
            "gemini": "GOOGLE_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY"
        }
        return os.getenv(key_map.get(provider, ""), "")

    def _init_client(self):
        """Initialize the appropriate client."""
        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                # Use gemini-2.0-flash for video analysis (supports video natively)
                self.client = genai.GenerativeModel("gemini-2.0-flash")
            except ImportError:
                raise ImportError("google-generativeai package required for Gemini. Install with: pip install google-generativeai")
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)

    async def analyze_video(
        self,
        video_path: Path,
        context: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> List[Step]:
        """
        Analyze a screen recording video and extract steps.

        Args:
            video_path: Path to the video file (.mov, .mp4)
            context: Optional context about what's being documented
            output_dir: Directory to save extracted frame screenshots

        Returns:
            List of Step objects with descriptions
        """
        if self.provider == "gemini":
            return await self._analyze_with_gemini(video_path, context, output_dir)
        else:
            # For Claude/GPT-4V, extract frames first
            frames = self._extract_keyframes(video_path, output_dir)
            return await self._analyze_frames(frames, context)

    async def _analyze_with_gemini(
        self,
        video_path: Path,
        context: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> List[Step]:
        """
        Analyze video directly with Gemini 1.5 Pro.
        Gemini can understand video natively - no frame extraction needed.
        """
        import google.generativeai as genai

        # Upload video to Gemini
        video_file = genai.upload_file(str(video_path))

        # Wait for processing
        import time
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise RuntimeError(f"Video processing failed: {video_file.state.name}")

        # Build prompt
        prompt = self._build_analysis_prompt(context)

        # Analyze video
        response = self.client.generate_content(
            [video_file, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096
            )
        )

        # Parse response into steps
        steps = self._parse_steps(response.text)

        # Optionally extract frames for each step
        if output_dir:
            self._extract_frames_for_steps(video_path, steps, output_dir)

        # Clean up uploaded file
        genai.delete_file(video_file.name)

        return steps

    async def _analyze_frames(
        self,
        frames: List[Path],
        context: Optional[str] = None
    ) -> List[Step]:
        """Analyze extracted frames with Claude or GPT-4V."""
        if self.provider == "anthropic":
            return await self._analyze_frames_claude(frames, context)
        else:
            return await self._analyze_frames_gpt4v(frames, context)

    async def _analyze_frames_claude(
        self,
        frames: List[Path],
        context: Optional[str] = None
    ) -> List[Step]:
        """Analyze frames using Claude's vision."""
        prompt = self._build_analysis_prompt(context)

        # Build content with all frames
        content = []
        for frame in frames[:20]:  # Limit to 20 frames
            with open(frame, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            })

        content.append({"type": "text", "text": prompt})

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": content}]
        )

        steps = self._parse_steps(response.content[0].text)

        # Associate screenshots with steps
        for i, step in enumerate(steps):
            if i < len(frames):
                step.screenshot_path = str(frames[i])

        return steps

    async def _analyze_frames_gpt4v(
        self,
        frames: List[Path],
        context: Optional[str] = None
    ) -> List[Step]:
        """Analyze frames using GPT-4 Vision."""
        prompt = self._build_analysis_prompt(context)

        # Build content with all frames
        content = [{"type": "text", "text": prompt}]

        for frame in frames[:20]:  # Limit to 20 frames
            with open(frame, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"}
            })

        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4096,
            messages=[{"role": "user", "content": content}]
        )

        steps = self._parse_steps(response.choices[0].message.content)

        # Associate screenshots with steps
        for i, step in enumerate(steps):
            if i < len(frames):
                step.screenshot_path = str(frames[i])

        return steps

    def _build_analysis_prompt(self, context: Optional[str] = None) -> str:
        """Build the prompt for video/frame analysis."""
        prompt = """You are analyzing a screen recording of a user performing actions in a web browser.

Your task is to identify each distinct user action and describe it as a step in a user guide.

Guidelines:
1. Identify each DISTINCT action (click, type, navigate, scroll, select)
2. Use imperative mood ("Click", "Enter", "Select", not "The user clicks")
3. Be specific about UI elements (button names, field labels, menu items)
4. Include approximate timestamps in MM:SS format
5. Group related micro-actions (e.g., clicking a field then typing = one "Enter" step)
6. For sensitive data like passwords, just say "Enter your password"
7. Number each step sequentially

"""
        if context:
            prompt += f"\nContext: The user is documenting {context}.\n"

        prompt += """
Output format (one step per line):
[MM:SS] Step N: Description

Example:
[00:05] Step 1: Navigate to the login page
[00:12] Step 2: Enter your email address in the "Email" field
[00:18] Step 3: Enter your password
[00:22] Step 4: Click the "Sign In" button

Analyze the video and provide the steps:"""

        return prompt

    def _parse_steps(self, response_text: str) -> List[Step]:
        """Parse AI response into Step objects."""
        steps = []
        lines = response_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to parse format: [MM:SS] Step N: Description
            import re
            match = re.match(r'\[(\d{1,2}:\d{2})\]\s*Step\s*(\d+):\s*(.+)', line, re.IGNORECASE)

            if match:
                timestamp, number, description = match.groups()
                steps.append(Step(
                    number=int(number),
                    timestamp=timestamp,
                    description=description.strip()
                ))
            else:
                # Try simpler format: Step N: Description or just N. Description
                match = re.match(r'(?:Step\s*)?(\d+)[.):]\s*(.+)', line, re.IGNORECASE)
                if match:
                    number, description = match.groups()
                    steps.append(Step(
                        number=int(number),
                        timestamp="",
                        description=description.strip()
                    ))

        return steps

    def _extract_keyframes(
        self,
        video_path: Path,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Extract keyframes from video using ffmpeg scene detection.
        Returns paths to extracted frame images.
        """
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp())

        output_dir.mkdir(parents=True, exist_ok=True)
        output_pattern = output_dir / "frame_%04d.png"

        # Use ffmpeg to extract frames on scene changes
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vf", "select='gt(scene,0.3)',showinfo",  # Scene change detection
            "-vsync", "vfr",
            "-frame_pts", "1",
            str(output_pattern),
            "-y"  # Overwrite
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Fallback: extract frames at fixed intervals (every 2 seconds)
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vf", "fps=0.5",  # 1 frame every 2 seconds
                str(output_pattern),
                "-y"
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        # Return sorted list of extracted frames
        frames = sorted(output_dir.glob("frame_*.png"))
        return frames

    def _extract_frames_for_steps(
        self,
        video_path: Path,
        steps: List[Step],
        output_dir: Path
    ):
        """Extract a frame for each step at its timestamp."""
        output_dir.mkdir(parents=True, exist_ok=True)

        for step in steps:
            if not step.timestamp:
                continue

            output_file = output_dir / f"step_{step.number:03d}.png"

            # Parse timestamp MM:SS to seconds
            parts = step.timestamp.split(":")
            if len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            else:
                seconds = 0

            # Extract frame at timestamp
            # Try common ffmpeg locations (check explicit paths first)
            ffmpeg_paths = [
                os.path.expanduser("~/bin/ffmpeg"),  # User bin
                "/usr/local/bin/ffmpeg",  # Homebrew Intel
                "/opt/homebrew/bin/ffmpeg",  # Homebrew ARM
            ]
            ffmpeg_cmd = None
            for fp in ffmpeg_paths:
                if os.path.exists(fp):
                    ffmpeg_cmd = fp
                    break

            if not ffmpeg_cmd:
                # Fall back to system PATH
                import shutil
                ffmpeg_cmd = shutil.which("ffmpeg")

            if not ffmpeg_cmd:
                continue

            cmd = [
                ffmpeg_cmd, "-ss", str(seconds),
                "-i", str(video_path),
                "-frames:v", "1",
                str(output_file),
                "-y"
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                step.screenshot_path = str(output_file)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass  # Frame extraction failed or ffmpeg not installed, continue without screenshot
