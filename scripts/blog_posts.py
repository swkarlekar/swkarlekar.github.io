"""Validate local blog sources and render Markdown at build time only."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import yaml


class BlogError(ValueError):
    """An author-facing error in a blog source."""


@dataclass(frozen=True)
class BlogPost:
    source: Path
    slug: str
    title: str
    date: date | datetime
    updated: date | datetime | None
    summary: str
    tags: tuple[str, ...]
    draft: bool
    body: str


class _FrontMatterLoader(yaml.SafeLoader):
    pass


# Parse dates ourselves, and accept true/false rather than YAML 1.1's yes/on.
# Copy the resolver lists so importing this module never changes safe_load().
_FrontMatterLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in values
          if tag not in {"tag:yaml.org,2002:timestamp", "tag:yaml.org,2002:bool"}]
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_FrontMatterLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$", re.IGNORECASE), list("tTfF")
)


def _unique_mapping(loader, node):
    values = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(
                None, None, "frontmatter field names must be strings", key_node.start_mark
            )
        if key in values:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate field {key!r}", key_node.start_mark
            )
        values[key] = loader.construct_object(value_node)
    return values


_FrontMatterLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
)
_FIELDS = {"title", "date", "updated", "summary", "slug", "tags", "draft"}
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})\Z"
)


def _date(value, field):
    if isinstance(value, str):
        try:
            if _DATE.fullmatch(value):
                return date.fromisoformat(value)
            if _TIMESTAMP.fullmatch(value):
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.utcoffset() is not None:
                    return parsed
        except ValueError:
            pass
    raise BlogError(f"{field} must be an ISO date (YYYY-MM-DD) or a timestamp with a timezone")


def _instant(value):
    # Date-only posts use midnight UTC for ordering alongside timestamped posts.
    return value if isinstance(value, datetime) else datetime.combine(value, time(), timezone.utc)


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise BlogError(f"{field} must be a nonempty string")
    return value.strip()


def _load_post(source):
    try:
        text = source.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            raise BlogError("expected YAML frontmatter beginning with ---")
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            raise BlogError("frontmatter is missing its closing ---")
        metadata = yaml.load("".join(lines[1:end]), Loader=_FrontMatterLoader)
        if not isinstance(metadata, dict):
            raise BlogError("frontmatter must be a mapping of named fields")
        unknown = set(metadata) - _FIELDS
        if unknown:
            raise BlogError("unknown frontmatter field(s): " + ", ".join(sorted(unknown)))
        for field in ("title", "date", "summary"):
            if field not in metadata:
                raise BlogError(f"missing required field {field!r}")
        title = _text(metadata["title"], "title")
        summary = _text(metadata["summary"], "summary")
        slug = metadata.get("slug", source.stem)
        if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
            raise BlogError("slug must contain lowercase letters/digits separated by single hyphens")
        published = _date(metadata["date"], "date")
        updated = _date(metadata["updated"], "updated") if "updated" in metadata else None
        if updated is not None and _instant(updated) < _instant(published):
            raise BlogError("updated must be on or after date")
        tags = metadata.get("tags", [])
        if not isinstance(tags, list):
            raise BlogError("tags must be a YAML list of nonempty strings")
        tags = tuple(_text(tag, "each tag") for tag in tags)
        if len(set(tags)) != len(tags):
            raise BlogError("tags must not contain duplicates")
        draft = metadata.get("draft", True)
        if type(draft) is not bool:
            raise BlogError("draft must be true or false (without quotes)")
        return BlogPost(source, slug, title, published, updated, summary, tags, draft,
                        "".join(lines[end + 1:]))
    except yaml.YAMLError as exc:
        message = getattr(exc, "problem", None) or str(exc)
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 2}" if mark else ""
        raise BlogError(f"{source}: invalid YAML{where}: {message}") from exc
    except (OSError, UnicodeError, BlogError) as exc:
        raise BlogError(f"{source}: {exc}") from exc


def read_post(path: Path) -> BlogPost:
    """Read one source, including an explicitly requested hidden/template draft."""
    source = Path(path)
    if source.is_symlink() or source.parent.is_symlink() or not source.is_file():
        raise BlogError(f"{source}: blog sources must be regular files, not symlinks")
    return _load_post(source)


def load_posts(directory: Path, *, include_drafts=False) -> list[BlogPost]:
    """Read direct .md children; validate all slugs before filtering drafts."""
    directory = Path(directory)
    if directory.is_symlink():
        raise BlogError(f"{directory}: blog directory must not be a symlink")
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise BlogError(f"{directory}: expected a directory")
    posts = []
    slugs = {}
    try:
        sources = sorted(directory.iterdir())
    except OSError as exc:
        raise BlogError(f"{directory}: {exc}") from exc
    for source in sources:
        if source.name.startswith((".", "_")) or source.name.lower() == "readme.md" or source.suffix != ".md":
            continue
        post = read_post(source)
        if post.slug in slugs:
            raise BlogError(f"{source}: duplicate slug {post.slug!r}; also used by {slugs[post.slug]}")
        slugs[post.slug] = source
        posts.append(post)
    posts.sort(key=lambda post: post.slug)
    posts.sort(key=lambda post: _instant(post.date), reverse=True)
    return [post for post in posts if include_drafts or not post.draft]


def _safe_link(value):
    # An allowlist also blocks javascript:, data:, file:, and obfuscated variants
    # after markdown-it has decoded Markdown escapes/entities and normalized URLs.
    if "\\" in value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    try:
        return urlsplit(value).scheme.lower() in {"", "https", "http", "mailto"}
    except ValueError:
        return False


def _tokens(tokens):
    for token in tokens:
        yield token
        if token.children:
            yield from _tokens(token.children)


def render_markdown(body: str) -> str:
    """Render CommonMark, tables and strikethrough without executable HTML."""
    markdown = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    markdown.validateLink = _safe_link
    tokens = markdown.parse(body)
    for token in _tokens(tokens):
        if token.type in {"th_open", "td_open"} and token.attrGet("style"):
            # The table extension's only styles are these alignments. Use CSS
            # classes so tables also work under the site's strict style-src CSP.
            alignment = token.attrs.pop("style").removeprefix("text-align:")
            if alignment in {"left", "center", "right"}:
                token.attrSet("class", f"text-{alignment}")
        if token.type == "image":
            src = token.attrGet("src") or ""
            parsed = urlsplit(src)
            if parsed.scheme or parsed.netloc or src.startswith("//") or "\\" in src:
                raise BlogError("Markdown images must use local paths; remote images are not allowed")
            token.attrSet("loading", "lazy")
            token.attrSet("decoding", "async")
    anchors = set()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        inline = tokens[index + 1]
        label = "".join(child.content for child in _tokens(inline.children or [])
                        if child.type in {"text", "code_inline"})
        ascii_label = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode().lower()
        base = re.sub(r"[^a-z0-9]+", "-", ascii_label).strip("-") or "section"
        anchor, suffix = base, 2
        while anchor in anchors:
            anchor = f"{base}-{suffix}"
            suffix += 1
        anchors.add(anchor)
        # Prefix author-provided headings so they cannot shadow document globals.
        token.attrSet("id", "post-" + anchor)
    for token in _tokens(tokens):
        if token.type == "link_open":
            href = token.attrGet("href") or ""
            if href.startswith("#") and unquote(href[1:]) in anchors:
                token.attrSet("href", "#post-" + unquote(href[1:]))
    return markdown.renderer.render(tokens, markdown.options, {})


def reading_minutes(body: str) -> int:
    """Approximate reading time at 200 words/minute, including code and captions."""
    words = len(re.findall(r"\b\w+(?:['’-]\w+)*\b", body))
    return max(1, (words + 199) // 200)
