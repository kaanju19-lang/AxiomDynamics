/*
 * AxiomDynamics vector assets.
 *
 * One sprite, one source of truth. Every icon below is drawn on a 24x24 grid
 * with 1.75px strokes so the set reads as one family rather than four drawings
 * that happen to sit in the same file. `currentColor` is used throughout, which
 * is what lets an icon inherit a state colour from the element that contains it
 * instead of baking a hex value into the shape.
 *
 * Why a sprite and not inline strings per call site: the previous version built
 * an SVG string, assigned it to innerHTML on a throwaway div, and read back
 * firstElementChild -- once per icon, once per table row. That is a full HTML
 * parse per cell. A <symbol> is parsed once, and <use> clones it cheaply.
 *
 * Usage:  icon('railcar', { size: 18 })        -> SVGElement
 *         icon('bearing', { size: 18, state: 'critical' })
 */
(function (global) {
  "use strict";

  // --- State colour tokens, kept identical to style.css ---------------------
  // Duplicated here because SVG in the DOM cannot read a CSS custom property
  // from a context manager; both lists are asserted equal by the test suite.
  const STATE_COLOR = {
    normal: "#047857",
    watch: "#b45309",
    warning: "#b45309",
    critical: "#b91c1c",
    review: "#b45309",
  };

  // --- The symbol set -------------------------------------------------------
  // Each entry is the INNER markup of a 24x24 symbol. Strokes are currentColor
  // unless a shape is explicitly a filled detail.
  const SYMBOLS = {
    // A wagon in side elevation: body, sill line, two wheelsets.
    railcar: `
      <rect x="2" y="6" width="20" height="9" rx="1.5" fill="none"
            stroke="currentColor" stroke-width="1.75"/>
      <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor"
            stroke-width="1.25" opacity="0.45"/>
      <circle cx="7" cy="18.5" r="2.1" fill="none" stroke="currentColor" stroke-width="1.75"/>
      <circle cx="17" cy="18.5" r="2.1" fill="none" stroke="currentColor" stroke-width="1.75"/>
      <line x1="9.1" y1="18.5" x2="14.9" y2="18.5" stroke="currentColor" stroke-width="1.25"/>`,

    // A bearing in plan: outer race, inner race, four visible rollers.
    bearing: `
      <circle cx="12" cy="12" r="9.2" fill="none" stroke="currentColor"
              stroke-width="1.75" opacity="0.45"/>
      <circle cx="12" cy="12" r="5.6" fill="none" stroke="currentColor" stroke-width="1.75"/>
      <circle cx="12" cy="12" r="2" fill="currentColor" opacity="0.75"/>
      <circle cx="12" cy="4.6" r="1.25" fill="currentColor"/>
      <circle cx="19.4" cy="12" r="1.25" fill="currentColor"/>
      <circle cx="12" cy="19.4" r="1.25" fill="currentColor"/>
      <circle cx="4.6" cy="12" r="1.25" fill="currentColor"/>`,

    // Rail in section: two rails, sleepers, centreline.
    track: `
      <line x1="2" y1="8.5" x2="22" y2="8.5" stroke="currentColor" stroke-width="1.75"/>
      <line x1="2" y1="15.5" x2="22" y2="15.5" stroke="currentColor" stroke-width="1.75"/>
      <line x1="6" y1="5.5" x2="6" y2="18.5" stroke="currentColor" stroke-width="1.4" opacity="0.55"/>
      <line x1="12" y1="5.5" x2="12" y2="18.5" stroke="currentColor" stroke-width="1.4" opacity="0.55"/>
      <line x1="18" y1="5.5" x2="18" y2="18.5" stroke="currentColor" stroke-width="1.4" opacity="0.55"/>`,

    // Thermometer with a graduated scale.
    thermometer: `
      <path d="M9.4 4a2.6 2.6 0 0 1 5.2 0v9.3a4.6 4.6 0 1 1-5.2 0z"
            fill="none" stroke="currentColor" stroke-width="1.75"/>
      <line x1="12" y1="7" x2="12" y2="14" stroke="currentColor" stroke-width="1.75"/>
      <circle cx="12" cy="17.6" r="2.6" fill="currentColor" opacity="0.8"/>`,

    // Signal strength: a rising series with an endpoint dot.
    signal: `
      <polyline points="2.5,17 8,11.5 12.5,14.5 21,4.5" fill="none"
                stroke="currentColor" stroke-width="1.75" stroke-linejoin="round"
                stroke-linecap="round"/>
      <circle cx="21" cy="4.5" r="1.9" fill="currentColor"/>`,

    // A warrant: document corner with a ruled body.
    warrant: `
      <path d="M5 2.5h9l5 5v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-18a1 1 0 0 1 1-1z"
            fill="none" stroke="currentColor" stroke-width="1.75" stroke-linejoin="round"/>
      <polyline points="14,2.5 14,7.5 19,7.5" fill="none" stroke="currentColor" stroke-width="1.75"/>
      <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="1.5"/>
      <line x1="8" y1="15.5" x2="16" y2="15.5" stroke="currentColor" stroke-width="1.5"/>
      <line x1="8" y1="19" x2="12.5" y2="19" stroke="currentColor" stroke-width="1.5"/>`,

    // Chain link: the ledger's tamper-evident property.
    chain: `
      <path d="M10 14.5a4.4 4.4 0 0 0 6.2 0l2.6-2.6a4.4 4.4 0 0 0-6.2-6.2l-1.3 1.3"
            fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"/>
      <path d="M14 9.5a4.4 4.4 0 0 0-6.2 0l-2.6 2.6a4.4 4.4 0 0 0 6.2 6.2l1.3-1.3"
            fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"/>`,

    // A shield: certification / custody.
    shield: `
      <path d="M12 2.5l8 3v6.4c0 4.6-3.2 8.3-8 9.6-4.8-1.3-8-5-8-9.6V5.5z"
            fill="none" stroke="currentColor" stroke-width="1.75" stroke-linejoin="round"/>
      <polyline points="8.4,12 11.2,14.8 15.8,9.4" fill="none" stroke="currentColor"
                stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>`,

    // A clock: MTTD.
    clock: `
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.75"/>
      <polyline points="12,6.5 12,12.4 16,14.6" fill="none" stroke="currentColor"
                stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>`,

    // A currency mark in a frame: ROI.
    currency: `
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.75"/>
      <line x1="12" y1="6.2" x2="12" y2="17.8" stroke="currentColor" stroke-width="1.75"
            stroke-linecap="round"/>
      <path d="M15 9.1c0-1.2-1.3-2-3-2s-3 .8-3 2 1.3 1.8 3 2.3 3 1.1 3 2.3-1.3 2-3 2-3-.8-3-2"
            fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>`,

    // A gauge needle: mission readiness.
    gauge: `
      <path d="M3.6 17.5a9 9 0 1 1 16.8 0" fill="none" stroke="currentColor"
            stroke-width="1.75" stroke-linecap="round"/>
      <line x1="12" y1="15.2" x2="16.4" y2="9.6" stroke="currentColor"
            stroke-width="1.9" stroke-linecap="round"/>
      <circle cx="12" cy="15.2" r="1.6" fill="currentColor"/>`,

    // A warning triangle, used for the single-signal flag.
    alert: `
      <path d="M12 3.4l9.2 16.2H2.8z" fill="none" stroke="currentColor"
            stroke-width="1.75" stroke-linejoin="round"/>
      <line x1="12" y1="9.4" x2="12" y2="14.4" stroke="currentColor" stroke-width="1.9"
            stroke-linecap="round"/>
      <circle cx="12" cy="17.2" r="1.05" fill="currentColor"/>`,

    // A check, used for the corroborated flag.
    check: `
      <polyline points="4,12.6 9.8,18.4 20,6.4" fill="none" stroke="currentColor"
                stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>`,
  };

  let spriteReady = false;

  function installSprite() {
    if (spriteReady || typeof document === "undefined") return;
    if (document.getElementById("axiom-sprite")) { spriteReady = true; return; }

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("id", "axiom-sprite");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    // Zero-size but not display:none -- display:none prevents <use> resolving
    // in some engines, and a 0x0 box with overflow hidden is the safe form.
    svg.setAttribute("style", "position:absolute;width:0;height:0;overflow:hidden");

    for (const [name, inner] of Object.entries(SYMBOLS)) {
      const sym = document.createElementNS("http://www.w3.org/2000/svg", "symbol");
      sym.setAttribute("id", "i-" + name);
      sym.setAttribute("viewBox", "0 0 24 24");
      sym.innerHTML = inner;
      svg.appendChild(sym);
    }
    document.body.insertBefore(svg, document.body.firstChild);
    spriteReady = true;
  }

  /**
   * Build an <svg><use href="#i-name"></svg> element.
   * @param {string} name    a key of SYMBOLS
   * @param {object} [opts]  { size, state, title, className }
   *   state  -- applies one of STATE_COLOR as the currentColor source
   *   title  -- when given, the icon is exposed as an image with that label;
   *             when absent it is aria-hidden, because a decorative glyph
   *             should not double-announce the text beside it.
   */
  function icon(name, opts) {
    installSprite();
    const o = opts || {};
    if (!SYMBOLS[name]) {
      throw new Error("icon: unknown symbol " + JSON.stringify(name));
    }
    const NS = "http://www.w3.org/2000/svg";
    const size = o.size || 18;

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("width", String(size));
    svg.setAttribute("height", String(size));
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("class", "icon" + (o.className ? " " + o.className : ""));
    svg.style.color = o.state ? (STATE_COLOR[o.state] || "currentColor") : "currentColor";

    if (o.title) {
      svg.setAttribute("role", "img");
      const t = document.createElementNS(NS, "title");
      t.textContent = o.title;
      svg.appendChild(t);
    } else {
      svg.setAttribute("aria-hidden", "true");
      svg.setAttribute("focusable", "false");
    }

    const use = document.createElementNS(NS, "use");
    use.setAttribute("href", "#i-" + name);
    // xlink:href for older engines that predate the plain href on <use>.
    use.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", "#i-" + name);
    svg.appendChild(use);
    return svg;
  }

  global.AxiomIcons = { icon, SYMBOLS, STATE_COLOR, installSprite };
})(window);
