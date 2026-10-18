"""Regression checks for author mistakes and untrusted Markdown/frontmatter."""
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

import yaml

try:
    from .blog_posts import BlogError, load_posts, read_post, reading_minutes, render_markdown
except ImportError:
    from blog_posts import BlogError, load_posts, read_post, reading_minutes, render_markdown


class HTML(HTMLParser):
    def __init__(self, value):
        super().__init__()
        self.elements = []
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class MarkdownTests(unittest.TestCase):
    def test_nested_markdown_fences_and_extensions(self):
        value = render_markdown('''## A *nested* heading

> A quote with **bold** and [a link](https://example.org/?a=1&b=2).
>
> - one
>   - two

```python
print("<script>")
```

| Name | Value |
| :--- | ---: |
| ~~old~~ | `new` |
''')
        tags = [tag for tag, attrs in HTML(value).elements]
        for tag in ["h2", "em", "blockquote", "strong", "a", "ul", "pre", "code", "table", "thead", "tbody", "s"]:
            self.assertIn(tag, tags)
        self.assertEqual(tags.count("ul"), 2)
        self.assertIn('class="language-python"', value)
        self.assertIn('&lt;script&gt;', value)
        self.assertIn('href="https://example.org/?a=1&amp;b=2"', value)
        self.assertNotIn('style=', value)
        self.assertIn('class="text-right"', value)

    def test_raw_html_and_attribute_injection_are_text(self):
        value = render_markdown('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[link](https://example.org/ "x\\\" onmouseover=alert(1)")')
        elements = HTML(value).elements
        self.assertNotIn("script", [tag for tag, attrs in elements])
        self.assertNotIn("img", [tag for tag, attrs in elements])
        self.assertTrue(all(not key.startswith("on") for tag, attrs in elements for key in attrs))
        self.assertIn('&lt;script&gt;', value)

    def test_dangerous_schemes_are_not_links(self):
        for address in ["javascript:alert(1)", "jav&#x61;script:alert(1)", "vbscript:evil", "data:text/html,evil", "file:///etc/passwd", "ftp://example.org/a"]:
            with self.subTest(address=address):
                self.assertNotIn("a", [tag for tag, attrs in HTML(render_markdown(f"[bad]({address})")).elements])
        value = render_markdown('[mail](mailto:me@example.org) [local](../cv.html#main)')
        self.assertEqual([attrs['href'] for tag, attrs in HTML(value).elements if tag == 'a'],
                         ['mailto:me@example.org', '../cv.html#main'])

    def test_images_stay_local_and_do_not_eagerly_load(self):
        for address in ["https://example.org/a.png", "//example.org/a.png", "///example.org/a.png"]:
            with self.subTest(address=address), self.assertRaisesRegex(BlogError, "local paths"):
                render_markdown(f"![description]({address})")
        for address in ["images/diagram.png", "../images/diagram.png", "/images/diagram.png"]:
            attrs = next(attrs for tag, attrs in HTML(render_markdown(f'![A & B]({address})')).elements if tag == 'img')
            self.assertEqual(attrs['src'], address)
            self.assertEqual(attrs['alt'], 'A & B')
            self.assertEqual(attrs['loading'], 'lazy')

    def test_heading_ids_are_stable_and_unique(self):
        body = '[Jump](#cafe-code) [Top](#main)\n\n## Café & `code`\n\n## Café & code\n\n## Café & code-2\n\n## Café & code\n\n## 中文\n\n## 中文'
        value = render_markdown(body)
        ids = [attrs['id'] for tag, attrs in HTML(value).elements if tag == 'h2']
        self.assertEqual(ids, ['post-cafe-code', 'post-cafe-code-2', 'post-cafe-code-2-2', 'post-cafe-code-3', 'post-section', 'post-section-2'])
        self.assertIn('href="#post-cafe-code"', value)
        self.assertIn('href="#main"', value)
        self.assertEqual(value, render_markdown(body))

    def test_reading_time_has_useful_boundaries(self):
        self.assertEqual(reading_minutes(''), 1)
        self.assertEqual(reading_minutes('word ' * 200), 1)
        self.assertEqual(reading_minutes('word ' * 201), 2)


class PostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write(self, name='example.md', metadata=None, body='A post.\n'):
        if metadata is None:
            metadata = 'title: Example\ndate: 2026-10-18\nsummary: A concise description.\ndraft: false'
        path = self.directory / name
        path.write_text(f'---\n{metadata}\n---\n{body}', encoding='utf-8')
        return path

    def test_loads_types_body_and_default_slug(self):
        path = self.write(metadata='title: Example\ndate: 2026-10-18\nupdated: 2026-10-18T12:30:00+02:00\nsummary: A concise description.\ntags: [Research, NLP]\ndraft: false', body='## Heading\n\nBody.\n')
        post, = load_posts(self.directory)
        self.assertEqual(post.source, path)
        self.assertEqual(post.slug, 'example')
        self.assertIs(type(post.date), date)
        self.assertIs(type(post.updated), datetime)
        self.assertEqual(post.tags, ('Research', 'NLP'))
        self.assertEqual(post.body, '## Heading\n\nBody.\n')

    def test_draft_default_and_explicit_preview(self):
        self.write(metadata='title: Draft\ndate: 2026-10-18\nsummary: Not public.')
        self.assertEqual(load_posts(self.directory), [])
        post, = load_posts(self.directory, include_drafts=True)
        self.assertTrue(post.draft)

    def test_explicit_template_read_keeps_it_a_draft(self):
        path = self.write('_template.md', 'title: Example\ndate: 2026-10-18\nsummary: A template.\nslug: example')
        self.assertEqual(load_posts(self.directory, include_drafts=True), [])
        self.assertTrue(read_post(path).draft)

    def test_ordering_handles_timezones_and_ties(self):
        for name, published in [('zeta', '2026-10-18'), ('alpha', '2026-10-18T00:00:00Z'),
                                ('later', '2026-10-18T03:00:00+02:00'), ('old', '2026-10-17')]:
            self.write(name + '.md', f'title: {name}\ndate: {published}\nsummary: Description.\ndraft: false')
        self.assertEqual([p.slug for p in load_posts(self.directory)], ['later', 'alpha', 'zeta', 'old'])

    def test_duplicate_slugs_include_unpublished_drafts(self):
        self.write()
        path = self.write('draft.md', 'title: Draft\ndate: 2026-10-19\nsummary: Hidden.\nslug: example')
        with self.assertRaisesRegex(BlogError, 'duplicate slug') as error:
            load_posts(self.directory)
        self.assertIn(str(path), str(error.exception))

    def test_ignored_sources_and_missing_directory(self):
        for name in ['README.md', '_template.md', '.private.md', 'not-markdown.txt']:
            (self.directory / name).write_text('not a post')
        self.assertEqual(load_posts(self.directory), [])
        self.assertEqual(load_posts(self.directory / 'missing'), [])

    def test_symlink_file_and_directory_are_rejected(self):
        original = self.write('_original.md')
        (self.directory / 'linked.md').symlink_to(original)
        with self.assertRaisesRegex(BlogError, 'symlink'):
            load_posts(self.directory)
        alias = self.directory / 'alias'
        alias.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaisesRegex(BlogError, 'symlink'):
            load_posts(alias)

    def test_yaml_code_tags_and_duplicate_fields_are_rejected(self):
        for metadata in ['title: !!python/object/apply:os.system ["echo unsafe"]',
                         'title: First\ntitle: Second\ndate: 2026-10-18\nsummary: Description.',
                         '? [title, date]\n: invalid']:
            with self.subTest(metadata=metadata):
                self.write(metadata=metadata)
                with self.assertRaises(BlogError) as error:
                    load_posts(self.directory)
                self.assertIn('example.md', str(error.exception))
        self.assertIsInstance(yaml.safe_load('date: 2026-10-18')['date'], date)
        self.assertIs(yaml.safe_load('yes'), True)

    def test_bad_fields_values_and_dates_have_source_context(self):
        good = {'title': 'Example', 'date': '2026-10-18', 'summary': 'Description.', 'draft': False}
        cases = [({'unexpected': 1}, 'unknown'), ({'title': ''}, 'title'), ({'summary': []}, 'summary'),
                 ({'date': '2026-02-30'}, 'date'), ({'date': '2026-10-18T12:30:00'}, 'timezone'),
                 ({'date': '20261018'}, 'date'), ({'updated': '2026-10-17'}, 'updated'),
                 ({'updated': '2026-10-17T23:59:59Z'}, 'updated'),
                 ({'slug': '../escape'}, 'slug'), ({'slug': 'double--hyphen'}, 'slug'),
                 ({'slug': 'Uppercase'}, 'slug'), ({'slug': 'bad_slug'}, 'slug'),
                 ({'tags': 'NLP'}, 'tags'), ({'tags': ['NLP', 'NLP']}, 'duplicates'),
                 ({'draft': 'false'}, 'draft'), ({'draft': 0}, 'draft')]
        for changes, message in cases:
            with self.subTest(changes=changes):
                self.write(metadata=yaml.safe_dump(good | changes))
                with self.assertRaisesRegex(BlogError, message) as error:
                    load_posts(self.directory)
                self.assertIn('example.md', str(error.exception))
        self.write(metadata='title: Example\ndate: 2026-10-18\nsummary: Description.\ndraft: yes')
        with self.assertRaisesRegex(BlogError, 'draft'):
            load_posts(self.directory)

    def test_missing_frontmatter_fields_and_closing_delimiter(self):
        path = self.directory / 'example.md'
        for value in ['# No metadata', '---\ntitle: Unclosed', '---\n- list\n---\nBody',
                      '---\ntitle: Example\ndate: 2026-10-18\n---\nBody']:
            with self.subTest(value=value):
                path.write_text(value)
                with self.assertRaises(BlogError) as error:
                    load_posts(self.directory)
                self.assertIn(str(path), str(error.exception))


if __name__ == '__main__':
    unittest.main()
