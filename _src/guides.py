"""Write the guides' pages (_src/pages/user-guide.html, developer-guide.html) from
AURA's Markdown guides, each with a table of contents beside the text.

    python _src/guides.py [path-to-AURA]        (default: C:\\dev_aura)
"""
import html
import os
import re
import shutil
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
AURA = sys.argv[1] if len(sys.argv) > 1 else r"C:\dev_aura"
GUIDES = (
    ("AURA_User_Guide_v1.0.md", "user-guide", "User Guide",
     "The AURA User Guide: the interface, the command language, data, statistics and estimation, survey data, graphics, scripts and packages."),
    ("AURA_Developer_Guide_v1.0.md", "developer-guide", "Developer Guide",
     "The AURA Developer Guide: write your own commands as Python modules, with their results, tables, help pages, dialog boxes and packages."),
)


def strip_toc(text):
    """The guide's own Table of Contents section: the column beside the text replaces it."""
    m = re.search(r"^## Table of Contents\s*$", text, re.MULTILINE)
    if not m:
        return text
    nxt = re.search(r"^(## |---\s*$)", text[m.end():], re.MULTILINE)
    end = m.end() + nxt.start() if nxt else len(text)
    return text[:m.start()] + text[end:]


def toc_html(tokens, depth=2):
    out = []
    for t in tokens:
        if t["level"] in (2, 3):
            out.append(f'<a class="l{t["level"]}" href="#{t["id"]}">{html.escape(html.unescape(t["name"]))}</a>')
        out.extend(toc_html(t.get("children", []), depth).splitlines())
    return "\n".join(out)


def main():
    images = os.path.join(AURA, "docs", "images")
    os.makedirs(os.path.join(SITE, "docs", "images"), exist_ok=True)
    for f in os.listdir(images):
        if f.endswith(".png"):
            shutil.copy2(os.path.join(images, f), os.path.join(SITE, "docs", "images", f))
    for src, slug, title, desc in GUIDES:
        text = open(os.path.join(AURA, "docs", src), encoding="utf-8").read()
        text = strip_toc(text)
        md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                               extension_configs={"toc": {"toc_depth": "2-3"}})
        body = md.convert(text)
        # links to AURA's source files (not on the site): the name stays, as code
        body = re.sub(r'<a href="\.\./[^"]+">(.*?)</a>', r"<code>\1</code>", body)
        toc = toc_html(md.toc_tokens)
        page = (f"<!-- title: {title} — AURA | description: {desc} | nav: learn | out: docs/{slug}.html -->\n\n"
                f'<div class="wrap docs">\n<nav class="toc" aria-label="Contents">\n{toc}\n</nav>\n'
                f'<article class="doc">\n{body}\n</article>\n</div>\n')
        # the guides' text braces must not be read as the site's {{placeholders}}
        page = page.replace("{{", "&#123;&#123;").replace("}}", "&#125;&#125;")
        with open(os.path.join(HERE, "pages", slug + ".html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
        print(f"{slug}.html: {len(body) // 1024} KB, {toc.count('<a ')} entries")


if __name__ == "__main__":
    main()
