/* Optional enhancements; every page and paper is readable without JavaScript. */
(function () {
  'use strict';
  // Keep bookmarks from the original panel-based homepage useful.
  if (document.body.dataset.page === 'about') {
    var legacyPages = { research: 'publications.html', projects: 'projects.html', awards: 'awards.html' };
    var legacyTarget = legacyPages[window.location.hash.slice(1)];
    if (Object.prototype.hasOwnProperty.call(legacyPages, window.location.hash.slice(1))) window.location.replace(legacyTarget);
  }
  var root = document.documentElement;
  var toggle = document.querySelector('.theme-toggle');
  var preference = window.matchMedia('(prefers-color-scheme: dark)');
  function theme() {
    return root.dataset.theme || (preference.matches ? 'dark' : 'light');
  }
  function updateToggle() {
    toggle.setAttribute('aria-label', 'Switch to ' + (theme() === 'dark' ? 'light' : 'dark') + ' mode');
  }
  try {
    var saved = localStorage.getItem('sweta-academic-theme');
    if (saved === 'dark' || saved === 'light') root.dataset.theme = saved;
  } catch (error) { /* Storage can be unavailable in a private or restricted context. */ }
  if (toggle) {
    toggle.hidden = false;
    updateToggle();
    toggle.addEventListener('click', function () {
      root.dataset.theme = theme() === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('sweta-academic-theme', root.dataset.theme); } catch (error) {}
      updateToggle();
    });
    if (preference.addEventListener) preference.addEventListener('change', updateToggle);
  }

  var tools = document.querySelector('.publication-tools');
  if (!tools) return;
  var search = document.getElementById('publication-search');
  var year = document.getElementById('publication-year');
  var papers = Array.from(document.querySelectorAll('.publication-list .publication'));
  var empty = document.querySelector('.empty-state');
  var count = document.getElementById('publication-count');
  function filter() {
    var query = search.value.trim().toLocaleLowerCase();
    var shown = 0;
    papers.forEach(function (paper) {
      var match = (year.value === 'all' || year.value === paper.dataset.year) && paper.textContent.toLocaleLowerCase().includes(query);
      paper.hidden = !match;
      if (match) shown += 1;
    });
    count.textContent = shown + (shown === 1 ? ' publication' : ' publications');
    empty.hidden = shown !== 0;
  }
  search.addEventListener('input', filter);
  year.addEventListener('change', filter);
  tools.hidden = false;
})();
