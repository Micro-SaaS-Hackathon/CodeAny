from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def compile_manim_to_mp4(module_id: str, manim_code: str) -> Optional[str]:
    """Compile Manim code to MP4 via Docker sandbox.

    Returns absolute path to MP4 on success, else None.
    Does not execute the code directly; uses dockerized `manim` tool with network disabled.
    """
    if not shutil.which("docker"):
        return None

    # Work directory
    tmpdir = tempfile.mkdtemp(prefix=f"manim_{module_id}_")
    work = Path(tmpdir)
    pyfile = work / f"{module_id}.py"
    mp4_name = f"{module_id}.mp4"

    # Ensure there is a Scene named Lesson; if not, prepend minimal stub
    code = manim_code or ""
    if "class Lesson(" not in code:
        code = (
            "# Auto-wrapped to ensure a `Lesson` Scene exists\n"
            + code
            + "\n\nfrom manim import *\n\nclass Lesson(Scene):\n    def construct(self):\n        self.add(Text('Lesson'))\n"
        )

    pyfile.write_text(code, encoding="utf-8")

    # Docker run; mounts tmpdir at /manim and writes output there
    cmd = [
        "docker", "run", "--rm", "--net=none",
        "--cpus=1", "--memory=1g", "--pids-limit=256",
        "-u", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{str(work)}:/manim",
        "manimcommunity/manim:stable",
        "manim", "-qL", "-o", mp4_name, f"/manim/{pyfile.name}", "Lesson",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except Exception:
        return None

    out = work / "media" / "videos" / pyfile.stem / "480p15" / mp4_name
    if out.exists():
        return str(out)
    # Some versions may place output directly under /manim
    alt = work / mp4_name
    return str(alt) if alt.exists() else None
