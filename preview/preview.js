(function () {
  'use strict';
  var controls = document.querySelectorAll('[data-view]');
  controls.forEach(function (button) {
    button.addEventListener('click', function () {
      document.body.classList.toggle('mobile', button.dataset.view === 'mobile');
      controls.forEach(function (control) {
        control.setAttribute('aria-pressed', String(control === button));
      });
    });
  });
})();
