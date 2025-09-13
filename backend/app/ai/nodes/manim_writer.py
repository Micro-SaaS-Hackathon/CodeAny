from __future__ import annotations
import ast
from typing import Dict, Any

from ..llm import openrouter_chat
from ..logging_utils import get_logger, preview

log = get_logger("nodes.manim")
from ..clients import env_models


MANIM_SYSTEM = (
    "Generate Python code for a single Manim Scene named `Lesson`.\n"
    "- Use only Manim Community stable APIs.\n"
    "- 16:9 aspect, minimal dependencies.\n"
    "- Include helpful comments.\n"
    "- One Scene only.\n"
)


def manim_prompt(module: Dict[str, Any], language: str) -> str:
    outline = "; ".join(module.get("outline", []))
    return (
        f"Create Manim code for: {module.get('title','')}\n"
        f"Outline: {outline}\n"
        f"Narrative language: {language}\n"
        f"Class name must be Lesson."
    )


async def write_manim_code(module: Dict[str, Any], language: str) -> str:
    models = env_models()
    try:
        log.info(f"Manim start | module={module.get('id')} | title={module.get('title')}")
        code = await openrouter_chat(
            system=MANIM_SYSTEM,
            user=manim_prompt(module, language),
            model=models["MANIM_MODEL"],
        )
    except Exception:
        code = ""
    code = (code or "").strip()
    # Best-effort extract code fences
    if code.startswith("```"):
        try:
            code = code.split("```", 2)[1]
            # trim possible language tag
            if "\n" in code:
                code = code.split("\n", 1)[1]
        except Exception:
            pass
    # Syntax check
    try:
        ast.parse(code)
        log.info(f"Manim parsed | module={module.get('id')} | len={len(code)} | preview={preview(code)}")
    except Exception as e:
        code = f"# Syntax error: {e}\n" + code
        log.warning(f"Manim syntax error | module={module.get('id')} | err={e} | preview={preview(code)}")
    return code
