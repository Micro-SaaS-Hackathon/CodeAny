from __future__ import annotations
import os
from typing import Optional, Dict, Any

from openai import OpenAI
try:
    from google import genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore


def get_openrouter_client() -> OpenAI:
    """Return an OpenAI SDK client configured for OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Create a client anyway; calls will fail until key is set
        api_key = ""
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    return client


def openrouter_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {}
    app_url = os.getenv("APP_URL", "http://localhost:8000")
    app_title = os.getenv("APP_TITLE", "Cursly CourseFactory")
    # OpenRouter attribution headers (optional but recommended)
    headers["HTTP-Referer"] = app_url
    headers["X-Title"] = app_title
    return headers


def get_gemini_client():
    """Return a Google AI Studio (Gemini) client if available, else None."""
    if genai is None:
        return None
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    return genai.Client(api_key=key)


def env_models() -> Dict[str, str]:
    return {
        # Default to free Kimi on OpenRouter for text tasks
        "SYLLABUS_MODEL": os.getenv("SYLLABUS_MODEL", "moonshotai/kimi-k2:free"),
        "TEXT_MODEL": os.getenv("TEXT_MODEL", "moonshotai/kimi-k2:free"),
        "MANIM_MODEL": os.getenv("MANIM_MODEL", "deepseek/deepseek-coder"),
        # Kept for compatibility; image worker now falls back to text Q&A via OpenRouter
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "moonshotai/kimi-k2:free"),
        "GEMINI_IMAGE_MODEL": os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview"),
    }
