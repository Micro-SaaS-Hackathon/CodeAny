from __future__ import annotations

import html
import io
import re
import unicodedata
from datetime import datetime
from typing import Iterable, List, Tuple
from zipfile import ZIP_DEFLATED, ZipFile

from .models import CourseDetail, Module


def _slugify(value: str, fallback: str = "course") -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    collapsed = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-")
    slug = collapsed.lower()
    return slug or fallback


def _format_paragraphs(text: str) -> str:
    if not text:
        return "<p>No detailed content provided.</p>"
    paragraphs = re.split(r"\n{2,}", text.strip())
    parts: List[str] = []
    for para in paragraphs:
        lines = [html.escape(line.strip()) for line in para.splitlines() if line.strip()]
        if not lines:
            continue
        parts.append("<p>" + "<br/>".join(lines) + "</p>")
    return "\n".join(parts) if parts else "<p>No detailed content provided.</p>"


def _render_outline(outline: Iterable) -> str:
    items: List[str] = []
    for raw in outline or []:
        if isinstance(raw, dict):
            title = raw.get("title") or raw.get("heading") or raw.get("text")
            if title:
                items.append(f"<li>{html.escape(str(title))}</li>")
        elif raw is not None:
            items.append(f"<li>{html.escape(str(raw))}</li>")
    if not items:
        return ""
    return "<h3>Outline</h3><ul>" + "".join(items) + "</ul>"


def _render_module_html(module: Module, index: int) -> str:
    body_parts = [f"<h1>{html.escape(module.title or f'Module {module.moduleId or index}')}</h1>"]
    if module.text:
        body_parts.append(_format_paragraphs(module.text))
    outline_html = _render_outline(module.outline)
    if outline_html:
        body_parts.append(outline_html)
    if module.manimCode:
        body_parts.append(
            "<h3>Manim Code</h3><pre><code>" + html.escape(module.manimCode) + "</code></pre>"
        )
    if module.videoStorageId:
        body_parts.append(
            "<p><strong>Video Storage ID:</strong> " + html.escape(module.videoStorageId) + "</p>"
        )
    if module.imageStorageId:
        body_parts.append(
            "<p><strong>Image Storage ID:</strong> " + html.escape(module.imageStorageId) + "</p>"
        )
    if module.imageCaption:
        body_parts.append(
            "<p><em>Image Caption:</em> " + html.escape(module.imageCaption) + "</p>"
        )
    return "".join(body_parts)


def _render_overview_html(course: CourseDetail) -> str:
    meta_rows: List[Tuple[str, str]] = []
    for label, value in [
        ("Instructor", course.instructor or ""),
        ("Audience", course.audience or ""),
        ("Level", course.level_label or ""),
        ("Duration (weeks)", str(course.duration_weeks) if course.duration_weeks is not None else ""),
        ("Category", course.category or ""),
        ("Age Range", course.age_range or ""),
        ("Language", course.language or ""),
        ("Status", course.status or ""),
    ]:
        if value:
            meta_rows.append((label, value))
    meta_html = "".join(
        f"<tr><th align=\"left\">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>"
        for label, value in meta_rows
    )
    description_html = _format_paragraphs(course.description or "")
    return (
        f"<h1>{html.escape(course.title)}</h1>"
        f"<p><strong>Course ID:</strong> {html.escape(course.id)}</p>"
        + (f"<table>{meta_html}</table>" if meta_html else "")
        + "<h2>Description</h2>"
        + description_html
    )


