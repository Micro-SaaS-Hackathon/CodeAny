from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from .logging_utils import get_logger
import time
from typing import Optional
from contextlib import contextmanager

log = get_logger("compile")
_compile_sem: Optional[threading.BoundedSemaphore] = None


def _get_compile_sem() -> threading.BoundedSemaphore:
    global _compile_sem
    if _compile_sem is None:
        try:
            size = int(os.getenv("MANIM_MAX_PARALLEL", "2") or 2)
        except Exception:
            size = 2
        _compile_sem = threading.BoundedSemaphore(max(1, size))
    return _compile_sem


@contextmanager
def _limit_parallelism():
    sem = _get_compile_sem()
    sem.acquire()
    try:
        yield
    finally:
        try:
            sem.release()
        except Exception:
            pass


def _ensure_image(image: str) -> bool:
    """Ensure the docker image exists locally; pull if missing (requires network)."""
    try:
        subprocess.run(
            ["docker", "image", "inspect", image],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=float(os.getenv("MANIM_DOCKER_INSPECT_TIMEOUT_S", "8") or 8),
        )
        return True
    except subprocess.TimeoutExpired:
        log.warning(f"Docker inspect timeout | image={image}")
        return False
    except Exception:
        try:
            log.info(f"Docker pulling image | image={image}")
            subprocess.run(
                ["docker", "pull", image],
                check=True,
                timeout=float(os.getenv("MANIM_DOCKER_PULL_TIMEOUT_S", "120") or 120),
            )
            return True
        except subprocess.TimeoutExpired:
            log.warning(f"Docker pull timeout | image={image}")
            return False
        except Exception as e:
            log.warning(f"Docker pull failed | image={image} | err={e}")
            return False


def _workdir_base() -> Path:
    base = os.getenv("MANIM_TMP_DIR")
    if base:
        p = Path(base).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    # Default to a user cache path to avoid dev reload loops on repo changes
    # and to remain under /Users for Docker Desktop file sharing on macOS.
    # Example: ~/.cache/cursly/manim_runs
    home_cache = Path.home() / ".cache" / "cursly" / "manim_runs"
    home_cache.mkdir(parents=True, exist_ok=True)
    return home_cache

def compile_manim_to_mp4(module_id: str, manim_code: str) -> Optional[str]:
    """Compile Manim code to MP4 via Docker sandbox.

    Returns absolute path to MP4 on success, else None.
    Does not execute the code directly; uses dockerized `manim` tool with network disabled.
    """
    if not shutil.which("docker"):
        log.warning("Docker not available; skipping Manim compile")
        return None

    with _limit_parallelism():
        # Work directory (under a Docker-shared path)
        base = _workdir_base()
        tmpdir = tempfile.mkdtemp(prefix=f"manim_{module_id}_", dir=str(base))
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
        log.info(f"Manim compile start | module={module_id} | workdir={str(work)} | file={pyfile.name}")

        image = os.getenv("MANIM_DOCKER_IMAGE", "manimcommunity/manim:stable")
        # Ensure image exists before running isolated network
        if not _ensure_image(image):
            log.warning(f"Skipping run; image unavailable | module={module_id} | image={image}")
            return None

        # Docker run; mounts tmpdir at /manim and writes output there
        cmd = [
            "docker", "run", "--rm", "--network=none",
            "--cpus=1", "--memory=1g", "--pids-limit=256",
        ]
        if os.getenv("MANIM_DOCKER_USER", "host").lower() != "none":
            cmd += ["-u", f"{os.getuid()}:{os.getgid()}"]
        cmd += [
            "-v", f"{str(work)}:/manim",
            image,
            "manim", "-qL", "-o", mp4_name, f"/manim/{pyfile.name}", "Lesson",
        ]
        try:
            start = time.time()
            log.info(f"Manim docker run | module={module_id} | image={image} | cmd={' '.join(cmd)}")
            res = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=float(os.getenv("MANIM_DOCKER_RUN_TIMEOUT_S", "180") or 180),
            )
            if res.stdout:
                log.info(f"Manim docker stdout | module={module_id} | preview={res.stdout[:240]}")
            if res.stderr:
                log.info(f"Manim docker stderr | module={module_id} | preview={res.stderr[:240]}")
            log.info(f"Manim docker done | module={module_id} | took={time.time()-start:.2f}s")
        except subprocess.TimeoutExpired:
            log.warning(f"Manim docker timeout | module={module_id}")
            return None
        except subprocess.CalledProcessError as e:
            log.warning(f"Manim compile error | module={module_id} | err={e} | stderr={(e.stderr or '')[:240]}")
            return None
        except Exception as e:
            log.warning(f"Manim compile error | module={module_id} | err={e}")
            return None

    out = work / "media" / "videos" / pyfile.stem / "480p15" / mp4_name
    if out.exists():
        try:
            size = out.stat().st_size
        except Exception:
            size = -1
        log.info(f"Manim compile ok | module={module_id} | output={out} | size={size}")
        return str(out)
    # Some versions may place output directly under /manim
    alt = work / mp4_name
    if alt.exists():
        log.info(f"Manim compile ok | module={module_id} | output={alt}")
        return str(alt)
    log.warning(f"Manim output not found | module={module_id} | looked=[{out}], alt=[{alt}]")
    return None
