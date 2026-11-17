"""Build the AURA site: each _src/pages/*.html body goes into _src/layout.html.

    python _src/build.py

A page starts with a comment of its settings:

    <!-- title: Features — AURA | description: ... | nav: features | out: features.html -->

`out` (default: the page's own name) may be in a folder (`docs/user-guide.html`);
the links of the layout then climb back to the site's root. A page may end with
`<!-- SCRIPTS -->` followed by the scripts it needs. The version, the installer
and the announcement are set once, below; pages may use {{version}}, {{size}},
{{installer}}, {{installer_url}}.

GitHub Pages does not publish folders whose name starts with "_": this folder
stays out of the site.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

CONFIG = {
    "version": "1.6",
    "size": "248 MB",
    "announce": "price and subsidy reforms with SUBSIM, a graph editor that works with the mouse, "
                "merged graphs, print previews.",
}
CONFIG["installer"] = f"AURA-{CONFIG['version']}-Setup.exe"
CONFIG["installer_url"] = ("https://github.com/aabbdd12/aura/releases/latest/download/"
                           + CONFIG["installer"])
NAVS = ("features", "packages", "learn", "download", "about")


def settings(text):
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.DOTALL)
    if not m:
        raise SystemExit("a page must start with its settings comment")
    out = {}
    for part in m.group(1).split("|"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out, text[m.end():]


def fill(text, values):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), text)


def build():
    layout = open(os.path.join(HERE, "layout.html"), encoding="utf-8").read()
    pages = sorted(f for f in os.listdir(os.path.join(HERE, "pages")) if f.endswith(".html"))
    for name in pages:
        raw = open(os.path.join(HERE, "pages", name), encoding="utf-8").read()
        meta, body = settings(raw)
        out = meta.get("out", name)
        depth = out.count("/")
        scripts = ""
        if "<!-- SCRIPTS -->" in body:
            body, scripts = body.split("<!-- SCRIPTS -->", 1)
        values = dict(CONFIG)
        values.update({
            "title": meta.get("title", "AURA"),
            "description": meta.get("description", ""),
            "root": "../" * depth,
            "head": meta.get("head", ""),
        })
        page = layout
        for nav in NAVS:
            page = page.replace("{{on:%s}}" % nav, " on" if meta.get("nav") == nav else "")
        page = page.replace("{{body}}", fill(body.strip(), values))
        page = page.replace("{{scripts}}", scripts.strip())
        page = fill(page, values)
        path = os.path.join(SITE, *out.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
        print("wrote", out)


if __name__ == "__main__":
    build()