def _build_manifest(course: CourseDetail, module_resources: List[Tuple[str, str, str]]) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    org_id = f"ORG-{course.id}"
    manifest_id = f"MANIFEST-{course.id}"
    overview_res_id = "RES-OVERVIEW"

    item_nodes = [
        (
            f"<item identifier=\"ITEM-OVERVIEW\" identifierref=\"{overview_res_id}\">"
            f"<title>{html.escape(course.title)} Overview</title>"
            "</item>"
        )
    ]
    resource_nodes = [
        f"<resource identifier=\"{overview_res_id}\" type=\"webcontent\" href=\"course_overview.html\">"
        "<file href=\"course_overview.html\"/></resource>"
    ]

    for idx, (res_id, filename, title) in enumerate(module_resources, start=1):
        item_nodes.append(
            f"<item identifier=\"ITEM-MOD-{idx}\" identifierref=\"{res_id}\">"
            f"<title>{html.escape(title or f'Module {idx}')}</title>"
            "</item>"
        )
        resource_nodes.append(
            f"<resource identifier=\"{res_id}\" type=\"webcontent\" href=\"{html.escape(filename)}\">"
            f"<file href=\"{html.escape(filename)}\"/></resource>"
        )

    schema_location = (
        "http://www.imsglobal.org/xsd/imscp_v1p1 "
        "http://www.imsglobal.org/profile/cc/ccv1p3/derived_schema/imscp_v1p1.xsd "
        "http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1 "
        "http://www.imsglobal.org/profile/cc/ccv1p3/derived_schema/imscc_v1p3_imscp_v1p1.xsd "
        "http://www.imsglobal.org/xsd/imsmd_v1p2 "
        "http://www.imsglobal.org/profile/cc/ccv1p3/derived_schema/imsmd_v1p2p2.xsd"
    )

    manifest = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<manifest identifier=\"{manifest_id}\"
    xmlns=\"http://www.imsglobal.org/xsd/imscp_v1p1\"
    xmlns:imsmd=\"http://www.imsglobal.org/xsd/imsmd_v1p2\"
    xmlns:imscc=\"http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1\"
    xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"
    xsi:schemaLocation=\"{schema_location}\">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.3.0</schemaversion>
    <imsmd:lom>
      <imsmd:general>
        <imsmd:title><imsmd:string language=\"en\">{html.escape(course.title)}</imsmd:string></imsmd:title>
        <imsmd:description><imsmd:string language=\"en\">{html.escape(course.description or 'Course package exported')}</imsmd:string></imsmd:description>
        <imsmd:keyword><imsmd:string language=\"en\">cursly</imsmd:string></imsmd:keyword>
      </imsmd:general>
      <imsmd:lifecycle>
        <imsmd:contribute>
          <imsmd:role><imsmd:value>author</imsmd:value></imsmd:role>
          <imsmd:entity>{html.escape(course.instructor or 'Cursly')}</imsmd:entity>
          <imsmd:date>
            <imsmd:datetime>{timestamp}</imsmd:datetime>
          </imsmd:date>
        </imsmd:contribute>
      </imsmd:lifecycle>
    </imsmd:lom>
  </metadata>
  <organizations default=\"{org_id}\">
    <organization identifier=\"{org_id}\" structure=\"rooted-hierarchy\">
      <title>{html.escape(course.title)}</title>
      {''.join(item_nodes)}
    </organization>
  </organizations>
  <resources>
    {''.join(resource_nodes)}
  </resources>
</manifest>
"""
    return manifest


def build_imscc_package(course: CourseDetail) -> Tuple[bytes, str]:
    modules = list(course.modules or [])
    module_entries: List[Tuple[str, str, str]] = []  # (resource_id, filename, title)
    buffer = io.BytesIO()

    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        overview_html = _render_overview_html(course)
        zf.writestr("course_overview.html", overview_html)

        for idx, module in enumerate(modules, start=1):
            res_id = f"RES-MOD-{idx}"
            filename = f"modules/module-{idx:02d}.html"
            module_html = _render_module_html(module, idx)
            zf.writestr(filename, module_html)
            module_entries.append((res_id, filename, module.title or f"Module {idx}"))

        manifest = _build_manifest(course, module_entries)
        zf.writestr("imsmanifest.xml", manifest)

    slug = _slugify(course.title, fallback=f"course-{course.id}"[:32])
    package_name = f"{slug or 'course'}.imscc"
    return buffer.getvalue(), package_name
