#!/usr/bin/env python3
"""Build the static academic website and Markdown blog."""
import argparse
from datetime import date
import hashlib
from html import escape
import json
from pathlib import Path
import sys
import time

from safety_page import render_safety_page

try:
    from blog_posts import BlogError, load_posts, read_post, reading_minutes, render_key_point, render_markdown
except ModuleNotFoundError as error:
    raise SystemExit(
        "Missing build dependencies. Run .venv/bin/python -m pip install -r "
        "requirements-build.txt, then use .venv/bin/python scripts/build_site.py."
    ) from error

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT
DATA = json.loads((ROOT / "content" / "site.json").read_text())
PROFILE = DATA["profile"]


def h(value):
    return escape(str(value), quote=True)


def url(value):
    # Keep previews portable under a GitHub Pages project subdirectory as well.
    return value.lstrip("/") if value.startswith("/") else value


def link(label, href, css="", new=False, asset_prefix=""):
    target = ' target="_blank" rel="noopener"' if new else ""
    label = label.replace("↗", "").replace("↓", "").strip()
    lower = label.lower()
    if href.startswith("mailto:"):
        symbol = "email"
    elif "linkedin.com/" in href:
        symbol = "linkedin"
    elif "github.com/" in href:
        symbol = "github"
    elif "scholar.google.com/" in href:
        symbol = "scholar"
    elif "x.com/" in href or "twitter.com/" in href:
        symbol = "twitter"
    elif "download" in lower and "bibtex" not in lower:
        symbol = "download"
    elif "bibtex" in lower:
        symbol = "code"
    elif "vimeo.com/" in href or "video" in lower:
        symbol = "video"
    elif "poster" in lower:
        symbol = "poster"
    elif "pdf" in lower:
        symbol = "pdf"
    elif "research" in lower or "publications" in lower:
        symbol = "book"
    else:
        symbol = "document"
    glyph = f'<svg class="icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><use href="{h(asset_prefix)}assets/icons/sprite.svg#{symbol}" width="24" height="24"></use></svg>'
    return f'<a class="{h(css)} icon-link" href="{h(url(href))}"{target}>{glyph}<span>{h(label)}</span></a>'


def document(title, page, body, *, prefix="", description=None, stylesheets=(), noindex=False):
    css_version = hashlib.sha256((ROOT / "assets/css/academic.css").read_bytes()).hexdigest()[:12]
    extra_styles = "".join(
        f'\n  <link rel="stylesheet" href="{h(prefix + path)}?v={hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12]}">'
        for path in stylesheets
    )
    robots = '\n  <meta name="robots" content="noindex, follow">' if noindex else ""
    nav = "".join(
        f'<a href="{h(prefix + href)}"' + (' aria-current="page"' if key == page else "") + f'>{label}</a>'
        for key, href, label in [("about", "index.html", "About"), ("publications", "publications.html", "Publications"),
                                 ("cv", "cv.html", "CV"), ("awards", "awards.html", "Awards"),
                                 ("blog", "blog.html", "Blog"), ("projects", "projects.html", "More")]
    )
    description = description or "Sweta Karlekar — Computer Science PhD student at Columbia University. Research in natural language processing, mechanistic interpretability, and probabilistic modeling."
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="description" content="{h(description)}">{robots}
  <meta name="theme-color" content="#f4f4f4">
  <title>{h(title)} · Sweta Karlekar</title>
  <link rel="icon" href="{h(prefix)}images/optimized/favicon-64.png" type="image/png">
  <link rel="stylesheet" href="{h(prefix)}assets/css/academic.css?v={css_version}">{extra_styles}
  <script src="{h(prefix)}assets/js/academic.js" defer></script>
</head>
<body data-page="{h(page)}">
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="wordmark" href="{h(prefix)}index.html">Sweta <strong>Karlekar</strong></a>
      <div class="header-controls">
        <nav aria-label="Main navigation">{nav}</nav>
        <button class="theme-toggle" type="button" aria-label="Switch color theme" hidden><span aria-hidden="true">◐</span></button>
      </div>
    </div>
  </header>
  <main id="main" class="page page-{h(page)}">{body}</main>
  <footer class="site-footer">
    <p>© {date.today().year} Sweta Karlekar <span aria-hidden="true">·</span> Columbia University</p>
    {link('Google Scholar', 'https://scholar.google.com/citations?user=P9lDUcEAAAAJ&hl=en', new=True, asset_prefix=prefix)}
  </footer>
