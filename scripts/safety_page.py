"""Render the standalone safety portfolio using existing site metadata."""

from html import escape
import re
from urllib.parse import urlsplit


def _h(value):
    return escape(str(value), quote=True)


def _url(value):
    value = str(value).strip()
    if not value or any(ord(char) < 32 for char in value):
        raise ValueError("Safety page links must have a nonempty, valid URL.")
    scheme = urlsplit(value).scheme.lower()
    if scheme not in ("", "http", "https", "mailto") or value.startswith("//"):
        raise ValueError(f"Unsupported safety page URL: {value!r}")
    return value.lstrip("/") if value.startswith("/") else value


def _icon(symbol):
    return (
        '<svg class="safety-icon" viewBox="0 0 24 24" width="16" height="16" '
        'aria-hidden="true" focusable="false">'
        f'<use href="assets/icons/sprite.svg#{symbol}" width="24" height="24"></use></svg>'
    )


def _symbol(label, href):
    label = str(label).lower()
    if href.startswith("mailto:"):
        return "email"
    if "linkedin.com/" in href:
        return "linkedin"
    if "github.com/" in href:
        return "github"
    if "vimeo.com/" in href or "video" in label:
        return "video"
    if "poster" in label:
        return "poster"
    if "pdf" in label or urlsplit(href).path.lower().endswith(".pdf"):
        return "pdf"
    if "writing" in label or "post" in label or "paper" in label:
        return "book"
    return "document"


def _link(label, href, css="safety-link", symbol=None):
    href = _url(href)
    external = urlsplit(href).scheme in ("http", "https")
    new_tab = external or urlsplit(href).path.lower().endswith(".pdf")
    target = ' target="_blank" rel="noopener"' if new_tab else ""
    glyph = _icon(symbol or _symbol(label, href))
    return f'<a class="{_h(css)}" href="{_h(href)}"{target}>{glyph}<span>{_h(label)}</span></a>'


def _paragraphs(value, css=""):
    attribute = f' class="{_h(css)}"' if css else ""
    return "".join(
        f"<p{attribute}>{_h(part.strip())}</p>"
        for part in str(value).split("\n\n")
        if part.strip()
    )


def _anchor(value):
    value = str(value)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value):
        raise ValueError(f"Invalid safety page section ID: {value!r}")
    return value


def _paper_entry(paper, summary):
    primary = None
    for label in ("paper", "pdf"):
        primary = next(
            (item for item in paper.get("links", []) if item["label"].lower() == label),
            None,
        )
        if primary:
            break
    href = primary["url"] if primary else f'publications.html#{paper["id"]}'
    title = _link(paper["title"], href, "safety-paper-title", "book")
    other_links = "".join(
        _link(item["label"], item["url"], "safety-resource-button")
        for item in paper.get("links", [])
        if primary is None or item["url"] != primary["url"]
    )
    resources = f'<div class="safety-paper-links">{other_links}</div>' if other_links else ""
    venue = " · ".join(
        str(value) for value in (paper["venue"], paper.get("publication_note")) if value
    )
    availability = _paragraphs(paper.get("availability_note", ""), "safety-availability-note")
    return (
        '<li class="safety-paper">'
        f'<p class="safety-paper-venue">{_h(venue)}</p>'
        f"<h4>{title}</h4>"
        f'{_paragraphs(summary, "safety-paper-summary") if summary else ""}'
        f"{availability}{resources}</li>"
    )


def _entry_paper(paper_id, papers, entry):
    if paper_id not in papers:
        raise ValueError(f"Unknown publication ID in safety page: {paper_id!r}")
    paper = {**papers[paper_id], **entry.get("paper_overrides", {}).get(paper_id, {})}
    summary = entry.get("paper_summaries", {}).get(paper_id, "")
    return _paper_entry(paper, summary)


def _resource_card(resource, level=3):
    title = _link(resource["label"], resource["url"], "safety-resource-title")
    meta = (
        f'<p class="safety-resource-meta">{_h(resource["meta"])}</p>'
        if resource.get("meta") else ""
    )
    description = _paragraphs(resource.get("description", ""), "safety-resource-description")
    return (
        '<article class="safety-resource-card">'
        f"{meta}<h{level}>{title}</h{level}>{description}</article>"
    )


