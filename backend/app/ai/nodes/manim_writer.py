from __future__ import annotations
import ast
import re
from typing import Dict, Any

from ..llm import openrouter_chat
from ..logging_utils import get_logger, preview
from ..resources import MANIM_DOC_EXCERPTS

log = get_logger("nodes.manim")
from ..clients import env_models


MANIM_SYSTEM = (
    "You are an expert Manim Community educator and animator.\n"
    "Generate Python code for a single Manim Scene named `Lesson`.\n"
    "Goal: a short tutorial-style video that explains the topic visually and with on-screen captions.\n"
    "Consult the official Manim tutorials and reference whenever choosing APIs: https://docs.manim.community/en/stable/tutorials_guides.html and https://docs.manim.community/en/stable/reference.html.\n"
    "Favor patterns that follow the stable Community edition documented there and avoid deprecated syntax.\n"
    "- Use only Manim Community stable APIs.\n"
    "- 16:9 aspect, minimal dependencies.\n"
    "- Include helpful comments.\n"
    "- One Scene only.\n"
    "- Do NOT import external libraries (pandas, numpy, matplotlib, seaborn, scipy, sklearn, PIL/Pillow, requests, networkx, etc.).\n"
    "- Prefer Text over LaTeX (MathTex/Tex) unless essential.\n"
    "- If using backslashes, use raw strings (r'...') to avoid invalid escape sequences.\n"
    "- Avoid any audio/voiceover libraries; show short bottom captions instead.\n"
    "Must-haves in the Scene:\n"
    "1) Title card with the lesson title.\n"
    "2) Quick learning objectives (2-4 bullets).\n"
    "3) Concept explanation with 2–3 simple animations (Create/Write/Transform).\n"
    "4) One worked example step-by-step.\n"
    "5) Recap/summary bullets.\n"
    "Provide a helper method inside the Scene: `def say(self, text: str, t: float = 2):` that shows a semi-transparent rectangle along the bottom with a short Text caption; fade it in, wait(t), then fade out. Use it for each step to explain what's happening. Keep captions concise (≤ 80 chars).\n"
    "Return only valid Python code that begins with `from manim import *`. Do not include Markdown fences, commentary, or explanations.\n"
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
    "manim_voiceover",
    "gtts",
    "pyttsx3",
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
        "    def say(self, text: str, t: float = 2):\n"
        "        bar = Rectangle(width=FRAME_WIDTH, height=0.8, fill_opacity=0.6, fill_color=BLACK, stroke_width=0)\n"
        "        bar.to_edge(DOWN)\n"
        "        caption = Text(text).scale(0.45)\n"
        "        caption.move_to(bar.get_center())\n"
        "        grp = VGroup(bar, caption)\n"
        "        self.play(FadeIn(grp))\n"
        "        self.wait(t)\n"
        "        self.play(FadeOut(grp))\n"
        "    def construct(self):\n"
        "        title = Text('Lesson').scale(1.2)\n"
        "        note = Text('" + msg.replace("'", "\\'") + "').scale(0.6)\n"
        "        group = VGroup(title, note).arrange(DOWN, buff=0.5)\n"
        "        self.play(FadeIn(group))\n"
        "        self.say('Auto-generated fallback scene')\n"
        "        self.wait(0.5)\n"
    )


def _has_animation_calls(code: str) -> bool:
    """Heuristic: ensure the scene contains at least some animations."""
    lowered = (code or "").lower()
    markers = [
        "self.play(",
        "write(",
        "create(",
        "transform(",
        "fadein(",
        "fadeout(",
        "growfromcenter(",
        "laggedstart(",
    ]
    return any(m in lowered for m in markers)


