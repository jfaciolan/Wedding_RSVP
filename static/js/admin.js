/* Site Admin: copy-link buttons and auto-submitting filters. */
(function () {
  "use strict";
  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-copy]");
    if (!button) return;
    var input = document.getElementById(button.dataset.copy);
    if (!input) return;
    var done = function () {
      var label = button.dataset.label || (button.dataset.label = button.textContent);
      button.textContent = "Copied";
      setTimeout(function () { button.textContent = label; }, 1500);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(input.value).then(done);
    } else {
      input.select();
      document.execCommand("copy");
      done();
    }
  });

  document.addEventListener("change", function (event) {
    var select = event.target.closest("select[data-autosubmit]");
    if (select && select.form) select.form.requestSubmit ? select.form.requestSubmit() : select.form.submit();
  });
})();
