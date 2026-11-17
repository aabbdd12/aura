"""Copy the package manuals (built in AURA by tools/build_technotes.py) into the site.

    python _src/manuals.py [path-to-AURA]        (default: C:\\dev_aura)

Each manual is a page of its own (its own styles); it loads MathJax from the CDN
(AURA keeps an offline copy for its viewer) and gets a thin bar back to the site.
"""
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
)
BAR = ('<div style="font:500 14px/1.4 Inter,Segoe UI,sans-serif;background:#0b3d6e;color:#fff;'
       'padding:.55rem 1rem"><a href="../../index.html" style="color:#fff;font-weight:700;'
       'text-decoration:none">AURA</a> &nbsp;·&nbsp; <a href="../../learn.html#manuals" '
       'style="color:#fff">Guides and manuals</a></div>')


def main():
    for src, out, figures in MANUALS:
        text = open(os.path.join(AURA, *src.split("/")), encoding="utf-8").read()
        text, n = re.subn(r'<script([^>]*)\ssrc="[^"]*tex-svg-full\.js"', rf'<script\1 src="{MATHJAX}"', text)
        if n != 1:
            raise SystemExit(f"{src}: MathJax script not found once ({n})")
        text = re.sub(r"(<body[^>]*>)", r"\1" + BAR, text, count=1)
        dest = os.path.join(SITE, *out.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if figures:
            fdest = os.path.join(os.path.dirname(dest), "figures")
            shutil.rmtree(fdest, ignore_errors=True)
            shutil.copytree(os.path.join(AURA, *figures.split("/")), fdest,
                            ignore=shutil.ignore_patterns("outputs"))
        print("wrote", out)


if __name__ == "__main__":
    main()