def _fallback_tutorial(module: Dict[str, Any]) -> str:
    """Produce a minimal tutorial-style scene with captions and simple animations."""
    title = (module.get("title") or "Lesson").replace("'", "\\'")
    outline = module.get("outline", []) or []
    bullets = [str(b) for b in outline if b]
    if len(bullets) > 4:
        bullets = bullets[:4]
    # Escape single quotes in bullets
    bullets = [b.replace("'", "\\'") for b in bullets]
    blines = ",\n            ".join([f"Text('• {b}').scale(0.5)" for b in bullets]) or "Text('• Overview').scale(0.5)"
    return (
        "from manim import *\n\n"
        "class Lesson(Scene):\n"
        "    def say(self, text: str, t: float = 2):\n"
        "        bar = Rectangle(width=FRAME_WIDTH, height=0.8, fill_opacity=0.6, fill_color=BLACK, stroke_width=0)\n"
        "        bar.to_edge(DOWN)\n"
        "        caption = Text(text).scale(0.45)\n"
        "        caption.move_to(bar.get_center())\n"
        "        grp = VGroup(bar, caption)\n"
        "        self.play(FadeIn(grp))\n"
        "        self.wait(t)\n"
        "        self.play(FadeOut(grp))\n"
        "    def construct(self):\n"
        f"        title = Text('{title}').scale(0.9)\n"
        "        self.play(Write(title))\n"
        f"        self.say('Today: {title}')\n"
        "        self.wait(0.3)\n"
        "        bullets = VGroup(\n"
        f"            {blines}\n"
        "        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(title, DOWN, buff=0.6).align_to(title, LEFT)\n"
        "        for line in bullets:\n"
        "            self.play(FadeIn(line, shift=RIGHT))\n"
        "            self.wait(0.3)\n"
        "        self.say('Let\'s see a quick example')\n"
        "        ax = Axes(x_range=[0, 4, 1], y_range=[0, 4, 1], tips=False).scale(0.8).to_edge(DOWN)\n"
        "        dot = Dot(ax.coords_to_point(0, 0), color=YELLOW)\n"
        "        path = VMobject(color=YELLOW)\n"
        "        path.set_points_as_corners([ax.coords_to_point(0,0), ax.coords_to_point(1,1), ax.coords_to_point(2,1.5), ax.coords_to_point(3,2.5)])\n"
        "        self.play(Create(ax))\n"
        "        self.play(FadeIn(dot))\n"
        "        self.play(MoveAlongPath(dot, path), run_time=3)\n"
        "        self.say('Example complete — notice the trend')\n"
        "        recap = VGroup(Text('Recap').scale(0.7), Text('• Key idea 1').scale(0.5), Text('• Key idea 2').scale(0.5))\n"
        "        recap.arrange(DOWN, aligned_edge=LEFT, buff=0.25).to_edge(UP)\n"
        "        self.play(ReplacementTransform(VGroup(title, bullets), recap))\n"
        "        self.wait(1)\n"
    )


