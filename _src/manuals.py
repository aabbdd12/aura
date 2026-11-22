"""Copy the package manuals (built in AURA by tools/build_technotes.py) into the site.

    python _src/manuals.py [path-to-AURA]        (default: C:\\dev_aura)

Each manual is a page of its own (its own styles); it loads MathJax from the CDN
(AURA keeps an offline copy for its viewer).  On the site it gets:

- the site's own announcement ribbon and header (the HTML of layout.html, the
  rules of assets/site.css, the site's colours kept to the header so that the
  manual keeps its own);
- a column of contents at the left — in AURA the viewer shows the manual's
  contents beside it, so the manual carries none —: the chapters and their
  sections, the current one highlighted as the page scrolls, held under the
  header; on a narrow screen it folds behind a "Contents" button.
"""
import html
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
AURA = sys.argv[1] if len(sys.argv) > 1 else r"C:\dev_aura"
MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg-full.js"
MANUALS = (
    ("daap/technotes/daap_manual.html", "manuals/daap/daap_manual.html", None),
    ("subsim/technotes/subsim_manual.html", "manuals/subsim/subsim_manual.html", "subsim/technotes/figures"),
    ("desyco/technotes/desyco_manual.html", "manuals/desyco/desyco_manual.html", "desyco/technotes/figures"),
)
WIDE = 1100                     # px: from this width the column of contents stays open
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family='
         'Manrope:wght@500;600;700&display=swap" rel="stylesheet">\n')

LAYOUT_CSS = """
body.site-manual { max-width: none !important; margin: 0 !important; padding: 0 !important; }
html { scroll-padding-top: 84px; }
.site-head { font-family: var(--font-sans); line-height: 1.6; }
header.site-head { font-size: 17px; color: var(--ink); }
.mlayout { display: flex; align-items: flex-start; }
.mbody { flex: 1; min-width: 0; max-width: 820px; margin: 2.2rem auto 4rem; padding: 0 1.4rem; }
#site-toc { position: sticky; top: 68px; height: calc(100vh - 68px); width: 300px; flex: none;
  overflow-y: auto; background: #f6f8fb; border-right: 1px solid #dde3ea;
  padding: 1rem .8rem 2.5rem; font: 14px/1.4 Inter, "Segoe UI", sans-serif; z-index: 15; }
#site-toc .toc-title { font-weight: 700; color: #0b3d6e; margin: .2rem .35rem .5rem; }
#site-toc .toc-title a { color: #0b3d6e; text-decoration: none; }
#site-toc ul { list-style: none; margin: 0; padding: 0; }
#site-toc li { margin: .08rem 0; }
#site-toc li.l1 { margin-top: .5rem; font-weight: 600; }
#site-toc li.l2 { padding-left: 1.05rem; font-size: 13.5px; }
#site-toc a { color: #33415c; text-decoration: none; display: block; padding: .14rem .35rem;
  border-radius: 4px; }
#site-toc a:hover { background: #e7edf5; }
#site-toc a.on { background: #dbe7f6; color: #0b3d6e; }
#site-toc .n { color: #7a869a; margin-right: .3rem; font-weight: 500; }
#toc-toggle { display: none; }
@media (max-width: %dpx) {
  #site-toc { position: fixed; top: 0; left: 0; bottom: 0; height: auto; width: min(300px, 86vw);
    z-index: 50; transform: translateX(-100%%); transition: transform .2s;
    box-shadow: 0 0 24px rgba(0, 0, 0, .18); }
  #site-toc.open { transform: none; }
  .mbody { padding: 0 1rem; margin-top: 1.4rem; }
  #toc-toggle { display: block; position: fixed; right: 14px; bottom: 14px; z-index: 60;
    background: #0b57e8; color: #fff; border: 0; border-radius: 20px; padding: .55rem 1.05rem;
    font: 600 14px Inter, "Segoe UI", sans-serif; box-shadow: 0 2px 8px rgba(0, 0, 0, .25);
    cursor: pointer; }
}
@media print { .site-head, #site-toc, #toc-toggle { display: none !important; } }
""" % (WIDE - 1)

TOC_JS = """<script>
(function () {
  var toc = document.getElementById("site-toc"), btn = document.getElementById("toc-toggle");
  function show(open) { toc.classList.toggle("open", open); btn.setAttribute("aria-expanded", open); }
  btn.addEventListener("click", function () { show(!toc.classList.contains("open")); });
  toc.addEventListener("click", function (e) {
    if (e.target.closest("a") && window.innerWidth < %d) show(false);
  });
  var links = {};
  toc.querySelectorAll("li a").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
  var heads = [].slice.call(document.querySelectorAll("h1[id], h2[id]"))
                .filter(function (h) { return links[h.id]; });
  var current = null;
  function spy() {
    var cur = null;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].getBoundingClientRect().top < 120) cur = heads[i]; else break;
    }
    if (cur === current) return;
    if (current) links[current.id].classList.remove("on");
    current = cur;
    if (!cur) return;
    var a = links[cur.id], r = a.getBoundingClientRect(), t = toc.getBoundingClientRect();
    a.classList.add("on");
    if (r.top < t.top + 40 || r.bottom > t.bottom - 20) a.scrollIntoView({block: "center"});
  }
  window.addEventListener("scroll", spy, {passive: true});
  spy();
})();
</script>
""" % WIDE

