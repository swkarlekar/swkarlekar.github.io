# Writing blog posts

Write posts as Markdown files directly in this folder. Each post starts with YAML metadata between `---` lines. The builder ignores this README and filenames beginning with `_`, including the starter template.

1. Copy `_template.md` to a filename such as `my-first-post.md`.
2. Replace the metadata and body with your own writing.
3. Keep `draft: true` while preparing the post. Drafts have no public page and do not appear in the Blog index. Omitting `draft` also keeps a post in draft mode. After building, open `http://127.0.0.1:4173/preview/blog/` to read drafts and see the template layout locally.
4. Set `draft: false` when it is ready to include in the local website.
5. From the repository root, run:

   ```sh
   .venv/bin/python scripts/build_site.py
   ```

The builder creates `blog.html` and published post pages at `posts/<slug>.html`. Edit the Markdown sources rather than the generated HTML. Building changes local files only; it does not deploy the website.

Use `.venv/bin/python scripts/build_site.py --watch` to rebuild automatically when you save Markdown, then refresh the browser. The [repository README](../../README.md#blog) has the one-time environment setup and local server instructions. Draft preview files are excluded from deployment. Changing a post back to a draft or removing its source removes its generated public page on the next build.

## Metadata

- `title`, `date`, and `summary` are required. The summary is a short description for the blog index.
- `date` accepts `YYYY-MM-DD` or an ISO timestamp with a timezone, such as `2026-10-18T14:30:00-04:00`. Quote dates in the YAML. Posts appear latest first by publication date.
- `slug` is optional and controls the final URL; by default it is the filename without `.md`. Use lowercase letters and numbers separated by single hyphens. Changing a filename or slug can change the URL; retain an explicit slug when renaming a file to keep its URL stable.
- `updated` is optional and accepts the same formats as `date`.
- `tags` is an optional YAML list, such as `[Research, Notes]`.
- `draft` is a Boolean: `true` or `false`, without quotes. Its default is `true`.

## Body and images

Use Markdown headings, paragraphs, links, lists, tables, strikethrough, and fenced code blocks. Start body headings at `##`; the page already displays the post title. LaTeX math rendering is not enabled.

Use local images rather than remote images, for example:

```md
![A useful description of the image](/images/blog/file.webp)
```

Place the optimized image in `images/blog/` at the repository root. Use Markdown rather than inline HTML or JavaScript. Ordinary links to external sources are fine.

Link to another post using its generated URL, such as `/posts/my-first-post.html`. Links to headings within a post use ordinary fragments such as `#a-section-heading`; the builder maps these to its generated heading anchors.
