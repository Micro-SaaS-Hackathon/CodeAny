from __future__ import annotations
import asyncio
from typing import Any, Dict, List, TypedDict, Optional

from .nodes.syllabus import generate_syllabus
from .nodes.text_writer import write_text
from .nodes.manim_writer import write_manim_code
from .nodes.gemini_image import generate_gemini_image_or_fallback
from .compile_manim import compile_manim_to_mp4
from .persist_convex import persist_course_and_modules
from .logging_utils import get_logger
from ..convex_client import ConvexClient


class ModuleSpec(TypedDict):
    id: str
    title: str
    objectives: List[str]
    outline: List[str]


class ModuleArtifact(TypedDict, total=False):
    module_id: str
    title: str
    outline: List[str]
    text: str
    manim_code: str
    gemini_output: Dict[str, Any]
    video_path: Optional[str]


class CourseState(TypedDict, total=False):
    topic: str
    level: str
    constraints: Dict[str, Any]
    syllabus: List[ModuleSpec]
    modules: Dict[str, ModuleArtifact]
    course_package: Dict[str, Any]


async def build_course_graph(state: CourseState, *, convex: ConvexClient, progress_cb=None, existing_course_id: Optional[str] = None) -> Dict[str, Any]:
    """High-level orchestration of course generation.

    Uses async fan-out to generate per-module assets, then compiles Manim and persists.
    """
    log = get_logger("graph")
    def report(pct: int, status: str):
        if progress_cb:
            try:
                asyncio.create_task(progress_cb(pct, status))
            except RuntimeError:
                # If no loop running, call sync
                progress_cb(pct, status)

    topic = state.get("topic", "")
    level = state.get("level", "beginner")
    constraints = state.get("constraints", {})

    try:
        log.info(f"Graph start | topic={topic} | level={level}")
        # Prefer LangGraph orchestration if available
        from langgraph.graph import StateGraph, START, END  # type: ignore
        from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore

        def _set(state_in: CourseState) -> CourseState:
            return state_in

        async def _syll(state_in: CourseState) -> CourseState:
            rep = state_in.get("_report")  # type: ignore
            if rep:
                rep(5, "creating")
            topic_l = state_in.get("topic", "")
            level_l = state_in.get("level", "beginner")
            cons_l = state_in.get("constraints", {})
            s = await generate_syllabus(topic_l, level_l, cons_l)
            state_in["syllabus"] = s  # type: ignore
            if rep:
                rep(20, "creating")
            return state_in

        async def _fanout(state_in: CourseState) -> CourseState:
            specs: List[ModuleSpec] = state_in.get("syllabus", [])  # type: ignore
            cons_l = state_in.get("constraints", {})
            lang = cons_l.get("language", "en")
            async def process(spec: ModuleSpec) -> ModuleArtifact:
                text, code, gim = await asyncio.gather(
                    write_text(spec, lang, cons_l),
                    write_manim_code(spec, lang),
                    generate_gemini_image_or_fallback(spec, lang, cons_l),
                )
                return {
                    "module_id": spec["id"],
                    "title": spec["title"],
                    "outline": spec.get("outline", []),
                    "text": text,
                    "manim_code": code,
                    "gemini_output": gim,
                }
            log.info(f"Fanout start | modules={len(specs)}")
            mods = await asyncio.gather(*[process(s) for s in specs])
            log.info(f"Fanout done | modules={len(mods)}")
            state_in["modules"] = {m["module_id"]: m for m in mods}  # type: ignore
            rep = state_in.get("_report")  # type: ignore
            if rep:
                rep(60, "rendering")
            return state_in

        async def _compile(state_in: CourseState) -> CourseState:
            mods_dict: Dict[str, ModuleArtifact] = state_in.get("modules", {})  # type: ignore
            async def _c(key: str, mart: ModuleArtifact):
                path = await asyncio.to_thread(compile_manim_to_mp4, mart["module_id"], mart.get("manim_code", ""))
                mart["video_path"] = path
                return key, mart
            log.info(f"Compile start | modules={len(mods_dict)}")
            items = await asyncio.gather(*[_c(k, v) for k, v in mods_dict.items()])
            log.info(f"Compile done | modules={len(items)}")
            state_in["modules"] = {k: v for k, v in items}  # type: ignore
            rep = state_in.get("_report")  # type: ignore
            if rep:
                rep(80, "uploading")
            return state_in

        async def _persist(state_in: CourseState) -> CourseState:
            topic_l = state_in.get("topic", "")
            level_l = state_in.get("level", "")
            mods_dict: Dict[str, ModuleArtifact] = state_in.get("modules", {})  # type: ignore
            mods_list = [mods_dict[k] for k in sorted(mods_dict.keys())]
            cons_l = state_in.get("constraints", {})
            course_payload = {
                "topic": topic_l,
                "level": level_l,
                "moduleCount": len(mods_list),
                "moduleIds": [m["module_id"] for m in mods_list],
                "createdAt": __import__("time").time(),
                "title": cons_l.get("title"),
                "description": cons_l.get("description"),
                "instructor": cons_l.get("instructor"),
                "audience": cons_l.get("audience"),
                "levelLabel": cons_l.get("level_label"),
                "durationWeeks": cons_l.get("duration_weeks"),
                "category": cons_l.get("category"),
                "ageRange": cons_l.get("age_range"),
                "language": cons_l.get("language", "en"),
                "status": "uploading",
                "progress": 80,
            }
            log.info("Persist start")
            pr = await persist_course_and_modules(convex=convex, course_payload=course_payload, modules=mods_list, existing_course_id=existing_course_id)
            log.info("Persist done")
            state_in["course_package"] = {
                "topic": topic_l,
                "level": level_l,
                "count_modules": len(mods_list),
                "modules": mods_list,
                "convex": {"courseId": pr.course_id, "moduleIds": pr.module_ids, "storage": pr.storage_ids},
            }
            rep = state_in.get("_report")  # type: ignore
            if rep:
                rep(95, "uploading")
            return state_in

        builder = StateGraph(CourseState)
        builder.add_node("syllabus", _syll)
        builder.add_node("fanout", _fanout)
        builder.add_node("compile", _compile)
        builder.add_node("persist", _persist)
        builder.add_edge(START, "syllabus")
        builder.add_edge("syllabus", "fanout")
        builder.add_edge("fanout", "compile")
        builder.add_edge("compile", "persist")
        builder.add_edge("persist", END)

        checkpointer = None
        try:
            checkpointer = SqliteSaver.from_conn_string("ai_state.sqlite")  # type: ignore
        except Exception:
            checkpointer = None

        graph = builder.compile(checkpointer=checkpointer) if checkpointer else builder.compile()
        # Inject progress reporter into state
        state["_report"] = report  # type: ignore
        out_state: CourseState = await graph.ainvoke(state)  # type: ignore
        course_package = out_state.get("course_package", {})  # type: ignore
        report(100, "ready")
        log.info("Graph done | status=ready")
        return course_package  # type: ignore
    except Exception:
        # Fallback async orchestration without LangGraph if library missing
        log.warning("LangGraph unavailable; using asyncio fallback")
        report(5, "creating")
        syllabus = await generate_syllabus(topic, level, constraints)
        state["syllabus"] = syllabus  # type: ignore
        report(20, "creating")

        async def process_module(spec: ModuleSpec) -> ModuleArtifact:
            lang = constraints.get("language", "en")
            text, code, gim = await asyncio.gather(
                write_text(spec, lang, constraints),
                write_manim_code(spec, lang),
                generate_gemini_image_or_fallback(spec, lang, constraints),
            )
            art: ModuleArtifact = {
                "module_id": spec["id"],
                "title": spec["title"],
                "outline": spec.get("outline", []),
                "text": text,
                "manim_code": code,
                "gemini_output": gim,
            }
            return art

        tasks = [process_module(spec) for spec in syllabus]
        modules_list = await asyncio.gather(*tasks)
        report(60, "rendering")

        # Compile Manim videos
        compile_tasks = []
        for m in modules_list:
            async def _compile(mart: ModuleArtifact):
                path = await asyncio.to_thread(compile_manim_to_mp4, mart["module_id"], mart.get("manim_code", ""))
                mart["video_path"] = path
                return mart
            compile_tasks.append(_compile(m))
        modules_list = await asyncio.gather(*compile_tasks)
        report(80, "uploading")

    # Persist to Convex or in-memory
    course_payload = {
        "topic": topic,
        "level": level,
        "moduleCount": len(modules_list),
        "moduleIds": [m["module_id"] for m in modules_list],
        "createdAt": __import__("time").time(),
        # mirror additional fields for UI if present
        "title": constraints.get("title"),
        "description": constraints.get("description"),
        "instructor": constraints.get("instructor"),
        "audience": constraints.get("audience"),
        "levelLabel": constraints.get("level_label"),
        "durationWeeks": constraints.get("duration_weeks"),
        "category": constraints.get("category"),
        "ageRange": constraints.get("age_range"),
        "language": constraints.get("language", "en"),
        "status": "uploading",
        "progress": 80,
    }

    pr = await persist_course_and_modules(convex=convex, course_payload=course_payload, modules=modules_list, existing_course_id=existing_course_id)
    report(95, "uploading")

    # Final package
    course_package = {
        "topic": topic,
        "level": level,
        "count_modules": len(modules_list),
        "modules": modules_list,
        "convex": {
            "courseId": pr.course_id,
            "moduleIds": pr.module_ids,
            "storage": pr.storage_ids,
        },
    }
    state["course_package"] = course_package
    report(100, "ready")
    log.info("Graph done | status=ready (fallback)")
    return course_package


async def run_course_build(
    *,
    topic: str,
    level: str,
    constraints: Dict[str, Any],
    convex: ConvexClient,
    progress_cb=None,
    existing_course_id: Optional[str] = None,
) -> Dict[str, Any]:
    state: CourseState = {"topic": topic, "level": level, "constraints": constraints}
    return await build_course_graph(state, convex=convex, progress_cb=progress_cb, existing_course_id=existing_course_id)