_HEAD = re.compile(r"<h([12])([^>]*)>(.*?)</h\1>", re.DOTALL)


def site_header():
    """(the CSS, the HTML of the announcement and the header, its script) of the
    site, from layout.html and assets/site.css, for a page two folders down."""
    sys.path.insert(0, HERE)
    from build import CONFIG, NAVS, fill
    layout = open(os.path.join(HERE, "layout.html"), encoding="utf-8").read()
    start = layout.index('<div class="announce" id="announce">')
    end = layout.index("</header>") + len("</header>")
    head = layout[start:end]
    head = head.replace('<div class="announce" id="announce">',
                        '<div class="announce site-head" id="announce">', 1)
    head = head.replace('<header class="top">', '<header class="top site-head">', 1)
    m = re.search(r"<script>\s*function hideAnnounce.*?</script>", layout, re.DOTALL)
    script = m.group(0)
    values = dict(CONFIG, root="../../")
    for nav in NAVS:
        head = head.replace("{{on:%s}}" % nav, " on" if nav == "learn" else "")
    head, script = fill(head, values), fill(script, values)

    css = open(os.path.join(SITE, "assets", "site.css"), encoding="utf-8").read()
    root = re.search(r":root \{.*?\n  \}\n", css, re.DOTALL).group(0)
    root = root.replace(":root {", ".site-head {", 1)          # the site's colours, kept here
    wrap = "\n".join(ln for ln in css.splitlines()          # .wrap and its wider padding
                     if re.match(r"\s*\.wrap \{[^}]*\}\s*$", ln)
                     or re.match(r"\s*@media \(min-width: 700px\) \{ \.wrap \{[^}]*\} \}\s*$", ln))
    if wrap.count("{") != 3 or wrap.count("}") != 3:
        raise SystemExit("site.css: the two .wrap rules not found")
    a = css.index("/* ── announcement ribbon")
    b = css.index("@media (max-width: 900px) {", a)
    depth, i = 0, css.index("{", b)
    while True:
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        if depth == 0:
            break
        i += 1
    rules = css[a:i + 1]
    on = re.search(r"nav\.main \.top-link\.on \{[^}]*\}", css).group(0)
    style = "<style>\n" + root + wrap + "\n" + rules + "\n" + on + "\n" + LAYOUT_CSS + "</style>\n"
    return style, head, script


def contents(text):
    """The column of contents: the chapters (h1) and sections (h2) with an id,
    their numbers as the manual writes them."""
    items = []
    for level, attrs, inner in _HEAD.findall(text):
        hid = re.search(r'\bid="([^"]+)"', attrs)
        if not hid or 'class="title"' in attrs:
            continue
        num = re.search(r'\bdata-number="([^"]+)"', attrs)
        label = re.sub(r'<span\s+class="header-section-number">.*?</span>', "", inner,
                       flags=re.DOTALL)
        label = re.sub(r"<[^>]+>", "", label)
        label = " ".join(html.unescape(label).split())
        number = f'<span class="n">{num.group(1)}</span>' if num else ""
        items.append(f'<li class="l{level}"><a href="#{hid.group(1)}">{number}'
                     f'{html.escape(label, quote=False)}</a></li>')
    title = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    name = title.group(1).split(":")[0].strip() if title else "Contents"
    return (f'<nav id="site-toc" aria-label="Contents"><p class="toc-title">'
            f'<a href="#">{name}</a></p><ul>' + "".join(items) + "</ul></nav>"), len(items)


def main():
    style, head, script = site_header()
    toggle = ('<button id="toc-toggle" type="button" aria-controls="site-toc" '
              'aria-expanded="false">Contents</button>')
    for src, out, figures in MANUALS:
        text = open(os.path.join(AURA, *src.split("/")), encoding="utf-8").read()
        text, n = re.subn(r'<script([^>]*)\ssrc="[^"]*tex-svg-full\.js"', rf'<script\1 src="{MATHJAX}"', text)
        if n != 1:
            raise SystemExit(f"{src}: MathJax script not found once ({n})")
        nav, count = contents(text)
        if not count:
            raise SystemExit(f"{src}: no chapter or section found for the contents")
        m = re.search(r"<body[^>]*>(.*)</body>", text, re.DOTALL)
        if not m:
            raise SystemExit(f"{src}: no body")
        body = ('<body class="site-manual">\n' + head + '\n<div class="mlayout">' + nav
                + '<div class="mbody">' + m.group(1) + "</div></div>\n" + toggle + "\n"
                + script + "\n" + TOC_JS + "</body>")
        text = text[:m.start()] + body + text[m.end():]
        text = text.replace("</head>", FONTS + style + "</head>", 1)
        dest = os.path.join(SITE, *out.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if figures:
            fdest = os.path.join(os.path.dirname(dest), "figures")
            shutil.rmtree(fdest, ignore_errors=True)
            shutil.copytree(os.path.join(AURA, *figures.split("/")), fdest,
                            ignore=shutil.ignore_patterns("outputs"))
        print("wrote", out, f"({count} entries in the contents)")


if __name__ == "__main__":
    main()
