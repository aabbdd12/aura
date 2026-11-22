"""Copy the package manuals (built in AURA by tools/build_technotes.py) into the site.

    python _src/manuals.py [path-to-AURA]        (default: C:\\dev_aura)

Each manual is a page of its own (its own styles); it loads MathJax from the CDN
(AURA keeps an offline copy for its viewer) and gets a thin bar back to the site.

In AURA the viewer shows the manual's table of contents beside it, so the manual
carries none; on the site, a column of contents is added at the left — the
chapters and their sections, the current one highlighted as the page scrolls —
which folds behind a "Contents" button on a narrow screen.
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
BAR = ('<div style="font:500 14px/1.4 Inter,Segoe UI,sans-serif;background:#0b3d6e;color:#fff;'
       'padding:.55rem 1rem"><a href="../../index.html" style="color:#fff;font-weight:700;'
       'text-decoration:none">AURA</a> &nbsp;·&nbsp; <a href="../../learn.html#manuals" '
       'style="color:#fff">Guides and manuals</a></div>')
WIDE = 1100                     # px: from this width the column of contents stays open

TOC_CSS = """<style>
#site-toc { position: fixed; top: 0; left: 0; bottom: 0; width: 300px; overflow-y: auto;
  background: #f6f8fb; border-right: 1px solid #dde3ea; padding: 1rem .8rem 2.5rem;
  font: 14px/1.4 Inter, "Segoe UI", sans-serif; box-sizing: border-box; z-index: 50; }
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
@media (min-width: %dpx) { body { margin-left: 340px !important; } }
@media (max-width: %dpx) {
  #site-toc { width: min(300px, 86vw); transform: translateX(-100%%); transition: transform .2s;
    box-shadow: 0 0 24px rgba(0, 0, 0, .18); }
  #site-toc.open { transform: none; }
  #toc-toggle { display: block; position: fixed; right: 14px; bottom: 14px; z-index: 60;
    background: #0b57e8; color: #fff; border: 0; border-radius: 20px; padding: .55rem 1.05rem;
    font: 600 14px Inter, "Segoe UI", sans-serif; box-shadow: 0 2px 8px rgba(0, 0, 0, .25);
    cursor: pointer; }
}
@media print { #site-toc, #toc-toggle { display: none; } body { margin-left: auto !important; } }
</style>
""" % (WIDE, WIDE - 1)

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
            f'<a href="#">{name}</a></p><ul>' + "".join(items) + "</ul></nav>"
            '<button id="toc-toggle" type="button" aria-controls="site-toc" '
            'aria-expanded="false">Contents</button>'), len(items)


def main():
    for src, out, figures in MANUALS:
        text = open(os.path.join(AURA, *src.split("/")), encoding="utf-8").read()
        text, n = re.subn(r'<script([^>]*)\ssrc="[^"]*tex-svg-full\.js"', rf'<script\1 src="{MATHJAX}"', text)
        if n != 1:
            raise SystemExit(f"{src}: MathJax script not found once ({n})")
        nav, count = contents(text)
        if not count:
            raise SystemExit(f"{src}: no chapter or section found for the contents")
        text = text.replace("</head>", TOC_CSS + "</head>", 1)
        text = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + BAR + nav, text, count=1)
        text = text.replace("</body>", TOC_JS + "</body>", 1)
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
