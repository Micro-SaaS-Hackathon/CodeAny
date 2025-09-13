from __future__ import annotations
import json
import os
import random
import asyncio
from typing import Optional, Dict, Any

from .clients import get_openrouter_client, openrouter_headers


def _is_retryable_error(err: Exception) -> bool:
    msg = str(err).lower()
    retry_markers = [
        "429", "rate limit", "too many requests", "quota", "overloaded",
        "timeout", "timed out", "server error", "502", "503", "504",
    ]
    return any(m in msg for m in retry_markers)


def _backoff_delay(attempt: int, base: float = 0.8, cap: float = 20.0) -> float:
    # Exponential backoff with jitter
    exp = base * (2 ** (attempt - 1))
    jitter = random.uniform(0, 0.3)
    return min(cap, exp + jitter)


_sem_openrouter: asyncio.Semaphore | None = None


def _get_openrouter_semaphore() -> asyncio.Semaphore:
    global _sem_openrouter
    if _sem_openrouter is None:
        try:
            size = int(os.getenv("LLM_CONCURRENCY", "3"))
        except Exception:
            size = 3
        _sem_openrouter = asyncio.Semaphore(max(1, size))
    return _sem_openrouter


async def openrouter_chat(
    *,
    system: Optional[str],
    user: str,
    model: str,
    max_retries: int | None = None,
    timeout_s: float = 60.0,
) -> str:
    """Call OpenRouter chat with bounded concurrency and retries on 429/5xx/timeouts.

    Uses asyncio.to_thread to avoid blocking the event loop with the sync SDK.
    """
    sem = _get_openrouter_semaphore()
    retries = max_retries if max_retries is not None else int(os.getenv("LLM_MAX_RETRIES", "5") or 5)

    async with sem:
        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                def _call_once() -> str:
                    client = get_openrouter_client()
                    headers = openrouter_headers()
                    messages = []
                    if system:
                        messages.append({"role": "system", "content": system})
                    messages.append({"role": "user", "content": user})
                    resp = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=2000,
                        timeout=timeout_s,
                        extra_headers=headers,
                    )
                    return resp.choices[0].message.content if resp.choices else ""

                content = await asyncio.to_thread(_call_once)
                return content or ""
            except Exception as e:
                last_err = e
                if attempt >= retries or not _is_retryable_error(e):
                    raise
                await asyncio.sleep(_backoff_delay(attempt))
        # Should not reach here
        if last_err:
            raise last_err
        return ""


def safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s)
    except Exception:
        return None
