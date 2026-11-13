#!/usr/bin/env python3
"""Structural and accessibility checks on the AxiomDynamics frontend.

There is no browser in this environment, so this suite cannot assert that the
dashboard *looks* right -- that was verified by reading a rendered screenshot.
What it does assert is that the things a screenshot cannot prove are true: that
the icon sprite is well-formed XML, that every icon the app asks for exists,
that the two copies of the state-colour table still agree, that no state is
encoded by colour alone, and that the contrast tokens on record are the ones
actually measured.

Every check reads the file from disk. Nothing is asserted from memory of what
was written.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(ROOT, "frontend", "icons.js")
APP = os.path.join(ROOT, "frontend", "app.js")
CSS = os.path.join(ROOT, "frontend", "style.css")
HTML = os.path.join(ROOT, "frontend", "index.html")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def relative_luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    parts = []
    for i in (0, 2, 4):
        v = int(h[i:i + 2], 16) / 255
        parts.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a, b):
    la, lb = relative_luminance(a) + 0.05, relative_luminance(b) + 0.05
    return max(la, lb) / min(la, lb)


# --- Sprite integrity ------------------------------------------------------

def test_every_symbol_is_wellformed_xml():
    """A malformed symbol is an icon that silently renders nothing."""
    import xml.etree.ElementTree as ET
    src = read(ICONS)
    body = src[src.index("const SYMBOLS = {"):src.index("let spriteReady")]
    for name, inner in re.findall(r'(\w+):\s*`(.*?)`', body, re.S):
        try:
            ET.fromstring(
                '<svg xmlns="http://www.w3.org/2000/svg">' + inner + "</svg>"
            )
        except ET.ParseError as exc:
            raise AssertionError(f"symbol {name!r} is not well-formed XML: {exc}")
    assert re.search(r"\brailcar\s*:", body), "the sprite parsed to nothing"


def test_sprite_covers_every_icon_the_app_requests():
    src_app = read(APP)
    src_icons = read(ICONS)
    requested = set(re.findall(r'AxiomIcons\.icon\(\s*"(\w+)"', src_app))
    requested |= set(re.findall(r'head\.appendChild\(AxiomIcons\.icon\(\s*"(\w+)"', src_app))
    # kpiCard takes the icon name as a trailing string argument.
    requested |= set(re.findall(r'"(gauge|clock|currency|warrant)",\s*\n\s*\)\);', src_app))
    assert requested, "no icon call sites found -- the regexes have gone stale"
    defined = set(re.findall(r"^\s{4}(\w+):\s*`", src_icons, re.M))
    missing = requested - defined
    assert not missing, f"app requests undefined icons: {sorted(missing)}"


def test_every_symbol_is_referenced_somewhere():
    """An unused symbol is dead weight, but an icon() call with a typo is worse.
    This catches the reverse case: symbols nothing asks for."""
    src_app, src_icons = read(APP), read(ICONS)
    defined = set(re.findall(r"^\s{4}(\w+):\s*`", src_icons, re.M))
    used = set(re.findall(r'icon\("(\w+)"', src_app))
    used |= set(re.findall(r'"(gauge|clock|currency|warrant)",\s*\n\s*\)\);', src_app))
    # shield / chain / alert / check are reserved for panels not yet built.
    reserved = {"shield", "chain", "track", "thermometer", "signal", "alert", "check"}
    orphans = defined - used - reserved
    assert not orphans, f"symbols defined but never used: {sorted(orphans)}"


# --- The duplicated token table --------------------------------------------

def test_state_colours_match_the_stylesheet():
    """icons.js duplicates the palette because SVG cannot read a CSS variable.
    A duplicate that drifts is a colour bug nobody sees until a badge is wrong."""
    js = read(ICONS)
    state_block = js[js.index("const STATE_COLOR"):js.index("// --- The symbol set")]
    js_map = dict(re.findall(r'(\w+):\s*"(#\w+)"', state_block))
    css = read(CSS)
    css_map = {
        "normal": re.search(r"--ok:\s*(#\w+)", css).group(1),
        "watch": re.search(r"--warn:\s*(#\w+)", css).group(1),
        "warning": re.search(r"--warn:\s*(#\w+)", css).group(1),
        "critical": re.search(r"--bad:\s*(#\w+)", css).group(1),
        "review": re.search(r"--warn:\s*(#\w+)", css).group(1),
    }
    assert js_map == css_map, f"palette drift: icons.js={js_map} css={css_map}"


def test_tokens_are_measured_and_pass_aa():
    """The ratio written beside each token must be the ratio that token has.
    A comment that misstates its own number is worse than no comment."""
    css = read(CSS)
    body = css[css.index(":root {"):css.index("* { box-sizing")]
    documented = re.findall(r"--([\w-]+):\s*(#\w+);[^\n]*?(\d+\.\d+):1", body)
    assert len(documented) >= 6, f"only {len(documented)} documented tokens found"
    for name, colour, claimed in documented:
        actual = contrast(colour, "#ffffff")
        assert abs(actual - float(claimed)) < 0.05, (
            f"--{name} {colour} claims {claimed}:1 but measures {actual:.2f}:1"
        )
        assert actual >= 4.5, f"--{name} {colour} is {actual:.2f}:1, below AA for text"


def test_chart_palette_is_legible_on_the_canvas():
    """The chart code was written for a dark canvas and moved to a light one
    without its palette following: series lines measured 1.55-1.95:1, which is
    very nearly invisible. Assert every chart colour clears 3:1 (AA-large)."""
    js = read(APP)
    canvas_bg = re.search(r"font-size: 14px;\s*--surface-sunken:\s*(#\w+)", read(CSS))
    bg = canvas_bg.group(1) if canvas_bg else "#f4f6f9"
    colours = set(re.findall(r'(?:ctx\.strokeStyle|ctx\.fillStyle)\s*=\s*"(#\w+)"', js))
    colours |= set(re.findall(r'color:\s*"(#\w+)"', js))
    # The grid rule is a decorative hairline, not information; it is exempt and
    # is deliberately faint. Everything else must be readable.
    colours.discard("#e2e8f0")
    assert colours, "no chart colours found"
    for c in sorted(colours):
        r = contrast(c, bg)
        assert r >= 3.0, f"chart colour {c} is {r:.2f}:1 on {bg} -- below AA-large"


# --- Structure and accessibility -------------------------------------------

def test_scripts_loaded_in_dependency_order():
    html = read(HTML)
    i = html.index('src="icons.js"')
    a = html.index('src="app.js"')
    assert i < a, "app.js loads before icons.js, so AxiomIcons is undefined at call time"


def test_demo_band_is_the_first_element_in_body():
    """The demonstration notice must survive any screenshot of the page. If it
    slides below the fold, a cropped image shows numbers with no disclosure --
    which is the drift D00 Part VI exists to prevent."""
    html = read(HTML)
    body = html[html.index("<body>"):]
    first_element = re.search(r"<(\w+)[\s>]", body[body.index("<body>") + 6:])
    assert first_element.group(1) == "div", first_element.group(1)
    band_at = body.index('id="demo-band"')
    header_at = body.index("<header>")
    assert band_at < header_at, "the demo band is not above the header"
    assert "synthetic" in body[:band_at].lower() + body[band_at:header_at].lower()


def test_no_state_is_encoded_by_colour_alone():
    """WCAG 1.4.1. Every severity badge must carry a glyph, not just a colour.

    The first version of this test asserted that a `.badge.critical::before`
    RULE EXISTED. Deleting the glyph content left the selector behind and the
    test still passed -- a check on the shape of a declaration rather than on
    whether a glyph is actually rendered. It now requires a `content` with a
    real character in every severity group, and asserts the four groups get
    four DISTINCT glyphs, so a copy-paste that gives every tier the same dot
    is caught too."""
    css = read(CSS)

    def glyph(selectors):
        # Find the rule whose selector list contains one of these, and read the
        # content character out of its declaration block.
        for m in re.finditer(r"([^{}]*)\{([^}]*)\}", css):
            sel, decl = m.group(1), m.group(2)
            if not any(s in sel for s in selectors):
                continue
            cm = re.search(r"content:\s*\"(.+?)\"", decl)
            if cm and cm.group(1).strip():
                return cm.group(1).strip()
        return None

    groups = {
        "ok": [".badge.normal::before", ".badge.informational::before"],
        "warn": [".badge.watch::before", ".badge.review::before",
                 ".badge.warning::before"],
        "bad": [".badge.critical::before", ".badge.urgentreview::before"],
    }
    seen = {}
    for tier, sels in groups.items():
        g = glyph(sels)
        assert g, f"no rendered glyph for the {tier} badge group"
        seen[tier] = g
    assert len(set(seen.values())) == 3, (
        f"badge groups share glyphs, so the shape carries no information: {seen}"
    )


def test_icon_is_decorative_unless_given_a_title():
    js = read(ICONS)
    assert 'svg.setAttribute("aria-hidden", "true")' in js
    assert 'if (o.title)' in js, "the titled-icon branch has gone"


def test_fleet_rows_are_keyboard_reachable():
    """Click-only rows are unusable without a mouse."""
    app = read(APP)
    assert 'tabindex: "0"' in app, "fleet rows lost their tab stop"
    assert 'role: "button"' in app, "fleet rows lost their button role"
    assert 'ev.key === "Enter"' in app, "fleet rows lost their Enter handler"


def test_spaces_on_a_row_do_not_scroll_the_page():
    """Space activates a button, so it must be consumed -- otherwise activating a
    row also scrolls the viewport, which reads as a bug."""
    app = read(APP)
    assert "ev.preventDefault()" in app


def test_reduced_motion_and_forced_colours_are_honoured():
    css = read(CSS)
    assert "prefers-reduced-motion" in css
    assert "forced-colors" in css


def main():
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except AssertionError as exc:
                failed += 1
                print(f"FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            else:
                passed += 1
                print(f"PASS  {name}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
