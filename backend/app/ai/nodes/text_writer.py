from __future__ import annotations
from typing import Dict, Any

from ..llm import openrouter_chat
from ..clients import env_models


TEXT_SYSTEM = (
    "Write concise Markdown for a course lesson.\n"
    "- Use headings matching the provided outline.\n"
    "- Keep under 1000 words.\n"
    "- Include exactly one worked example.\n"
    "- End with a recap and 3 reflection questions.\n"
)


def text_prompt(module: Dict[str, Any], language: str, constraints: Dict[str, Any]) -> str:
    outline = "\n- ".join(module.get("outline", []))
    return (
        f"Language: {language}\n"
        f"Title: {module.get('title','')}\n"
        f"Objectives: {module.get('objectives', [])}\n"
        f"Outline:\n- {outline}\n"
        f"Audience: {constraints.get('audience','')} Level: {constraints.get('level_label','')}\n"
        f"Prerequisites: {constraints.get('prerequisites', [])}\n"
        f"Learning outcomes: {constraints.get('learning_outcomes', [])}\n"
    )


async def write_text(module: Dict[str, Any], language: str, constraints: Dict[str, Any]) -> str:
    models = env_models()
    try:
        content = await openrouter_chat(
            system=TEXT_SYSTEM,
            user=text_prompt(module, language, constraints),
            model=models["TEXT_MODEL"],
        )
    except Exception:
        content = ""
    return content or "# Lesson\n\nContent unavailable."
