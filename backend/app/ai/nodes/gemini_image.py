from __future__ import annotations
from typing import Dict, Any

from ..clients import env_models
from ..llm import openrouter_chat
from ..logging_utils import get_logger, preview

log = get_logger("nodes.gemini")


async def generate_gemini_image_or_fallback(module: Dict[str, Any], language: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Kimi-first behavior: return textual Q&A instead of generating images.

    This replaces Google Gemini image generation to rely solely on OpenRouter
    text output (default: moonshotai/kimi-k2:free).
    """
    models = env_models()
    qa_prompt = (
        f"Produce 5 short Q&A pairs in Markdown about: {module.get('title','')}.\n"
        f"Level: {constraints.get('level_label','')} Audience: {constraints.get('audience','')} Language: {language}."
    )
    try:
        log.info(f"Kimi QA start | module={module.get('id')}")
        qa_md = await openrouter_chat(system=None, user=qa_prompt, model=models["TEXT_MODEL"])
    except Exception as e:
        log.warning(f"Kimi QA error | module={module.get('id')} | err={e}")
        qa_md = ""
    if qa_md:
        log.info(f"Kimi QA ok | module={module.get('id')} | len={len(qa_md)} | preview={preview(qa_md)}")
    return {"qa": qa_md or "- Q: What is the key idea?\n  - A: A concise explanation.\n- Q: When to use it?\n  - A: In scenarios X and Y.\n- Q: Common pitfall?\n  - A: Missing assumptions."}
