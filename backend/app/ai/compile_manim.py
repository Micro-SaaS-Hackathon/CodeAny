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
        # Try a quick pull as a fallback (daemon might wake up)
        try:
            subprocess.run(
                ["docker", "pull", image],
                check=True,
                timeout=float(os.getenv("MANIM_DOCKER_PULL_TIMEOUT_S", "120") or 120),
            )
            return True
        except Exception as e:
            log.warning(f"Docker pull after inspect-timeout failed | image={image} | err={e}")
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

def _try_local_manim(work: Path, module_id: str, pyfile: Path, mp4_name: str) -> Optional[str]:
    """Attempt to use a local `manim` binary if available (no Docker).

    Returns the path to the mp4 if successful, else None.
    """
    if not shutil.which("manim"):
        return None
    cmd = [
        "manim", "-qL", "-o", mp4_name, str(pyfile), "Lesson",
    ]
    try:
        log.info(f"Local manim run | module={module_id} | cmd={' '.join(cmd)}")
        res = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(work),
            timeout=float(os.getenv("MANIM_LOCAL_RUN_TIMEOUT_S", "180") or 180),
        )
        if res.stdout:
            log.info(f"Local manim stdout | module={module_id} | preview={res.stdout[:240]}")
        if res.stderr:
            log.info(f"Local manim stderr | module={module_id} | preview={res.stderr[:240]}")
    except subprocess.TimeoutExpired:
        log.warning(f"Local manim timeout | module={module_id}")
        return None
    except subprocess.CalledProcessError as e:
        log.warning(f"Local manim error | module={module_id} | err={e} | stderr={(e.stderr or '')[:240]}")
        return None
    except Exception as e:
        log.warning(f"Local manim exec error | module={module_id} | err={e}")
        return None

    # Locate output (same conventions as docker path detection below)
    out = work / "media" / "videos" / pyfile.stem / "480p15" / mp4_name
    if out.exists():
        return str(out)
    alt = work / mp4_name
    return str(alt) if alt.exists() else None


def _try_ffmpeg_placeholder(work: Path, module_id: str, mp4_name: str, title: str = "Lesson") -> Optional[str]:
    """Generate a simple placeholder MP4 using ffmpeg if available.

    Creates a few seconds of black video with a title overlay.
    """
    if not shutil.which("ffmpeg"):
        return None
    seconds = int(os.getenv("MANIM_PLACEHOLDER_SECONDS", "5") or 5)
    size = os.getenv("MANIM_PLACEHOLDER_SIZE", "1280x720")
    text = title.replace("'", "\'")[:60]
    out = work / mp4_name
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={size}:d={seconds}",
        "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
        str(out),
    ]
    try:
        log.info(f"FFmpeg placeholder run | module={module_id} | cmd={' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(work))
        return str(out) if out.exists() else None
    except Exception as e:
        log.warning(f"FFmpeg placeholder failed | module={module_id} | err={e}")
        return None


def compile_manim_to_mp4(module_id: str, manim_code: str) -> Optional[str]:
    """Compile Manim code to MP4 via Docker sandbox.

    Returns absolute path to MP4 on success, else None.
    Does not execute the code directly; uses dockerized `manim` tool with network disabled.
    """
    use_docker = (os.getenv("MANIM_ENABLE_DOCKER", "1") != "0")
    use_local = (os.getenv("MANIM_ENABLE_LOCAL", "1") != "0")
    use_placeholder = (os.getenv("MANIM_ENABLE_PLACEHOLDER", "1") != "0")

    docker_available = bool(shutil.which("docker")) if use_docker else False
    if not docker_available:
        log.warning("Docker CLI not available or disabled; will try local/placeholder")

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
        if not docker_available or not _ensure_image(image):
            log.warning(f"Docker image unavailable; will try local/placeholder | module={module_id} | image={image}")
            # fall through to local/placeholder below
        else:
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
            except subprocess.CalledProcessError as e:
                log.warning(f"Manim compile error | module={module_id} | err={e} | stderr={(e.stderr or '')[:240]}")
            except Exception as e:
                log.warning(f"Manim compile error | module={module_id} | err={e}")

    # Try local manim fallback
    if use_local:
        out_local = _try_local_manim(work, module_id, pyfile, mp4_name)
        if out_local:
            return out_local

    # Try placeholder video for graceful UX
    if use_placeholder:
        ph = _try_ffmpeg_placeholder(work, module_id, mp4_name, title=f"Lesson {module_id}")
        if ph:
            return ph
        else:
            log.warning("Placeholder generation failed; returning no video")

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
