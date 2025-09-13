from __future__ import annotations
from typing import Any, Dict, List

from ..llm import openrouter_chat, safe_json_loads
from ..logging_utils import get_logger, preview

log = get_logger("nodes.syllabus")
from ..clients import env_models


SYLLABUS_SYSTEM = (
    "You are a course designer. Output ONLY valid JSON:\n"
    "{\n  \"modules\": [\n    {\n      \"id\": \"m1\",\n      \"title\": \"<title>\",\n      \"objectives\": [\"<objective>\", \"...\"],\n      \"outline\": [\"<section 1>\", \"<section 2>\", \"...\"]\n    }\n  ]\n}\n"
    "Rules:\n"
    "- 6–10 modules unless constraints specify otherwise.\n"
    "- Titles must be specific and learner-facing.\n"
    "- Objectives use measurable verbs (explain, derive, apply).\n"
    "- Outline is 4–7 bullet points, sequenced for learning.\n"
    "- No prose outside the JSON."
)


def syllabus_user_prompt(topic: str, level: str, constraints: Dict[str, Any]) -> str:
    return (
        f"Topic: {topic}\n"
        f"Level: {level}\n"
        f"Constraints: {constraints}"
    )


async def generate_syllabus(topic: str, level: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
    models = env_models()
    try:
        log.info(f"Syllabus start | topic={topic} | level={level} | constraints_keys={list(constraints.keys())}")
        content = await openrouter_chat(
            system=SYLLABUS_SYSTEM,
            user=syllabus_user_prompt(topic, level, constraints),
            model=models["SYLLABUS_MODEL"],
        )
    except Exception:
        content = ""
    log.info(f"Syllabus raw preview={preview(content)}")
    data = safe_json_loads(content or "")
    if not data or "modules" not in data or not isinstance(data["modules"], list):
        # Fallback minimal syllabus (6 modules)
        modules = []
        count = int(constraints.get("count_modules") or 6)
        count = max(1, min(count, 10))
        for i in range(1, count + 1):
            modules.append({
                "id": f"m{i}",
                "title": f"Module {i}: {topic}",
                "objectives": ["Explain key ideas", "Apply basic methods"],
                "outline": ["Introduction", "Core Concepts", "Worked Example", "Practice", "Recap"],
            })
        log.warning(f"Syllabus fallback used | count={count}")
        return modules
    mods = data["modules"]
    log.info(f"Syllabus ok | modules={len(mods)} | ids={[m.get('id') for m in mods]}")
    return mods