def _extract_manim_code(raw: str) -> str:
    """Strip assistant chatter and extract the first relevant code block."""
    text = (raw or "").strip()
    if not text:
        return ""
    # Prefer fenced blocks
    fenced = re.findall(r"```(?:python)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if fenced:
        for block in fenced:
            block_stripped = block.strip()
            if "from manim" in block_stripped or "class Lesson" in block_stripped:
                return block_stripped
        return fenced[0].strip()
    # If no fences, find the first occurrence of a Manim import or class definition
    markers = ["from manim", "class Lesson"]
    for marker in markers:
        idx = text.lower().find(marker)
        if idx != -1:
            return text[idx:].strip()
    return text


def _ensure_say_helper(code: str) -> str:
    """Inject the standard `say` helper if the Scene is missing one."""
    if "class Lesson" not in code or "def say(" in code:
        return code
    lines = code.splitlines()
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("class Lesson"):
            insert_idx = i + 1
            break
    if insert_idx is None:
        return code
    # Determine indentation (default four spaces inside the class)
    indent = "    "
    say_block = [
        f"{indent}def say(self, text: str, t: float = 2):",
        f"{indent}    bar = Rectangle(width=FRAME_WIDTH, height=0.8, fill_opacity=0.6, fill_color=BLACK, stroke_width=0)",
        f"{indent}    bar.to_edge(DOWN)",
        f"{indent}    caption = Text(text).scale(0.45)",
        f"{indent}    caption.move_to(bar.get_center())",
        f"{indent}    group = VGroup(bar, caption)",
        f"{indent}    self.play(FadeIn(group))",
        f"{indent}    self.wait(t)",
        f"{indent}    self.play(FadeOut(group))",
        "",
    ]
    lines[insert_idx:insert_idx] = say_block
    return "\n".join(lines)


def _verify_scene_structure(tree: ast.AST) -> tuple[bool, list[str]]:
    """Check for key structural requirements before compiling Manim code."""
    errors: list[str] = []

    has_manim_import = False
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("manim"):
            has_manim_import = True
            break
        if isinstance(node, ast.Import):
            for name in node.names:
                if (name.name or "").startswith("manim"):
                    has_manim_import = True
                    break
            if has_manim_import:
                break
    if not has_manim_import:
        errors.append("Missing `from manim import *` or equivalent Manim import.")

    lesson_cls: ast.ClassDef | None = None
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ClassDef) and node.name == "Lesson":
            lesson_cls = node
            break
    if not lesson_cls:
        errors.append("Missing class `Lesson` inheriting from Scene as required by the docs.")
        return False, errors

    def _is_scene_base(base: ast.expr) -> bool:
        if isinstance(base, ast.Name):
            return base.id.endswith("Scene")
        if isinstance(base, ast.Attribute):
            return base.attr.endswith("Scene")
        return False

    if not any(_is_scene_base(b) for b in lesson_cls.bases):
        errors.append("Class `Lesson` must inherit from `Scene` (or a Scene subclass).")

    has_construct = False
    has_say = False
    for stmt in lesson_cls.body:
        if isinstance(stmt, ast.FunctionDef):
            if stmt.name == "construct":
                has_construct = True
                has_animation_call = False
                for inner in ast.walk(stmt):
                    if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                        if isinstance(inner.func.value, ast.Name) and inner.func.value.id == "self":
                            if inner.func.attr in {"play", "say", "add", "wait"}:
                                has_animation_call = True
                                break
                if not has_animation_call:
                    errors.append("`construct` must include at least one animation call such as `self.play(...)` as shown in the tutorials.")
            elif stmt.name == "say":
                has_say = True
                args = stmt.args
                arg_names = [a.arg for a in args.args]
                if len(arg_names) < 3 or arg_names[0] != "self" or arg_names[1] != "text" or arg_names[2] != "t":
                    errors.append("`say` helper must accept `(self, text, t)` parameters, matching the recommended signature.")
                else:
                    defaults = args.defaults or []
                    if defaults:
                        default_targets = args.args[-len(defaults):]
                        default_map = {target.arg: default for target, default in zip(default_targets, defaults)}
                    else:
                        default_map = {}
                    if "t" not in default_map:
                        errors.append("`say` helper must provide a default duration for `t`, e.g., `t: float = 2`. See Manim docs on custom methods.")
                    else:
                        default_val = default_map["t"]
                        if isinstance(default_val, ast.Constant):
                            const_val = default_val.value
                            if const_val not in (2, 2.0):
                                errors.append("`say` helper duration default should be 2 seconds to match pacing guidance.")
                        else:
                            errors.append("`say` helper duration default should be the numeric literal 2.")
    if not has_construct:
        errors.append("Missing `construct` method in `Lesson` Scene.")
    if not has_say:
        errors.append("Missing `say` helper required for captions (see tutorials on text overlays).")

    return not errors, errors