</body>
</html>
'''


def authors(paper):
    values = []
    for author in paper["authors"]:
        label = f'<strong>{h(author)}</strong>' if author in ("Sweta Karlekar", "S. S. Karlekar") else h(author)
        if author in paper.get("equal_contribution", []):
            label += '<sup aria-label="equal contribution">*</sup>'
        values.append(label)
    return ", ".join(values)


def bibtex(paper):
    def tex(value):
        escapes = {"#": r"\#", "&": r"\&", "%": r"\%", "_": r"\_", "$": r"\$", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "\\": r"\textbackslash{}"}
        return "".join(escapes.get(char, char) for char in str(value))

    venue = paper.get("bibliography_venue", paper["venue"].split(" · ")[0])
    kind = paper.get("citation_type", "misc" if paper.get("arxiv_id") else "inproceedings")
    venue_field = {"article": "journal", "misc": "howpublished"}.get(kind, "booktitle")
    fields = [("title", paper["title"]), ("author", " and ".join(paper["authors"])), ("year", str(paper["year"])),
              (venue_field, "arXiv" if kind == "misc" else venue)]
    if paper.get("arxiv_id"):
        fields += [("eprint", paper["arxiv_id"]), ("archivePrefix", "arXiv")]
    if paper.get("publication_note"):
        fields += [("note", paper["publication_note"])]
    if paper["links"]:
        fields += [("url", paper["links"][0]["url"])]
    values = []
    for key, value in fields:
        value = value if key == "url" else tex(value)
        if key == "title":
            value = "{" + value + "}"
        values.append("  " + key + " = {" + value + "}")
    return "@" + kind + "{" + paper["id"] + ",\n" + ",\n".join(values) + "\n}"


def publication(paper, compact=False):
    venue_parts = [paper["venue"]]
    if paper.get("presentation_venue"):
        venue_parts.append("Presented at " + paper["presentation_venue"])
    if paper.get("presentation"):
        venue_parts.append(paper["presentation"])
    venue_label = " · ".join(venue_parts)
    resources = "".join(link(item["label"], item["url"], "resource-link", True) for item in paper["links"])
    if paper["links"]:
        title = f'<a href="{h(url(paper["links"][0]["url"]))}" target="_blank" rel="noopener">{h(paper["title"])}</a>'
    elif compact:
        title = f'<a href="publications.html#{h(paper["id"])}">{h(paper["title"])}</a>'
    else:
        title = h(paper["title"])
    resource_row = f'<div class="resource-links">{resources}</div>' if resources else ""
    citation = "" if compact else f'\n        <details><summary>BibTeX</summary><pre><code>{h(bibtex(paper))}</code></pre></details>'
    details = f'''<div class="publication-details">
        <details><summary>Abstract</summary><p>{h(paper['abstract'])}</p></details>{citation}
      </div>'''
    note = '<p class="contribution-note">* Equal contribution</p>' if paper.get("equal_contribution") else ""
    return f'''<article class="publication" id="{h(paper['id'])}" data-year="{paper['year']}">
      <div class="publication-marker"><span>{paper['year']}</span><span class="marker-line" aria-hidden="true"></span></div>
      <div class="publication-content">
        <p class="venue">{h(venue_label)}</p>
        <h3>{title}</h3>
        <p class="authors">{authors(paper)}</p>{note}
        {resource_row}{details}
      </div>
    </article>'''


def section_heading(label, number, href=None, action=None):
    more = link(action, href, "text-link") if href else ""
    return f'<div class="section-heading"><h2><span class="section-number" aria-hidden="true">{number}</span>{h(label)}</h2>{more}</div>'


def project_entry(project, compact=False):
    resources = "".join(link(item["label"], item["url"], "resource-link", True) for item in project["links"])
    context = f'<p class="eyebrow">{h(project["context"])}</p>' if project.get("context") else ""
    credits = f'<p class="project-credits">{h(project["credits"])}</p>' if project.get("credits") else ""
    return f'''<article class="project" id="{h(project['id'])}">
      <div class="project-marker" aria-hidden="true"><svg class="icon" viewBox="0 0 24 24"><use href="assets/icons/sprite.svg#book" width="24" height="24"></use></svg></div>
      <div><h3>{h(project['title'])}</h3>{context}{credits}<p>{h(project['summary'])}</p><div class="resource-links">{resources}</div></div>
    </article>'''


def inline_text(value):
    if isinstance(value, str):
        return h(value)
    parts = []
    for part in value:
        if isinstance(part, str):
            parts.append(h(part))
        else:
            parts.append(f'<a href="{h(url(part["url"]))}" target="_blank" rel="noopener">{h(part["text"])}</a>')
    return "".join(parts)


def material_entry(material):
    resources = "".join(link(item["label"], item["url"], "button", True) for item in material["links"])
    return f'''<article class="material-row" id="{h(material['id'])}"><div><h3>{h(material['title'])}</h3><p>{inline_text(material['summary'])}</p></div><div class="resource-links">{resources}</div></article>'''


def about():
    fellowships = {item["id"]: item for item in DATA["honors"] if item.get("kind") == "fellowship"}
    papers_by_id = {paper["id"]: paper for paper in DATA["publications"]}
    selected = "".join(publication(papers_by_id[paper_id], True) for paper_id in DATA["selected_publications"])
    interests = "".join(f'<li>{h(topic)}</li>' for topic in PROFILE["interests"])
    return f'''
    <div class="about-main">
    <section class="intro" id="about" aria-labelledby="profile-name">
      <div class="intro-copy">
        <h1 id="profile-name">Sweta <strong>Karlekar</strong></h1>
        <p>Hi! I'm a Ph.D. student in Computer Science at Columbia University, advised by <a href="{h(PROFILE['advisor_url'])}" target="_blank" rel="noopener">David Blei</a>.</p>
        <p>I’m a <a href="{h(fellowships['columbia-ai-ethics']['url'])}" target="_blank" rel="noopener">Columbia AI Ethics Fellow</a>, <a href="{h(fellowships['ndseg']['url'])}" target="_blank" rel="noopener">NDSEG Fellow</a>, and <a href="{h(fellowships['provost-doctoral']['url'])}" target="_blank" rel="noopener">Provost Doctoral Fellow</a>.</p>
        <p>My research spans natural language processing, mechanistic interpretability, and probabilistic modeling. I’m interested in the concepts language models learn, how we can understand them, and how we can reason about their reliability.</p>
        <p>Before Columbia, I was an applied machine learning researcher at Meta. I first worked on causal inference with the Bayesian Modeling team, then on AI safety with the Generative AI team.</p>
        <p>During my undergraduate studies at UNC Chapel Hill, I researched applications of NLP for social good, advised by <a href="https://www.cs.unc.edu/~mbansal/" target="_blank" rel="noopener">Mohit Bansal</a>.</p>
        <div class="intro-actions">
          {link('View research', 'publications.html', 'button button-primary')}
          {link('Download CV ↗', PROFILE['cv_url'], 'button', True)}
        </div>
        <div class="social-links" aria-label="Contact and profiles">
          {link('Email ↗', 'mailto:' + PROFILE['email'])}
          {link('Scholar ↗', 'https://scholar.google.com/citations?user=P9lDUcEAAAAJ&hl=en', new=True)}
          {link('GitHub ↗', 'https://github.com/swkarlekar', new=True)}
          {link('LinkedIn ↗', 'https://www.linkedin.com/in/swetakarlekar/', new=True)}
          {link('X / Twitter', PROFILE['twitter_url'], new=True)}
        </div>
      </div>
      <aside class="profile">
        <div class="portrait-wrap"><picture><source type="image/webp" srcset="images/optimized/headshot-2026-480.webp?v=cleaned-user-crop 480w, images/optimized/headshot-2026-960.webp?v=cleaned-user-crop 960w" sizes="(max-width: 680px) 229px, (max-width: 820px) 199px, (max-width: 1100px) 239px, (min-width: 1500px) 274px, 261px"><img class="portrait" src="images/optimized/headshot-2026-480.jpg?v=cleaned-user-crop" srcset="images/optimized/headshot-2026-480.jpg?v=cleaned-user-crop 480w, images/optimized/headshot-2026-960.jpg?v=cleaned-user-crop 960w" sizes="(max-width: 680px) 229px, (max-width: 820px) 199px, (max-width: 1100px) 239px, (min-width: 1500px) 274px, 261px" width="960" height="1302" alt="Sweta Karlekar" fetchpriority="high"></picture></div>
      </aside>
    </section>
    <section class="research-interests" aria-label="Research interests"><p class="eyebrow">Research interests</p><ul>{interests}</ul></section>
    <section class="updates" aria-labelledby="updates-title">
      <h2 id="updates-title">A few recent highlights</h2>
      <dl><div><dt>2026</dt><dd>Became a <a href="awards.html">Columbia AI Ethics Fellow</a> as part of the fall cohort.</dd></div>
      <div><dt>2026</dt><dd><a href="publications.html#care">CARE</a>, our work on robust concept directions, was accepted at NeurIPS.</dd></div>
      <div><dt>2026</dt><dd><a href="https://arxiv.org/abs/2507.23220" target="_blank" rel="noopener">Model Directions, Not Words</a> was accepted to TACL and will be presented at EMNLP 2026 in Budapest.</dd></div>
      <div><dt>2026</dt><dd><a href="https://arxiv.org/abs/2602.21585" target="_blank" rel="noopener">Duel-Evolve</a>, our work on test-time scaling with LLM self-preferences, appeared at the ICLR Workshop on Recursive Self Improvement (RSI).</dd></div>
      <div><dt>2026</dt><dd>Our work on <a href="https://openreview.net/forum?id=KzH1cLVU1R" target="_blank" rel="noopener">concept representations under distribution shifts</a> appeared at the ICLR Workshop on Unifying Concept Representation Learning (UCRL).</dd></div></dl>
    </section>
    <section class="selected-publications" id="research" aria-label="Selected publications">
      {section_heading('Selected publications', '01', 'publications.html', 'All publications ↗')}
      {selected}
    </section>
    </div>
    <section class="beyond" aria-labelledby="beyond-title">
      <picture><source type="image/webp" srcset="images/optimized/about-450.webp"><img src="images/optimized/about-450.jpg" width="450" height="600" alt="Sweta Karlekar in Golden Gate Park, San Francisco" loading="lazy"></picture>
      <div><p class="eyebrow">Beyond research</p><h2 id="beyond-title">A little about me</h2>
      <p>I care about the ways technology can influence society for good, and about making computer science more welcoming through communities like Girls Who Code and Rewriting the Code.</p>
      <p>Outside of research, I love cooking, reading science fiction and fantasy, going to jazz concerts, and painting little rocks.</p></div>
    </section>'''


def projects():
    project_rows = "".join(project_entry(project) for project in DATA.get("projects", []))
    talks = "".join(material_entry(talk) for talk in DATA.get("talks", []))
    notes = "".join(material_entry(note) for note in DATA.get("chalk_talk_notes", []))
    disclaimer = h(DATA.get("chalk_talk_notes_disclaimer", ""))
    project_intro = "Complete (or near-complete) non-archival research projects and exploratory work that I presented through posters or talks."
    talks_intro = "A small selection of presentations that I’m particularly proud of."
    notes_intro = "Whiteboard notes I made for presenting research, textbook chapters, etc."
    return f'''<header class="page-heading"><p class="eyebrow">Explorations & teaching</p><h1>Projects & talks</h1><div class="heading-links"><a href="#projects">Research projects</a><a href="#talks">Talks</a><a href="#chalk-talk-notes">Chalk Talk Notes</a></div></header>
    <section id="projects" aria-label="Additional Research Projects">{section_heading('Additional Research Projects', '01')}<div class="section-intro"><p>{h(project_intro)}</p></div>{project_rows}</section>
    <section id="talks" aria-label="Selected Presentations and Talks">{section_heading('Selected Presentations and Talks', '02')}<div class="section-intro"><p>{h(talks_intro)}</p></div>{talks}</section>
    <section id="chalk-talk-notes" aria-label="Chalk Talk Notes"><span id="lecture-notes" aria-hidden="true"></span>{section_heading('Chalk Talk Notes', '03')}<aside class="section-intro notes-disclaimer" aria-label="About these notes"><p>{h(notes_intro)}</p><p><strong>Disclaimer:</strong> {disclaimer}</p></aside>{notes}</section>'''


def publications():
    years = sorted({paper["year"] for paper in DATA["publications"]}, reverse=True)
    options = "".join(f'<option value="{year}">{year}</option>' for year in years)
    papers = "".join(publication(paper) for paper in DATA["publications"])
    return f'''
    <header class="page-heading"><p class="eyebrow">Research</p><h1>Publications</h1>
      <div class="heading-links">{link('Google Scholar ↗', 'https://scholar.google.com/citations?user=P9lDUcEAAAAJ&hl=en', 'text-link', True)}{link('Download BibTeX ↓', 'publications.bib', 'text-link')}</div>
    </header>
    <div class="publication-tools" hidden>
      <label class="search-field"><span>Search publications</span><input id="publication-search" type="search" placeholder="Search title, author, or topic…" autocomplete="off"></label>
      <label class="year-field"><span>Year</span><select id="publication-year"><option value="all">All years</option>{options}</select></label>
      <p id="publication-count" role="status" aria-live="polite">{len(DATA['publications'])} publications</p>
    </div>
    <div class="publication-list">{papers}</div>
    <p class="empty-state" hidden>No publications match your search. Try a different name or topic.</p>
    <p class="materials-link">Explore <a href="projects.html">projects, talks, and chalk talk notes</a> for more research materials.</p>'''


def timeline_entry(item, role_first=False):
    heading = item["role"] if role_first else item["organization"]
    subtitle = item["organization"] if role_first else item["role"]
    detail = f'<p>{h(item["detail"])}</p>' if item.get("detail") else ""
    return f'<article class="timeline-row"><p class="timeline-date">{h(item["dates"])}</p><div><h3>{h(heading)}</h3><p class="role">{h(subtitle)}</p>{detail}</div></article>'


def cv():
    education = "".join(timeline_entry({**item, "organization": item["institution"], "role": item["degree"]}) for item in DATA["education"])
    experience = "".join(timeline_entry(item) for item in DATA["experience"])
    teaching = "".join(timeline_entry(item) for item in DATA["teaching"])
    service = "".join(timeline_entry(item, role_first=True) for item in DATA["service"])
    return f'''
    <header class="page-heading heading-with-action"><div><p class="eyebrow">Background</p><h1>Curriculum vitae</h1></div>{link('Download full CV ↗', PROFILE['cv_url'], 'button button-primary', True)}</header>
    <section class="cv-section">{section_heading('Education', '01')}{education}</section>
    <section class="cv-section">{section_heading('Selected experience', '02')}{experience}</section>
    <section class="cv-section" id="teaching">{section_heading('Teaching', '03')}{teaching}</section>
    <section class="cv-section" id="service">{section_heading('Service and Volunteering', '04')}{service}</section>
    <section class="cv-endnote"><h2>Publications & recognition</h2><p>Explore <a href="publications.html">publications and research materials</a>, or see <a href="awards.html">fellowships, honors, and features</a>.</p></section>'''


def honor_entry(item):
    title = h(item["title"])
    if item.get("url"):
        title = f'<a href="{h(url(item["url"]))}" target="_blank" rel="noopener">{title}</a>'
    detail = f'<p>{h(item["detail"])}</p>' if item.get("detail") else ""
    return f'<li><span class="honor-date">{h(item["date"])}</span><div><h3>{title}</h3>{detail}</div></li>'


def awards():
    fellowships = [item for item in DATA["honors"] if item.get("kind") == "fellowship"]
    other_honors = [item for item in DATA["honors"] if item.get("kind") != "fellowship"]
    featured = "".join(honor_entry(item) for item in fellowships)
    honors = "".join(honor_entry(item) for item in other_honors)
    features = "".join(f'<li>{link(item["title"] + " ↗", item["url"], new=True)}</li>' for item in DATA["features"])
    return f'''
    <header class="page-heading"><p class="eyebrow">Recognition</p><h1>Awards & features</h1></header>
    <section class="fellowships-section" id="fellowships" aria-label="Fellowships">{section_heading('Fellowships', '01')}<ul class="honors-list">{featured}</ul></section>
    <section id="selected-honors" aria-label="Selected honors">{section_heading('Selected honors', '02')}<ul class="honors-list">{honors}</ul></section>
    <section class="features-section" id="featured-articles" aria-label="Featured articles">{section_heading('Featured articles', '03')}<ul class="features-list">{features}</ul></section>'''


BLOG_MARKER = '<!-- Generated blog page; edit content/blog/ instead. -->\n'


def post_date(value):
    return f'<time datetime="{h(value.isoformat())}">{value.strftime("%B")} {value.day}, {value.year}</time>'


def post_tags(post):
    if not post.tags:
        return ""
    return '<ul class="blog-tags" aria-label="Topics">' + "".join(f'<li>{h(tag)}</li>' for tag in post.tags) + '</ul>'


def post_reading_minutes(post):
    return reading_minutes("\n".join((*post.key_points, post.body)))


def post_summary(post):
    if not post.key_points:
        return ""
    items = "".join(f'<li>{render_key_point(point)}</li>' for point in post.key_points)
    return '<aside class="post-summary" aria-labelledby="article-summary-heading"><h2 id="article-summary-heading">Summary</h2><ul>' + items + '</ul></aside>'


def blog_index(posts):
    rows = "".join(
        f'''<article class="blog-entry">
          <div class="blog-entry-date">{post_date(post.date)}</div>
          <div><h2><a href="posts/{h(post.slug)}.html">{h(post.title)}</a></h2>
          <p>{h(post.summary)}</p>{post_tags(post)}
          <a class="blog-read-link" href="posts/{h(post.slug)}.html">Read post <span aria-hidden="true">·</span> {post_reading_minutes(post)} min read</a></div>
        </article>''' for post in posts
    )
    if not rows:
        rows = '<div class="blog-empty"><span class="blog-empty-line" aria-hidden="true"></span><p>Posts coming soon.</p></div>'
    return '''<header class="page-heading"><p class="eyebrow">Writing</p><h1>Blog</h1>
      <div class="blog-intro"><p>A space for my thoughts on research, AI safety, and other things I find important.</p>
      <aside class="section-intro blog-disclaimer" aria-label="About the opinions expressed here"><p>All opinions and claims expressed are my own (though the writing is often polished with chatbots) and subject to change.</p></aside></div>
    </header><div class="blog-list">''' + rows + '</div>'


def blog_post(post, *, preview=False):
    banner = '<aside class="draft-banner"><strong>Draft preview</strong><span>This preview is excluded from the published website.</span></aside>' if preview else ""
    prefix = "../../" if preview else "../"
    updated = f'<span>Updated {post_date(post.updated)}</span>' if post.updated else ""
    try:
        content = render_markdown(post.body)
    except BlogError as error:
        raise BlogError(f"{post.source}: {error}") from error
    body = f'''<article class="blog-post">
      <a class="blog-back" href="{prefix}blog.html">Back to Blog</a>{banner}
      <header class="blog-post-heading"><p class="blog-meta">{post_date(post.date)}<span>{post_reading_minutes(post)} min read</span>{updated}</p>
      <h1>{h(post.title)}</h1>{post_tags(post)}</header>{post_summary(post)}
      <div class="blog-prose">{content}</div>
    </article>'''
    return document(post.title, "blog", body, prefix=prefix, description=post.summary)


def validate_blog_output(directory, pages):
    """Check ownership of both output trees before changing generated pages."""
    parent = ROOT
    for part in directory.relative_to(ROOT).parts:
        parent /= part
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise BlogError(f"Blog output must use real directories: {parent}")
    old_pages = []
    for path in directory.glob("*.html"):
        if path.is_symlink() or not path.is_file():
            raise BlogError(f"Blog output must be a regular file: {path}")
        owned = path.read_bytes().startswith(BLOG_MARKER.encode("utf-8"))
        if path.name in pages and not owned:
            raise BlogError(f"Refusing to overwrite a handwritten page: {path}")
        if owned and path.name not in pages:
            old_pages.append(path)
    return old_pages


def write_blog_pages(directory, pages):
    """Replace only generated blog pages, removing obsolete generated URLs."""
    old_pages = validate_blog_output(directory, pages)
    directory.mkdir(parents=True, exist_ok=True)
    for filename, html in pages.items():
        (directory / filename).write_text(BLOG_MARKER + html, encoding="utf-8")
    for path in old_pages:
        path.unlink()


def safety_page(posts):
    content = json.loads((ROOT / "content" / "safety.json").read_text())
    writing = content.get("writing")
    if writing:
        published = {post.slug: post for post in posts}
        resources = []
        for slug in writing["post_slugs"]:
            if slug not in published:
                continue
            post = published[slug]
            resources.append({
                "label": post.title, "url": f"posts/{post.slug}.html",
                "description": post.summary,
                "meta": post.date.strftime("%B %Y"),
            })
        if resources:
            content.setdefault("sections", []).append({**writing, "resources": resources})
    return document(
        content["title"], "safety", render_safety_page(DATA, content, posts),
        description=content["intro"], stylesheets=("assets/css/safety.css",), noindex=True,
    )


def build():
    global DATA, PROFILE
    DATA = json.loads((ROOT / "content" / "site.json").read_text())
    PROFILE = DATA["profile"]
    all_posts = load_posts(ROOT / "content" / "blog", include_drafts=True)
    posts = [post for post in all_posts if not post.draft]
    # Render and validate everything before replacing any generated page.
    safety_html = safety_page(posts)
    public_pages = {post.slug + ".html": blog_post(post) for post in posts}
    draft_pages = {"post-" + post.slug + ".html": blog_post(post, preview=True) for post in all_posts if post.draft}
    template = ROOT / "content" / "blog" / "_template.md"
    if template.exists():
        draft_pages["_template.html"] = blog_post(read_post(template), preview=True)
    preview_rows = '<li><a href="_template.html">Example post layout</a></li>' if template.exists() else ""
    preview_rows += "".join(f'<li><a href="post-{h(post.slug)}.html">{h(post.title)}</a></li>' for post in all_posts if post.draft)
    draft_pages["index.html"] = document("Blog previews", "blog", '<header class="page-heading"><p class="eyebrow">Local previews</p><h1>Blog drafts</h1></header><ul class="draft-list">' + preview_rows + '</ul>', prefix="../../")
    validate_blog_output(ROOT / "posts", public_pages)
    validate_blog_output(ROOT / "preview" / "blog", draft_pages)
    write_blog_pages(ROOT / "posts", public_pages)
    write_blog_pages(ROOT / "preview" / "blog", draft_pages)
    for filename, title, key, body in [("index.html", "About", "about", about()),
                                       ("publications.html", "Publications", "publications", publications()),
                                       ("projects.html", "Projects & talks", "projects", projects()),
                                       ("cv.html", "CV", "cv", cv()),
                                       ("awards.html", "Awards & features", "awards", awards()),
                                       ("blog.html", "Blog", "blog", blog_index(posts))]:
        (DEST / filename).write_text(document(title, key, body))
    (DEST / "ai-safety.html").write_text(safety_html)
    (DEST / "publications.bib").write_text("\n\n".join(bibtex(paper) for paper in DATA["publications"]) + "\n")
    # Preserve links to the local design study after promoting it to the root.
    aliases = ROOT / "academic"
    aliases.mkdir(exist_ok=True)
    for filename in ("index.html", "publications.html", "projects.html", "cv.html", "awards.html"):
        (aliases / filename).write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0;url=../' + filename + '"><title>Sweta Karlekar</title></head><body><p>This page has moved to <a href="../' + filename + '">the main website</a>.</p></body></html>\n')
    (aliases / "publications.bib").write_text((DEST / "publications.bib").read_text())
    print(f"Built six main pages, the standalone AI safety page, {len(posts)} blog posts, local draft previews, and the bibliography.", flush=True)


def source_signature():
    paths = [ROOT / "content" / "site.json", ROOT / "content" / "safety.json",
             ROOT / "assets/css/academic.css", ROOT / "assets/css/safety.css"]
    paths.extend((ROOT / "content" / "blog").glob("*.md"))
    signature = []
    for path in sorted(paths):
        try:
            info = path.stat()
        except FileNotFoundError:
            continue  # Some editors replace a file atomically while saving.
        signature.append((str(path), info.st_mtime_ns, info.st_size))
    return tuple(signature)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", action="store_true", help="Rebuild when post Markdown, site content, or CSS changes; refresh the browser to see edits.")
    args = parser.parse_args()
    try:
        build()
    except (BlogError, OSError, ValueError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        if not args.watch:
            return 1
        # Keep watching if started while a Markdown file is still being edited.
    if not args.watch:
        return 0
    print("Watching content/blog/, site content, and CSS. Refresh the browser after saving. Ctrl-C stops the watcher.", flush=True)
    previous = source_signature()
    try:
        while True:
            time.sleep(0.75)
            current = source_signature()
            if current == previous:
                continue
            previous = current
            try:
                build()
            except (BlogError, OSError, ValueError) as error:
                print(f"Build failed; fix the source and save again: {error}", file=sys.stderr, flush=True)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
