"""Write _src/pages/commands.html — the command reference — from AURA's help pages.

    python _src/commands.py [path-to-AURA]        (default: C:\\dev_aura)

Each auru/<name>.aurh starts with "# name — what it does": the line gives the
command and its description. The category of each command is kept in
_src/command_categories.json; a help page not listed there stops the script,
so that a new command is given its place on purpose.
"""
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AURA = sys.argv[1] if len(sys.argv) > 1 else r"C:\dev_aura"
ORDER = ["Data & variables", "Explore & summarize", "Estimation & tests", "Survey", "Graphics",
         "Programming & results", "System & help", "Distributive analysis (DAAP)",
         "Price reforms (SUBSIM)", "Demand systems (DESYCO)"]


def pages():
    out = {}
    for path in glob.glob(os.path.join(AURA, "auru", "*.aurh")):
        name = os.path.splitext(os.path.basename(path))[0]
        first = open(path, encoding="utf-8").read().lstrip().split("\n", 1)[0]
        m = re.match(r"#\s*\S+\s+[—–-]+\s+(.*)", first)
        desc = (m.group(1) if m else first.lstrip("# ")).strip()
        out[name] = desc[:1].upper() + desc[1:]
    return out


def main():
    cats = json.load(open(os.path.join(HERE, "command_categories.json"), encoding="utf-8"))
    found = pages()
    unplaced = sorted(set(found) - set(cats))
    if unplaced:
        raise SystemExit("give these commands a category in command_categories.json: "
                         + ", ".join(unplaced))
    rows = sorted(found.items(), key=lambda kv: (ORDER.index(cats[kv[0]]), kv[0]))
    counts = {c: sum(1 for n in found if cats[n] == c) for c in ORDER}
    buttons = [f'<button class="fbtn on" data-f="all">All <b>{len(found)}</b></button>']
    buttons += [f'<button class="fbtn" data-f="{html.escape(c)}">{html.escape(c)} <b>{counts[c]}</b></button>'
                for c in ORDER if counts[c]]
    trs = []
    for name, desc in rows:
        c = html.escape(cats[name])
        trs.append(f'<tr data-cat="{c}" data-name="{html.escape(name)}" data-desc="{html.escape(desc.lower())}">'
                   f'<td class="cmd">{html.escape(name)}</td><td class="cat"><span class="pill">{c}</span></td>'
                   f'<td>{html.escape(desc)}</td></tr>')
    page = f"""<!-- title: Command reference — AURA | description: Every AURA command and what it does, from the in-app help: data, estimation, survey, graphics, programming, DAAP and SUBSIM. | nav: learn | out: commands.html -->

<section class="page-head">
  <div class="wrap">
    <p class="eyebrow">Reference</p>
    <h1>Command reference</h1>
    <p>Every command of AURA and of its packages, and what it does, taken from the help pages of AURA {{{{version}}}}. In AURA, type <span class="k">help</span> followed by a command for its syntax, options and examples.</p>
  </div>
</section>

<div class="wrap">
  <div class="controls">
    <input id="q" class="search" type="search" placeholder="Search the commands and what they do (regress, poverty, merge…)" aria-label="Search the commands">
    <div class="filters" id="filters">{''.join(buttons)}</div>
  </div>
  <p class="count" id="count"></p>
  <table class="cmds">
    <thead><tr><th>Command</th><th class="cat">Category</th><th>What it does</th></tr></thead>
    <tbody id="tb">
{chr(10).join(trs)}
    </tbody>
  </table>
  <p id="empty" style="display:none;color:var(--muted)">No command matches.</p>
  <div style="height:64px"></div>
</div>

<!-- SCRIPTS -->
<script>
  var q = document.getElementById("q"), tb = document.getElementById("tb"),
      rows = [].slice.call(tb.querySelectorAll("tr")), countEl = document.getElementById("count"),
      emptyEl = document.getElementById("empty"), cat = "all";
  function apply() {{
    var s = (q.value || "").trim().toLowerCase(), n = 0;
    rows.forEach(function (r) {{
      var ok = (cat === "all" || r.getAttribute("data-cat") === cat) &&
               (!s || r.getAttribute("data-name").indexOf(s) >= 0 || r.getAttribute("data-desc").indexOf(s) >= 0);
      r.style.display = ok ? "" : "none";
      if (ok) n++;
    }});
    countEl.textContent = n + " command" + (n === 1 ? "" : "s");
    emptyEl.style.display = n ? "none" : "block";
  }}
  q.addEventListener("input", apply);
  document.getElementById("filters").addEventListener("click", function (e) {{
    var b = e.target.closest(".fbtn"); if (!b) return;
    cat = b.getAttribute("data-f");
    [].forEach.call(this.querySelectorAll(".fbtn"), function (x) {{ x.classList.toggle("on", x === b); }});
    apply();
  }});
  apply();
</script>
"""
    with open(os.path.join(HERE, "pages", "commands.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"commands.html: {len(found)} commands")


if __name__ == "__main__":
    main()
