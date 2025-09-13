from __future__ import annotations
import base64
import os
import random
import asyncio
from typing import Dict, Any, Tuple

from ..clients import get_gemini_client, env_models

_gemini_sem: asyncio.Semaphore | None = None
from ..llm import openrouter_chat


def _extract_image_b64_from_gemini_response(resp) -> Tuple[str | None, str | None]:
    try:
        # google-genai responses have candidates[0].content.parts
        cand = resp.candidates[0]
        parts = cand.content.parts
        image_b64: str | None = None
        caption: str | None = None
        for p in parts:
            # inline_data with mime_type image/* and base64 data
            if hasattr(p, "inline_data"):
                mime = getattr(p.inline_data, "mime_type", "")
                data = getattr(p.inline_data, "data", None)
                if mime.startswith("image/") and data:
                    image_b64 = data
            elif hasattr(p, "text"):
                if not caption and p.text:
                    caption = p.text
        return image_b64, caption
    except Exception:
        return None, None


async def generate_gemini_image_or_fallback(module: Dict[str, Any], language: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
    models = env_models()
    want_images = bool(constraints.get("images", True))
    if want_images:
        try:
            client = get_gemini_client()
            # Fallback to generic generate_content with an image-capable model
            prompt = (
                f"Create a single didactic diagram (PNG) for the lesson: {module.get('title','')}.\n"
                f"Audience: {constraints.get('audience','')} | Level: {constraints.get('level_label','')} | Language: {language}.\n"
                "Keep it clear and simple. Include labels when helpful."
            )
            model_name = models["GEMINI_IMAGE_MODEL"]
            # Retry with exponential backoff on rate limits and 5xx
            async def _call_once():
                return client.models.generate_content(model=model_name, contents=prompt)  # type: ignore

            async def _with_retry():
                retries = int(os.getenv("GEMINI_MAX_RETRIES", "5") or 5)
                try:
                    conc = int(os.getenv("GEMINI_CONCURRENCY", "2") or 2)
                except Exception:
                    conc = 2
                # Semaphore to bound concurrent Gemini calls
                global _gemini_sem
                try:
                    _gemini_sem
                except NameError:
                    _gemini_sem = None  # type: ignore
                if _gemini_sem is None:
                    _gemini_sem = asyncio.Semaphore(max(1, conc))  # type: ignore
                async with _gemini_sem:  # type: ignore
                    last_err: Exception | None = None
                    for attempt in range(1, retries + 1):
                        try:
                            return await asyncio.to_thread(lambda: _call_once())
                        except Exception as e:
                            last_err = e
                            msg = str(e).lower()
                            retryable = any(m in msg for m in ["429", "rate limit", "quota", "too many requests", "502", "503", "504", "timeout"])  # noqa: E501
                            if attempt >= retries or not retryable:
                                raise
                            delay = min(20.0, 0.8 * (2 ** (attempt - 1)) + random.uniform(0, 0.3))
                            await asyncio.sleep(delay)
                    if last_err:
                        raise last_err
                    raise RuntimeError("gemini retry loop exhausted")

            response = await _with_retry()
            img_b64, caption = _extract_image_b64_from_gemini_response(response)
            if img_b64:
                return {"gemini_image_b64": img_b64, "gemini_image_caption": caption or module.get("title", "")}
        except Exception:
            # Fall through to QA
            pass

    # Fallback: 5 Q&A via OpenRouter
    qa_prompt = (
        f"Produce 5 short Q&A pairs in Markdown about: {module.get('title','')}.\n"
        f"Level: {constraints.get('level_label','')} Audience: {constraints.get('audience','')} Language: {language}."
    )
    try:
        qa_md = await openrouter_chat(system=None, user=qa_prompt, model=models["TEXT_MODEL"])
    except Exception:
        qa_md = ""
    return {"qa": qa_md or "- Q: What is the key idea?\n  - A: A concise explanation.\n- Q: When to use it?\n  - A: In scenarios X and Y.\n- Q: Common pitfall?\n  - A: Missing assumptions."}
