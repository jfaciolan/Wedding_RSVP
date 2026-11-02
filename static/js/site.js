/* Public site: nav menu, FAQ accordion, attending toggle, guest stepper. */
(function () {
  "use strict";

  // ----- Mobile nav menu -----
  var nav = document.querySelector("[data-nav]");
  var toggle = document.querySelector("[data-nav-toggle]");
  if (nav && toggle) {
    var setOpen = function (open) {
      nav.classList.toggle("nav--open", open);
      toggle.setAttribute("aria-expanded", String(open));
    };
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    nav.querySelectorAll(".nav__links a").forEach(function (link) {
      link.addEventListener("click", function () { setOpen(false); });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  // ----- FAQ accordion: each button toggles only its own answer -----
  document.querySelectorAll("[data-accordion] .faq-item__button").forEach(function (button) {
    var panel = document.getElementById(button.getAttribute("aria-controls"));
    if (!panel) return;
    button.addEventListener("click", function () {
      var open = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", String(!open));
      panel.classList.toggle("is-open", !open);
    });
  });

  // ----- RSVP form -----
  var form = document.querySelector("[data-rsvp-form]");
  if (!form) return;

  var guestsField = form.querySelector("[data-guests-field]");
  var radios = form.querySelectorAll('input[name="attending"]');

  function syncAttending() {
    var declined = false;
    radios.forEach(function (radio) {
      radio.closest(".radio-card").classList.toggle("is-checked", radio.checked);
      if (radio.checked && radio.value === "no") declined = true;
    });
    if (guestsField) guestsField.hidden = declined;
  }
  radios.forEach(function (radio) { radio.addEventListener("change", syncAttending); });
  syncAttending();

  var stepper = form.querySelector("[data-stepper]");
  if (stepper) {
    var input = stepper.querySelector("input");
    var minus = stepper.querySelector('[data-step="-1"]');
    var plus = stepper.querySelector('[data-step="1"]');
    var status = form.querySelector("[data-stepper-status]");
    var min = parseInt(input.min, 10) || 1;
    var max = parseInt(input.max, 10) || min;

    var render = function (announce) {
      var value = parseInt(input.value, 10);
      if (isNaN(value)) value = min;
      value = Math.min(max, Math.max(min, value));
      input.value = value;
      minus.disabled = value <= min;
      plus.disabled = value >= max;
      if (announce && status) {
        status.textContent = value + (value === 1 ? " guest" : " guests");
      }
    };
    stepper.addEventListener("click", function (event) {
      var button = event.target.closest("[data-step]");
      if (!button || button.disabled) return;
      input.value = (parseInt(input.value, 10) || min) + parseInt(button.dataset.step, 10);
      render(true);
    });
    input.addEventListener("change", function () { render(true); });
    render(false);
  }

  // After a failed submit, bring the error summary into view for everyone.
  var summary = form.querySelector("[data-error-summary]");
  if (summary) summary.focus();
})();
