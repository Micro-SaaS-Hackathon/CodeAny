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
    "- Do NOT import external libraries (pandas, numpy, matplotlib, seaborn, scipy, sklearn, PIL/Pillow, requests, networkx, etc.).\n"
    "- Prefer Text over LaTeX (MathTex/Tex) unless essential.\n"
    "- If using backslashes, use raw strings (r'...') to avoid invalid escape sequences.\n"
)


_BANNED_IMPORTS = {
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "scipy",
    "sklearn",
    "requests",
    "pil",
    "pillow",
    "networkx",
}


def _has_banned_imports(code: str) -> bool:
    try:
        tree = ast.parse(code or "")
    except Exception:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if (n.name or "").split(".")[0].lower() in _BANNED_IMPORTS:
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0].lower()
            if mod in _BANNED_IMPORTS:
                return True
    return False


def _fallback_lesson(msg: str = "Visualization simplified (no external libs)") -> str:
    return (
        "from manim import *\n\n"
        "class Lesson(Scene):\n"
        "    def construct(self):\n"
        "        title = Text('Lesson').scale(1.2)\n"
        "        note = Text('" + msg.replace("'", "\\'") + "').scale(0.6)\n"
        "        group = VGroup(title, note).arrange(DOWN, buff=0.5)\n"
        "        self.play(FadeIn(group))\n"
        "        self.wait(2)\n"
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
    # Guardrail: ban heavy third-party imports which are not available in the sandbox image
    if _has_banned_imports(code):
        log.warning(
            f"Manim code contains banned imports | module={module.get('id')} | preview={preview(code)}"
        )
        code = _fallback_lesson("External libraries omitted — using Manim primitives only")
    # Syntax check
    try:
        ast.parse(code)
        log.info(f"Manim parsed | module={module.get('id')} | len={len(code)} | preview={preview(code)}")
    except Exception as e:
        code = _fallback_lesson(f"Syntax error sanitized: {e}")
        log.warning(f"Manim syntax error | module={module.get('id')} | err={e} | preview={preview(code)}")
    return code
