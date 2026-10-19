# Sweta Karlekar's website

The active site uses the academic layout at the repository root. It is a small, independently implemented static design inspired by [al-folio](https://github.com/alshedivat/al-folio), using the original site's Raleway/Montserrat typography, photographs, gray palette, and blue accents. No client-side framework or third-party runtime requests are required.

## Editing

- Edit biography details, publications, projects, talks, Chalk Talk Notes, experience, teaching, service, honors, and links in `content/site.json`. The transcription disclaimer is stored alongside `chalk_talk_notes`.
- Talk descriptions accept plain text or a list of text and `{ "text": "link label", "url": "https://…" }` segments for inline links. The builder escapes both formats.
- Set `profile.cv_url` in that file to update both CV download buttons.
- Publication abstracts use the paper's verbatim wording. Their primary sources are recorded in `abstract_source_url`; the NeurIPS CARE abstract was supplied by the author. Keep abstracts separate from project descriptions.
- Set `selected_publications` to the publication IDs to feature on the homepage, in display order. The Publications page retains the full list.
- Edit page structure and introductory prose in `scripts/build_site.py`.
- Edit appearance in `assets/css/academic.css` and optional theme/search behavior in `assets/js/academic.js`.
- Edit the standalone AI safety page’s timeline and selected resources in `content/safety.json`; its appearance is in `assets/css/safety.css` and structure in `scripts/safety_page.py`. Publication titles and links come from `content/site.json`, and selected blog titles, dates, and descriptions come from their Markdown metadata. Resource descriptions support safe inline Markdown emphasis, such as `**bold text**`.
- Rebuild the six main HTML pages, standalone AI safety page, blog posts, and bibliography with `.venv/bin/python scripts/build_site.py`.
- Preview locally with `python3 -m http.server 4173 --bind 127.0.0.1`, then open `http://127.0.0.1:4173/`.

Generated pages are committed so GitHub Pages can serve them without installing a build tool. The `academic/` HTML files redirect earlier design-preview links to the main pages. The original homepage's research and awards fragments are also forwarded to their new pages.

`ai-safety.html` is a standalone portfolio of safety and interpretability work, with a selected-CV timeline, talks, and writing. It is omitted from the main navigation and has a `noindex` directive. It can be shared directly once published; it is an ordinary public page, not access controlled.

## Blog

Write posts as Markdown files in [`content/blog/`](content/blog/README.md). Copy `_template.md` to a new filename, then edit its metadata and body. The frontmatter holds the title, publication date, summary, tags, optional updated date and URL slug, and `draft` status. Posts default to drafts; set `draft: false` when a post is ready for the public Blog page.

The builder converts posts to static HTML before serving them. Readers load ordinary pages with no Markdown parser, content fetch, or extra JavaScript. Published posts are listed newest first at `blog.html`, with individual pages at `posts/<slug>.html`. Drafts and the template have local previews at `preview/blog/`; they are excluded from both deployment paths. Changing a published post to a draft, removing its source, or changing its slug removes its obsolete generated page on the next successful build. Keep the same explicit slug to preserve an existing URL.

Create the isolated build environment once (Python 3.10 or newer):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
```

Then rebuild after saving a post:

```sh
.venv/bin/python scripts/build_site.py
```

Or keep a content watcher running in a separate terminal:

```sh
.venv/bin/python scripts/build_site.py --watch
```

The watcher rebuilds when Markdown, `content/site.json`, `content/safety.json`, or either stylesheet changes. Refresh the browser after saving. It does not start a server, commit, sync, or publish anything. The usual local server remains `python3 -m http.server 4173 --bind 127.0.0.1`. Open `/blog.html` for the public layout or `/preview/blog/` for draft previews.

Build-only dependencies are pinned in `requirements-build.txt`: [markdown-it-py](https://pypi.org/project/markdown-it-py/) renders Markdown, [PyYAML](https://pypi.org/project/PyYAML/) reads metadata, and `mdurl` is the Markdown parser's URL dependency. The isolated environment, source Markdown, and build dependencies are excluded from the published site. Raw HTML is displayed as text; post images use local paths. Put public blog images directly in `images/blog/` and reference them as `/images/blog/example.webp`.

Run the blog checks with `.venv/bin/python -m unittest discover -s scripts -p 'test_blog*.py'`. Run `.venv/bin/python scripts/package_site.py` to prepare the publication allowlist after building. These commands do not publish the site; GitHub sync waits for the author's explicit instruction.

## Archived designs

`_archive/classic-optimized/` contains the optimized classic layout, with its assets and documents. `_archive/original-79d8555/` contains the untouched tracked website from commit `79d855576353986ad328be370dd1d0174272e6ac`. Each snapshot is self-contained and includes a SHA-256 manifest and restoration instructions. Treat those snapshots as historical; their obsolete scripts are not part of the active website.

`_config.yml` excludes `_archive/`, authoring files, and local comparisons from GitHub Pages' Jekyll output. For an explicit deployment artifact, run `.venv/bin/python scripts/package_site.py`; its allowlist creates `dist/` with only the active website, published blog pages, compatibility redirects, fonts, icons, optimized photos, and PDF downloads. It does not include the archive or drafts. Publish that output if using a host that serves files directly without Jekyll. Packaging does not deploy anything.

The local comparison remains at `/preview/`, with desktop/mobile frames of the archive and active design. It is excluded from publication.

`/preview/portrait-comparison.html` compares the Codex portrait crop with `images/IMG_4959_cropped.png`, including separate homepage previews. The uploaded crop is resized without additional cropping.

## Assets

Original unoptimized photography, icon fonts, and Sass are preserved in the archive. The active site uses responsive optimized photographs, two locally hosted text fonts, and a small SVG icon sprite. Font and icon licenses are retained beside the assets. Research-material PDF URLs are retained for compatibility; historical resumes are kept in `files/old_resumes/`.

The current portrait uses the author's background-cleaned version, `images/IMG_4959_cropped_artifacts_removed.png` (1834×2488), preserving the selected crop without additional cropping. The site serves WebP copies at 480×651 and 960×1302, with JPEG fallbacks, exported at quality 80 with personal metadata removed. The full-size source photos are kept locally and ignored by Git; source photos and the previous headshot copies are excluded from deployment. The original crop comparison remains in the local preview. The personal introduction photo also uses WebP with a JPEG fallback.

Content updates in this draft draw from the research CV, verified primary publication records, and author-supplied updates. The current download is the fall 2026 CV. The mechanistic-topic-model paper is listed as TACL 2026, presented at EMNLP 2026. Publication presentation types are stored separately from their venues so labels remain consistent across the site.