def render_safety_page(site_data, safety_data, posts):
    """Return escaped body HTML; the caller supplies the document and stylesheets.

    Timeline and supplementary sections retain their authored order. Blog links are
    supplied through resources so this page never publishes or guesses post URLs.
    """
    profile = site_data.get("profile", {})
    papers = {paper["id"]: paper for paper in site_data.get("publications", [])}
    timeline = safety_data.get("timeline", [])
    sections = safety_data.get("sections", [])
    used_ids = {"main", "safety-heading", "safety-cv", "safety-cv-title"}
    for item in [*timeline, *sections]:
        item_id = _anchor(item["id"])
        if item_id in used_ids or f"safety-title-{item_id}" in used_ids:
            raise ValueError(f"Duplicate safety page section ID: {item_id!r}")
        used_ids.update((item_id, f"safety-title-{item_id}"))

    title = safety_data.get("title", "AI safety & interpretability")
    intro = safety_data.get(
        "intro", "Research, experience, and writing on understanding and aligning language models."
    )
    name = f'<p class="safety-name">{_h(profile["name"])}</p>' if profile.get("name") else ""
    focus = ""
    if safety_data.get("focus"):
        focus = '<ul class="safety-focus" aria-label="Focus areas">' + "".join(
            f"<li>{_h(topic)}</li>" for topic in safety_data["focus"]
        ) + "</ul>"
    actions = []
    if profile.get("cv_url"):
        actions.append(_link("Full CV", profile["cv_url"], "safety-action", "download"))
    if profile.get("email"):
        actions.append(_link("Email", "mailto:" + profile["email"], "safety-action", "email"))
    action_row = '<div class="safety-actions">' + "".join(actions) + "</div>" if actions else ""
    header = (
        '<header class="safety-header">'
        f'{name}<h1 id="safety-heading">{_h(title)}</h1>'
        f'<div class="safety-intro">{_paragraphs(intro)}</div>'
        f"{focus}{action_row}</header>"
    )

    entries = []
    for entry in timeline:
        entry_id = entry["id"]
        label = f'<p class="safety-label">{_h(entry["label"])}</p>' if entry.get("label") else ""
        bullets = ""
        if entry.get("bullets"):
            bullets = '<ul class="safety-bullets">' + "".join(
                f"<li>{_h(point)}</li>" for point in entry["bullets"]
            ) + "</ul>"
        resources = ""
        if "work" in entry:
            work_rows = []
            for item in entry["work"]:
                if "paper_id" in item:
                    work_rows.append(_entry_paper(item["paper_id"], papers, entry))
                else:
                    work_rows.append(
                        '<li class="safety-paper safety-work-resource">'
                        + _resource_card(item, level=4) + "</li>"
                    )
            paper_list = (
                '<ol class="safety-papers safety-work" aria-label="Selected research work">'
                + "".join(work_rows) + "</ol>"
                if work_rows else ""
            )
        else:
            paper_rows = [
                _entry_paper(paper_id, papers, entry) for paper_id in entry.get("paper_ids", [])
            ]
            paper_list = (
                '<ul class="safety-papers" aria-label="Related publications">'
                + "".join(paper_rows) + "</ul>"
                if paper_rows else ""
            )
            if entry.get("resources"):
                resources = '<div class="safety-inline-resources">' + "".join(
                    _resource_card(resource, level=4) for resource in entry["resources"]
                ) + "</div>"
        entries.append(
            '<li class="safety-entry">'
            f'<div class="safety-when"><p class="safety-date">{_h(entry["date"])}</p>{label}</div>'
            f'<article class="safety-card" id="{_h(entry_id)}" '
            f'aria-labelledby="safety-title-{_h(entry_id)}">'
            f'<h3 id="safety-title-{_h(entry_id)}">{_h(entry["title"])}</h3>'
            f'<div class="safety-description">{_paragraphs(entry["description"])}</div>'
            f"{bullets}{paper_list}{resources}</article></li>"
        )
    cv = (
        '<section class="safety-cv" id="safety-cv" aria-labelledby="safety-cv-title">'
        '<div class="safety-section-heading"><h2 id="safety-cv-title">Selected CV</h2></div>'
        '<ol class="safety-entries">' + "".join(entries) + "</ol></section>"
        if entries else ""
    )
    supplemental = []
    for section in sections:
        section_id = section["id"]
        cards = "".join(_resource_card(resource) for resource in section.get("resources", []))
        supplemental.append(
            f'<section class="safety-section" id="{_h(section_id)}" '
            f'aria-labelledby="safety-title-{_h(section_id)}">'
            '<div class="safety-section-heading">'
            f'<h2 id="safety-title-{_h(section_id)}">{_h(section["title"])}</h2>'
            f'{_paragraphs(section.get("description", ""), "safety-section-description")}</div>'
            f'<div class="safety-resource-grid">{cards}</div></section>'
        )
    return '<div class="safety-page">' + header + cv + "".join(supplemental) + "</div>"
