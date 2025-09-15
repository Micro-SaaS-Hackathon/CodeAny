"""Curated Manim guidance extracted from official docs for the agent RAG prompts.

Sources:
- Tutorials & Guides: https://docs.manim.community/en/stable/tutorials_guides.html
- Reference Manual: https://docs.manim.community/en/stable/reference.html

The text in `MANIM_DOC_EXCERPTS` paraphrases stable guidance so we can include it in
prompt context without pulling the entire docs each call. Keep snippets concise and
update when the upstream docs change.
"""

MANIM_DOC_EXCERPTS = """
Core scene structure (Scene reference: manim.scene.scene.Scene)
- Subclass `Scene` and implement `def construct(self): ...`.
- Display objects with `self.add(...)` or `self.play(Create(...))`; remove with `self.remove(...)`.
- Use `self.play(...)` for all animations and `self.wait()` to pause.
- Avoid overriding `__init__`; use `setup()` for pre-construct hooks.

Animating and positioning (Tutorial quickstart + reference)
- Common mobjects: `Circle()`, `Square()`, `Rectangle()`, `Triangle()`, `Text("label")`, `MathTex(r"...")`.
- Animate creation with `Create`, transformation with `Transform`, fading with `FadeIn/FadeOut`.
- `.animate` turns any mutating method (like `shift`, `set_fill`, `rotate`) into an animation; combine inside `self.play(...)`.
- Arrange items with methods such as `next_to`, `to_edge`, `arrange`, and group with `VGroup`.
- Use constants like `UP`, `DOWN`, `LEFT`, `RIGHT`, `ORIGIN` and color constants from `manim` (e.g., `BLUE`, `YELLOW`).

Layout helpers (Tutorials)
- Use `VGroup`/`Group` to manage collections of mobjects and animate them together.
- `arrange(direction=...)` can quickly lay out bullets or columns.
- For bullet text, prefer `Text` or `MarkupText` for plain strings; reserve `MathTex` for math.

Camera & background tips
- Set background color by editing `self.camera.background_color = ...` or using `self.add(BackgroundRectangle(...))`.
- Use `self.play(FadeIn(background))` to animate overlays.

Timing and pacing
- Pass `run_time` to `self.play` or animation constructors to control duration.
- Chain `self.play` calls sequentially; use `self.play(AnimationGroup(..., lag_ratio=...))` for parallel steps.

Best practices
- Prefer raw strings for backslashes in `Text`/`MathTex`.
- Keep scenes under ~10 animations; reuse helper methods for repeated captions.
- Call `self.wait()` briefly after major transitions for legibility.
- Use `config.frame_width`/`config.frame_height` for layout-aware sizes.

See tutorials for worked examples: Quickstart (CreateCircle, SquareToCircle), `.animate` usage, and positioning.
"""

