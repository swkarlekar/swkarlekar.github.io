"""Exercise the real site builder/packager without writing into the repository."""
from contextlib import redirect_stdout
import copy
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import yaml


SCRIPTS = Path(__file__).resolve().parent
REPOSITORY = SCRIPTS.parent
with patch.object(sys, "path", [str(SCRIPTS), *sys.path]):
    import build_site as builder
    import package_site as packager
    from blog_posts import BlogError


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.navigation = []
        self._in_nav = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == 'nav':
            self._in_nav = attrs.get('aria-label') == 'Main navigation'
        if self._in_nav and tag == 'a':
            self.navigation.append(attrs)

    def handle_endtag(self, tag):
        if tag == 'nav':
            self._in_nav = False


class BlogBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='blog-build-tests-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.sources = self.root / 'content/blog'
        self.sources.mkdir(parents=True)
        actual_data = json.loads((REPOSITORY / 'content/site.json').read_text())
        (self.root / 'content/site.json').write_text(json.dumps(actual_data))
        (self.root / 'content/safety.json').write_bytes((REPOSITORY / 'content/safety.json').read_bytes())
        build_paths = patch.multiple(builder, ROOT=self.root, DEST=self.root,
                                     DATA=copy.deepcopy(actual_data), PROFILE=copy.deepcopy(actual_data['profile']))
        build_paths.start()
        self.addCleanup(build_paths.stop)
        package_paths = patch.object(packager, 'ROOT', self.root)
        package_paths.start()
        self.addCleanup(package_paths.stop)
        # Packaging checks paths and payload hashes, not PDF/image decoding. Tiny
        # fixtures keep these tests independent of large downloadable documents.
        for name in packager.REQUIRED_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'packaging fixture\n')
        for directory in ['assets/fonts', 'assets/icons']:
            path = self.root / directory
            path.mkdir(parents=True, exist_ok=True)
            (path / 'LICENSE.txt').write_text('Fixture license.\n')
        # Preserve real link targets and icon IDs without copying large PDFs.
        for source in (REPOSITORY / 'files').glob('*.pdf'):
            (self.root / 'files' / source.name).write_bytes(b'PDF download fixture\n')
        (self.root / 'assets/icons/sprite.svg').write_bytes(
            (REPOSITORY / 'assets/icons/sprite.svg').read_bytes())

    def post(self, name='post.md', *, slug=None, draft=False, published='2026-10-18',
             title='A real test post', summary='A useful summary.', tags=None, body='## Heading\n\nSome writing.\n'):
        metadata = dict(title=title, date=published, summary=summary, tags=tags or [])
        if slug is not None:
            metadata['slug'] = slug
        if draft is not None:
            metadata['draft'] = draft
        path = self.sources / name
        path.write_text('---\n' + yaml.safe_dump(metadata, sort_keys=False) + '---\n' + body)
        return path

    def build(self):
        with redirect_stdout(io.StringIO()):
            builder.build()

    def generated_snapshot(self):
        paths = [*self.root.glob('*.html'), self.root / 'publications.bib',
                 *self.root.glob('posts/*.html'), *self.root.glob('preview/blog/*.html'),
                 *self.root.glob('academic/*')]
        return {str(path.relative_to(self.root)): path.read_bytes() for path in paths if path.is_file()}

    def test_public_list_order_escaping_and_relative_document_assets(self):
        self.post('older.md', published='2026-10-16')
        title = 'New <img src=x onerror=alert(1)> & "quotes"'
        summary = 'Summary " onmouseover="evil() <script>evil()</script>'
        topic = '<svg onload=alert(1)>'
        self.post('newest.md', title=title, summary=summary, tags=[topic])
        self.post('private.md', draft=None, title='UNPUBLISHED-DRAFT-TITLE')
        self.post('_template.md', slug='example-layout', draft=True)
        self.build()
        index = (self.root / 'blog.html').read_text()
        index_page = Page(index)
        links = [attrs['href'] for tag, attrs in index_page.elements
                 if tag == 'a' and attrs.get('href', '').startswith('posts/')]
        self.assertEqual(links, ['posts/newest.html', 'posts/newest.html', 'posts/older.html', 'posts/older.html'])
        self.assertNotIn('UNPUBLISHED-DRAFT-TITLE', index)
        self.assertNotIn('<img src=x', index)
        self.assertNotIn('<svg onload=', index)
        self.assertNotIn('<script>evil()', index)
        self.assertIn('&lt;img', index)

        public_html = (self.root / 'posts/newest.html').read_text()
        page = Page(public_html)
        description = next(attrs['content'] for tag, attrs in page.elements
                           if tag == 'meta' and attrs.get('name') == 'description')
        self.assertEqual(description, summary)
        for tag, attrs in page.elements:
            self.assertFalse(any(key.startswith('on') or key == 'style' for key in attrs))
        self.assertEqual([attrs['href'] for attrs in page.navigation],
                         ['../index.html', '../publications.html', '../cv.html', '../awards.html', '../blog.html', '../projects.html'])
        self.assertEqual([attrs['href'] for attrs in page.navigation if attrs.get('aria-current') == 'page'], ['../blog.html'])
        css_version = hashlib.sha256((self.root / 'assets/css/academic.css').read_bytes()).hexdigest()[:12]
        self.assertIn(('link', {'rel': 'stylesheet', 'href': '../assets/css/academic.css?v=' + css_version}), page.elements)
        self.assertTrue(any(tag == 'script' and attrs.get('src') == '../assets/js/academic.js' for tag, attrs in page.elements))
        self.assertTrue(any(tag == 'link' and attrs.get('href') == '../images/optimized/favicon-64.png' for tag, attrs in page.elements))
        self.assertTrue(any(tag == 'use' and attrs.get('href') == '../assets/icons/sprite.svg#scholar' for tag, attrs in page.elements))
        self.assertTrue(any(tag == 'a' and attrs.get('href') == '../blog.html' for tag, attrs in page.elements))
        self.assertEqual(len([1 for tag, attrs in page.elements if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy']), 1)
        draft = (self.root / 'preview/blog/post-private.html').read_text()
        self.assertIn('Draft preview', draft)
        self.assertIn('href="../../blog.html"', draft)
        self.assertIn('src="../../assets/js/academic.js"', draft)
        self.assertFalse((self.root / 'posts/private.html').exists())
        self.assertTrue((self.root / 'preview/blog/_template.html').exists())

    def test_css_changes_invalidate_cached_styles_on_main_post_and_preview_pages(self):
        self.post('public.md')
        self.post('private.md', draft=True)
        self.build()
        pages = ['index.html', 'publications.html', 'cv.html', 'awards.html',
                 'blog.html', 'projects.html', 'posts/public.html',
                 'preview/blog/post-private.html', 'preview/blog/index.html']

        def stylesheet_urls():
            return {name: next(attrs['href'] for tag, attrs in Page((self.root / name).read_text()).elements
                               if tag == 'link' and attrs.get('rel') == 'stylesheet') for name in pages}

        original_urls = stylesheet_urls()
        self.build()
        self.assertEqual(stylesheet_urls(), original_urls)
        original_signature = builder.source_signature()
        stylesheet = self.root / 'assets/css/academic.css'
        stylesheet.write_text('.post-summary { background: aliceblue; }\n')
        self.assertNotEqual(builder.source_signature(), original_signature)
        self.build()
        for name, href in stylesheet_urls().items():
            self.assertNotEqual(href, original_urls[name])
            self.assertEqual(href.split('?', 1)[0], original_urls[name].split('?', 1)[0])
        self.assertEqual(len({href.split('?', 1)[1] for href in stylesheet_urls().values()}), 1)

    def test_safety_page_stays_unlisted_with_valid_links_and_separate_packaged_style(self):
        self.post('public.md', slug='could-ai-safety-make-ai-less-safe')
        self.build()
        safety_path = self.root / 'ai-safety.html'
        page = Page(safety_path.read_text())
        robots = next(attrs['content'] for tag, attrs in page.elements
                      if tag == 'meta' and attrs.get('name') == 'robots')
        self.assertEqual({value.strip() for value in robots.split(',')}, {'noindex', 'follow'})
        csp = [attrs['content'] for tag, attrs in page.elements
               if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy']
        self.assertEqual(len(csp), 1)
        for directive in ["default-src 'none'", "script-src 'self'", "style-src 'self'",
                          "base-uri 'none'", "form-action 'none'", "object-src 'none'"]:
            self.assertIn(directive, csp[0].split('; '))

        navigation = ['index.html', 'publications.html', 'cv.html',
                      'awards.html', 'blog.html', 'projects.html']
        self.assertEqual([attrs['href'] for attrs in page.navigation], navigation)
        main_pages = ['index.html', 'publications.html', 'cv.html',
                      'awards.html', 'blog.html', 'projects.html']
        for name in main_pages:
            main = Page((self.root / name).read_text())
            self.assertEqual([attrs['href'] for attrs in main.navigation], navigation)
            self.assertFalse(any(tag == 'a' and attrs.get('href') == 'ai-safety.html'
                                 for tag, attrs in main.elements))
            self.assertFalse(any(tag == 'link' and 'safety.css' in attrs.get('href', '')
                                 for tag, attrs in main.elements))

        ids = [attrs['id'] for tag, attrs in page.elements if 'id' in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        for tag, attrs in page.elements:
            for attribute in ['aria-labelledby', 'aria-describedby']:
                for identifier in attrs.get(attribute, '').split():
                    self.assertIn(identifier, ids)
            for attribute in ['href', 'src']:
                if attribute not in attrs:
                    continue
                address = urlsplit(attrs[attribute])
                if address.scheme or address.netloc:
                    continue
                target = (safety_path.parent / unquote(address.path)).resolve() if address.path else safety_path
                self.assertTrue(target.is_relative_to(self.root), attrs[attribute])
                self.assertTrue(target.is_file(), attrs[attribute])
                if address.fragment:
                    target_ids = {attributes['id'] for _, attributes in Page(target.read_text()).elements
                                  if 'id' in attributes}
                    self.assertIn(unquote(address.fragment), target_ids, attrs[attribute])

        def stylesheets():
            return [attrs['href'] for tag, attrs in Page(safety_path.read_text()).elements
                    if tag == 'link' and attrs.get('rel') == 'stylesheet']

        original_styles = stylesheets()
        self.assertEqual(len(original_styles), 2)
        safety_css = self.root / 'assets/css/safety.css'
        version = hashlib.sha256(safety_css.read_bytes()).hexdigest()[:12]
        self.assertEqual(original_styles[1], 'assets/css/safety.css?v=' + version)
        main_before = (self.root / 'index.html').read_bytes()
        signature = builder.source_signature()
        safety_css.write_text('.safety-page { color: navy; }\n')
        self.assertNotEqual(builder.source_signature(), signature)
        self.build()
        self.assertEqual(stylesheets()[0], original_styles[0])
        self.assertNotEqual(stylesheets()[1], original_styles[1])
        self.assertEqual((self.root / 'index.html').read_bytes(), main_before)

        source = self.root / 'scripts/safety_page.py'
        source.parent.mkdir()
        source.write_text('PRIVATE-SAFETY-RENDERER-SOURCE\n')
        packager.package_site()
        output = self.root / 'dist'
        entries = {entry['path'] for entry in json.loads((output / packager.MARKER_NAME).read_text())['files']}
        for name in ['ai-safety.html', 'assets/css/safety.css']:
            self.assertIn(name, entries)
            self.assertEqual((output / name).read_bytes(), (self.root / name).read_bytes())
        self.assertNotIn('content/safety.json', entries)
        self.assertNotIn('scripts/safety_page.py', entries)

    def test_safety_writing_uses_current_metadata_and_never_links_requested_drafts(self):
        source = self.root / 'content/safety.json'
        content = json.loads(source.read_text())
        content['writing']['post_slugs'] = ['selected-public', 'selected-draft', 'missing-post']
        source.write_text(json.dumps(content))
        self.post('public.md', slug='selected-public', title='Original public title',
                  summary='Original public summary.', published='2026-09-17')
        self.post('draft.md', slug='selected-draft', draft=True,
                  title='PRIVATE-DRAFT-TITLE', summary='PRIVATE-DRAFT-SUMMARY')
        self.build()
        self.assertIn('Original public title', (self.root / 'ai-safety.html').read_text())

        self.post('public.md', slug='selected-public', title='Updated title & direction',
                  summary='Updated public summary.', published='2026-10-18')
        self.build()
        html = (self.root / 'ai-safety.html').read_text()
        post_links = [attrs['href'] for tag, attrs in Page(html).elements
                      if tag == 'a' and attrs.get('href', '').startswith('posts/')]
        self.assertEqual(post_links, ['posts/selected-public.html'])
        self.assertIn('Updated title &amp; direction', html)
        self.assertIn('Updated public summary.', html)
        self.assertIn('October 2026', html)
        for private_or_stale in ['Original public title', 'Original public summary.',
                                 'PRIVATE-DRAFT-TITLE', 'PRIVATE-DRAFT-SUMMARY',
                                 'posts/selected-draft.html', 'posts/missing-post.html']:
            self.assertNotIn(private_or_stale, html)
        self.assertFalse((self.root / 'posts/selected-draft.html').exists())

        self.post('public.md', slug='selected-public', draft=True,
                  title='No longer public', summary='This is now a private draft.')
        self.build()
        html = (self.root / 'ai-safety.html').read_text()
        self.assertFalse(any(tag == 'a' and attrs.get('href', '').startswith('posts/')
                             for tag, attrs in Page(html).elements))
        self.assertNotIn('id="writing"', html)
        self.assertNotIn('No longer public', html)

    def test_draft_publication_rename_and_deletion_remove_obsolete_pages(self):
        self.post(draft=True, slug='original')
        self.build()
        self.assertTrue((self.root / 'preview/blog/post-original.html').exists())
        self.assertFalse((self.root / 'posts/original.html').exists())
        self.post(draft=False, slug='original')
        self.build()
        self.assertTrue((self.root / 'posts/original.html').exists())
        self.assertFalse((self.root / 'preview/blog/post-original.html').exists())
        self.post(draft=True, slug='original')
        self.build()
        self.assertFalse((self.root / 'posts/original.html').exists())
        self.assertTrue((self.root / 'preview/blog/post-original.html').exists())
        self.post(draft=False, slug='renamed')
        self.build()
        self.assertTrue((self.root / 'posts/renamed.html').exists())
        self.assertFalse((self.root / 'preview/blog/post-original.html').exists())
        self.post(draft=False, slug='final-name')
        self.build()
        self.assertFalse((self.root / 'posts/renamed.html').exists())
        self.assertTrue((self.root / 'posts/final-name.html').exists())
        (self.sources / 'post.md').unlink()
        self.build()
        self.assertFalse((self.root / 'posts/final-name.html').exists())
        self.assertIn('Posts coming soon.', (self.root / 'blog.html').read_text())

    def test_optional_summary_is_escaped_before_prose_and_counts_toward_reading_time(self):
        # The same 200-word body takes one minute alone; the summary moves it
        # across that boundary without changing the body or the card teaser.
        body = 'word ' * 200
        source = self.post('with-summary.md', body=body, summary='A separate card teaser.')
        metadata_text, original_body = source.read_text()[4:].split('---\n', 1)
        metadata = yaml.safe_load(metadata_text)
        metadata['key_points'] = ['<img src=x onerror="alert(1)"> **A literal point.**',
                                  '<script>evil()</script> & **Safe formatting.**',
                                  '**Third point.** Inline emphasis is *safe*.',
                                  '**Fourth point.** Inline code is `safe`.',
                                  '**Fifth point.** [Links](javascript:evil) stay inactive.']
        source.write_text('---\n' + yaml.safe_dump(metadata) + '---\n' + original_body)
        self.post('without-summary.md', body=body)
        self.build()

        html = (self.root / 'posts/with-summary.html').read_text()
        page = Page(html)
        self.assertIn(('aside', {'class': 'post-summary', 'aria-labelledby': 'article-summary-heading'}), page.elements)
        self.assertIn(('h2', {'id': 'article-summary-heading'}), page.elements)
        self.assertLess(html.index('class="post-summary"'), html.index('class="blog-prose"'))
        self.assertIn('&lt;img src=x onerror=&quot;alert(1)&quot;&gt;', html)
        self.assertIn('&lt;script&gt;evil()&lt;/script&gt; &amp; <strong>Safe formatting.</strong>', html)
        summary = html.split('<aside class="post-summary"', 1)[1].split('</aside>', 1)[0]
        self.assertEqual(summary.count('<li>'), 5)
        self.assertEqual(summary.count('<strong>'), 5)
        self.assertIn('<em>safe</em>', summary)
        self.assertIn('<code>safe</code>', summary)
        self.assertNotIn('<a ', summary)
        self.assertNotIn('img', [tag for tag, attrs in page.elements])
        self.assertEqual(sum(tag == 'script' for tag, attrs in page.elements), 1)
        self.assertTrue(all(not key.startswith('on') for tag, attrs in page.elements for key in attrs))
        self.assertIn('<span>2 min read</span>', html)

        without = (self.root / 'posts/without-summary.html').read_text()
        self.assertNotIn('class="post-summary"', without)
        self.assertNotIn('article-summary-heading', without)
        self.assertIn('<span>1 min read</span>', without)
        index = (self.root / 'blog.html').read_text()
        self.assertIn('A separate card teaser.', index)
        self.assertIn('·</span> 2 min read', index)
        self.assertIn('·</span> 1 min read', index)
        self.assertNotIn('Safe formatting.', index)

    def test_handwritten_page_survives_and_cannot_be_overwritten_or_packaged(self):
        (self.root / 'posts').mkdir()
        path = self.root / 'posts/handwritten.html'
        original = b'<!doctype html><p>Keep this manually written page.</p>\n\xff'
        path.write_bytes(original)
        self.post()
        self.build()
        self.assertEqual(path.read_bytes(), original)
        self.post('collision.md', slug='handwritten')
        with self.assertRaisesRegex(BlogError, 'handwritten'):
            self.build()
        self.assertEqual(path.read_bytes(), original)
        with self.assertRaisesRegex(packager.PackagingError, 'not generated'):
            packager.collect_inputs()

    def test_preview_index_slug_does_not_collide_with_listing(self):
        self.post('index.md', draft=True, title='A draft whose slug is index')
        self.build()
        listing = (self.root / 'preview/blog/index.html').read_text()
        draft = (self.root / 'preview/blog/post-index.html').read_text()
        self.assertIn('href="post-index.html"', listing)
        self.assertIn('<h1>A draft whose slug is index</h1>', draft)
        self.assertIn('Draft preview', draft)
        self.assertNotIn('<h1>Blog drafts</h1>', draft)

    def test_preview_ownership_failure_leaves_public_outputs_unchanged(self):
        self.post(title='Original title')
        self.build()
        handwritten = self.root / 'preview/blog/post-future.html'
        handwritten.write_bytes(b'Manually written preview.\n')
        snapshot = self.generated_snapshot()
        self.post(title='New title must not be written during a failed build')
        self.post('future.md', draft=True)
        with self.assertRaisesRegex(BlogError, 'handwritten'):
            self.build()
        self.assertEqual(self.generated_snapshot(), snapshot)

    def test_symlinked_preview_parent_is_rejected_before_any_writes(self):
        outside = self.root / 'outside-preview'
        outside.mkdir()
        (self.root / 'preview').symlink_to(outside, target_is_directory=True)
        self.post()
        snapshot = self.generated_snapshot()
        with self.assertRaisesRegex(BlogError, 'real directories'):
            self.build()
        self.assertEqual(self.generated_snapshot(), snapshot)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root / 'posts').exists())

    def test_invalid_metadata_or_markdown_leaves_all_generated_files_unchanged(self):
        self.post(title='Original published title')
        self.build()
        snapshot = self.generated_snapshot()
        self.post(title='Changed title that must not be written on failure')
        invalid = self.sources / 'broken.md'
        invalid.write_text('---\ntitle: Missing the other required metadata\n---\nBody.\n')
        with self.assertRaisesRegex(BlogError, 'broken.md'):
            self.build()
        self.assertEqual(self.generated_snapshot(), snapshot)
        self.post('broken.md', body='![remote](https://example.org/tracker.png)')
        with self.assertRaisesRegex(BlogError, 'broken.md.*local paths'):
            self.build()
        self.assertEqual(self.generated_snapshot(), snapshot)

    def test_package_contains_only_public_post_html_and_allowlisted_assets(self):
        self.post('public.md')
        self.post('private.md', draft=True, body='PRIVATE-DRAFT-BODY')
        self.post('_template.md', slug='example-layout', draft=True)
        self.build()
        for name in ['.venv/lib/dependency.py', 'preview/private.md', 'posts/source.md',
                     'images/blog/internal.svg', 'requirements-build.txt', 'content/blog/README.md']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('PRIVATE-NOT-A-DEPLOYMENT-INPUT')
        (self.root / 'images/blog/diagram.png').write_bytes(b'public image fixture')
        count, total_bytes = packager.package_site()
        output = self.root / 'dist'
        manifest = json.loads((output / packager.MARKER_NAME).read_text())
        entries = {record['path']: record for record in manifest['files']}
        actual = {str(path.relative_to(output)) for path in output.rglob('*') if path.is_file()}
        self.assertEqual(actual, set(entries) | {packager.MARKER_NAME})
        self.assertEqual(count, len(entries))
        self.assertEqual(total_bytes, sum(record['bytes'] for record in entries.values()))
        self.assertEqual([name for name in entries if name.startswith('posts/')], ['posts/public.html'])
        self.assertIn('blog.html', entries)
        self.assertIn('images/blog/diagram.png', entries)
        for name in entries:
            self.assertNotIn(Path(name).parts[0], ['content', 'preview', '.venv', 'scripts', '_archive'])
            self.assertNotIn(Path(name).suffix, ['.md', '.py'])
            if name.startswith('images/blog/'):
                self.assertNotEqual(Path(name).suffix, '.svg')
            source = self.root / name
            published = output / name
            self.assertEqual(source.read_bytes(), published.read_bytes())
            self.assertEqual(hashlib.sha256(published.read_bytes()).hexdigest(), entries[name]['sha256'])
            self.assertEqual(len(published.read_bytes()), entries[name]['bytes'])
            if name.endswith('.html'):
                self.assertNotIn('PRIVATE-DRAFT-BODY', published.read_text())
        self.assertFalse((output / 'posts/private.html').exists())
        self.assertFalse((output / 'preview').exists())
        # Repackaging after unpublishing must remove the previously public URL.
        self.post('public.md', draft=True)
        self.build()
        packager.package_site()
        self.assertFalse((output / 'posts/public.html').exists())
        updated = json.loads((output / packager.MARKER_NAME).read_text())
        self.assertFalse(any(entry['path'].startswith('posts/') for entry in updated['files']))


if __name__ == '__main__':
    unittest.main()
