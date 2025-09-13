from __future__ import annotations
import os
from typing import Optional, Dict, Any

from openai import OpenAI
from google import genai


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


def get_gemini_client() -> genai.Client:
    """Return a Google AI Studio (Gemini) client.

    Uses GEMINI_API_KEY or GOOGLE_API_KEY.
    """
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    return genai.Client(api_key=key)


def env_models() -> Dict[str, str]:
    return {
        "SYLLABUS_MODEL": os.getenv("SYLLABUS_MODEL", "openrouter/auto"),
        "TEXT_MODEL": os.getenv("TEXT_MODEL", "google/gemini-2.5-flash"),
        "MANIM_MODEL": os.getenv("MANIM_MODEL", "deepseek/deepseek-coder"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "google/gemini-2.5-flash"),
        "GEMINI_IMAGE_MODEL": os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview"),
    }
