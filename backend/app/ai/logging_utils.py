from __future__ import annotations
import logging
import logging.handlers
import os
from typing import Any, Dict


_CONFIGURED = False


def _ensure_handler():
    global _CONFIGURED
    if _CONFIGURED:
        return
    level_str = os.getenv("AI_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    root = logging.getLogger("cursly.ai")
    root.setLevel(level)
    fmt = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%H:%M:%S")
    # Console handler
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)
    # File handler (rotating). Path from AI_LOG_FILE or default logs/ai.log
    log_file = os.getenv("AI_LOG_FILE", "logs/ai.log")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers):
            fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
            fh.setFormatter(fmt)
            root.addHandler(fh)
    except Exception:
        # If file handler can't be created, continue with console only
        pass
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _ensure_handler()
    return logging.getLogger(f"cursly.ai.{name}")


def preview(val: Any, *, limit: int | None = None) -> str:
    try:
        lim = limit if limit is not None else int(os.getenv("AI_LOG_PREVIEW", "240"))
    except Exception:
        lim = 240
    try:
        if val is None:
            return "<none>"
        s = str(val)
        if len(s) <= lim:
            return s
        return s[:lim] + f"… (+{len(s)-lim} chars)"
    except Exception:
        return "<unprintable>"


REDACT_KEYS = {"authorization", "api_key", "apikey", "openrouter_api_key", "gemini_api_key", "google_api_key", "convex_deploy_key", "convex_user_bearer"}


def safe_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        lk = str(k).lower()
        if lk in REDACT_KEYS or "token" in lk or "secret" in lk or "key" in lk:
            out[k] = "<redacted>"
        else:
            out[k] = v
    return out
