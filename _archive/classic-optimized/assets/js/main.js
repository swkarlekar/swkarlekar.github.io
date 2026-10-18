/*
 * Progressive panel navigation for the original Indivisible theme.
 * Content remains readable if JavaScript is disabled or unavailable.
 */
(function () {
    'use strict';

    var panels = Array.prototype.slice.call(document.querySelectorAll('#wrapper > .panel'));
    var home = document.getElementById('home');
    if (!home || !panels.length) return;

    function panelForHash(hash) {
        var id;
        try {
            id = decodeURIComponent((hash || '').replace(/^#/, ''));
        } catch (error) {
            return home;
        }
        var candidate = document.getElementById(id);
        return panels.indexOf(candidate) === -1 ? home : candidate;
    }

    function loadImages(panel) {
        panel.querySelectorAll('img[data-src]').forEach(function (image) {
            // A selected panel is visible now; do not defer its image further.
            image.loading = 'eager';
            if (image.dataset.srcset) {
                image.srcset = image.dataset.srcset;
                image.removeAttribute('data-srcset');
            }
            image.src = image.dataset.src;
            image.removeAttribute('data-src');
        });
    }

    function activatePanel(moveFocus) {
        var selected = panelForHash(window.location.hash);
        loadImages(selected);
        panels.forEach(function (panel) {
            panel.hidden = panel !== selected;
        });
        document.body.classList.add('has-panel-navigation');

        if (moveFocus) {
            var heading = selected.querySelector('h1, h2');
            if (heading) {
                heading.setAttribute('tabindex', '-1');
                heading.focus({ preventScroll: true });
            }
            window.scrollTo(0, 0);
        }
    }

    document.addEventListener('click', function (event) {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        var link = event.target.closest('a[href^="#"]');
        if (!link) return;
        var href = link.getAttribute('href');
        var selected = panelForHash(href);
        // Leave non-panel fragment links to the browser.
        if (href !== '#' && href !== '#home' && selected === home) return;
        event.preventDefault();
        var hash = '#' + selected.id;
        if (window.location.hash === hash) activatePanel(true);
        else window.location.hash = hash;
    });

    window.addEventListener('hashchange', function () {
        activatePanel(true);
    });

    activatePanel(false);
})();