def manim_prompt(module: Dict[str, Any], language: str, narrative_text: str | None = None) -> str:
    outline = "; ".join(module.get("outline", []))
    prompt = (
        f"Create Manim code for: {module.get('title','')}\n"
        f"Outline: {outline}\n"
        f"Narrative language: {language}\n"
        f"Class name must be Lesson.\n"
        f"Style: teacher explains with brief on-screen captions and simple, clear visuals.\n"
        "Reference the following Manim documentation summary when choosing APIs:\n"
        f"{MANIM_DOC_EXCERPTS}\n"
        "Return only Python source code without Markdown or commentary. Start with `from manim import *`.\n"
    )
    if narrative_text:
        # Provide the lesson text so captions can be derived/condensed.
        # Keep only a preview to constrain length; the LLM should summarize.
        snippet = narrative_text.strip()
        if len(snippet) > 2500:
            snippet = snippet[:2500]
        prompt += ("\nKey points to cover (from lesson text):\n" + snippet)
    return prompt


async def write_manim_code(module: Dict[str, Any], language: str, narrative_text: str | None = None) -> str:
    models = env_models()
    feedback: list[str] = []
    max_attempts = 2
    log.info(f"Manim start | module={module.get('id')} | title={module.get('title')}")

    for attempt in range(1, max_attempts + 1):
        try:
            user_prompt = manim_prompt(module, language, narrative_text)
            if feedback:
                issues = "\n".join(f"- {item}" for item in feedback)
                user_prompt += (
                    "\nThe previous draft was invalid. Review the official Manim docs linked above and fix these issues before returning the code:\n"
                    f"{issues}\nReturn only the corrected Python code without Markdown fences or commentary."
                )
            raw = await openrouter_chat(
                system=MANIM_SYSTEM,
                user=user_prompt,
                model=models["MANIM_MODEL"],
            )
        except Exception as e:
            log.warning(f"Manim chat error | module={module.get('id')} | attempt={attempt} | err={e}")
            raw = ""

        code = _extract_manim_code(raw)
        if not code:
            feedback = [
                "No executable Python source was returned. Reply with only the Manim code starting with `from manim import *`."
            ]
            if attempt >= max_attempts:
                log.warning(f"Manim empty output after retries | module={module.get('id')}")
                return _fallback_tutorial(module)
            continue

        code = _ensure_say_helper(code)

        if _has_banned_imports(code):
            log.warning(
                f"Manim code contains banned imports | module={module.get('id')} | attempt={attempt} | preview={preview(code)}"
            )
            feedback = ["Do not import third-party libraries; rely solely on `from manim import *` and core classes."]
            if attempt >= max_attempts:
                return _fallback_lesson("External libraries omitted — using Manim primitives only")
            continue

        try:
            tree = ast.parse(code)
            log.info(
                f"Manim parsed | module={module.get('id')} | attempt={attempt} | len={len(code)} | preview={preview(code)}"
            )
        except Exception as e:
            log.warning(
                f"Manim syntax error | module={module.get('id')} | attempt={attempt} | err={e} | preview={preview(code)}"
            )
            feedback = [f"Fix the Python syntax error reported: {e}"]
            if attempt >= max_attempts:
                return _fallback_lesson(f"Syntax error sanitized: {e}")
            continue

        ok, structural_errors = _verify_scene_structure(tree)
        if not ok:
            log.warning(
                f"Manim structural verification failed | module={module.get('id')} | attempt={attempt} | issues={structural_errors}"
            )
            feedback = structural_errors
            if attempt >= max_attempts:
                return _fallback_tutorial(module)
            continue

        if not _has_animation_calls(code):
            log.warning(
                f"Manim code lacks animations; injecting tutorial fallback | module={module.get('id')}"
            )
            return _fallback_tutorial(module)

        return code

    # If all retries exhausted, synthesize a minimal tutorial scene
    log.warning(f"Manim generation retries exhausted | module={module.get('id')}")
    return _fallback_tutorial(module)
