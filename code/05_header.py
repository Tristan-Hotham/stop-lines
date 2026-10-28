"""Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder of TTFs as FONT_DIR (FrauncesVar.ttf, SourceSerif4-Regular.ttf,
IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf from github.com/google/fonts);
otherwise the system serif is used.
Run: python3 05_header.py
"""
import os, json, math
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
S = json.load(open(os.path.join(ROOT, "work", "site.json")))
R = S["R"]; FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
K = math.cos(math.radians(53.5)); box = (-5.9, 49.9, 1.9, 55.9)
H = 610; W = H * (box[2] - box[0]) * K / (box[3] - box[1])
P = lambda la, lo: ((lo - box[0]) * K / ((box[3] - box[1])) * H, (box[3] - la) / (box[3] - box[1]) * H)
ins = lambda la, lo: box[1] <= la <= box[3] and box[0] <= lo <= box[2]
dots = "".join('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (*P(r[0], r[1]), 1.5 if r[2] == 0 else 1.1) for r in S["s"] if ins(r[0], r[1]))
lines = " ".join("M%.1f %.1fL%.1f %.1f" % (*P(s[0][1], s[0][0]), *P(s[1][1], s[1][0])) for g in S["slg"] for s in g if ins(s[0][1], s[0][0]))
sea = " ".join("M" + "L".join("%.1f %.1f" % P(c[1], c[0]) for c in f["geometry"]["coordinates"]) for f in S["sea"]["features"])
ff = ""
if FD and os.path.isdir(FD):
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:linear-gradient(160deg,#F4F1E6 0%,#E6E1CD 100%);color:#1E241C;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:84px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#69705E;display:flex;gap:12px;align-items:center}}
.k b{{background:#B8341B;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:66px;top:128px;margin:0;font:900 112px/.9 Fraunces,Georgia,serif;letter-spacing:-.02em}}
h1 em{{font-style:normal;color:#B8341B;display:block}}
p{{position:absolute;left:70px;top:386px;width:560px;margin:0;font-size:26px;line-height:1.36;color:#2B3226}}
.f{{position:absolute;left:70px;bottom:44px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#7C8370}}
svg{{position:absolute;right:40px;top:10px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Britain, 1940</span></div>
<h1>The last<em>line</em></h1>
<p>{R['n_sites']:,} recorded wartime defences and {R['n_stop_line_groups']} stop lines. Where they stood, what survived, and the planned invasion beaches.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{W:.0f}" height="{H}" viewBox="0 0 {W:.0f} {H}">
<g fill="#4F5A22" fill-opacity=".55">{dots}</g>
<path d="{lines}" stroke="#B8341B" stroke-width="1.6" fill="none" stroke-linecap="round"/>
<path d="{sea}" stroke="#B8341B" stroke-width="12" stroke-opacity=".3" fill="none" stroke-linecap="round"/>
<path d="{sea}" stroke="#B8341B" stroke-width="3" fill="none"/>
</svg>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
print("header.png written")
