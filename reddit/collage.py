"""Reddit collage for Britain's Last Line of Defence (stop-lines). Run from reddit/: python3 collage.py
Reads ../data/*.csv, ../data/*.geojson and ../data/results.json; Natural Earth land for the coast.
Fonts: Fraunces, Source Serif 4, IBM Plex Mono in FONT_DIR."""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
FG = "#1E241C"; MUT = "#5F6652"; LAND = "#DCD5BC"; COAST = "#A99F7E"
HOT = "#B8341B"; PILL = "#4F5A22"; OLIVE = "#4C7A3A"; SLATE = "#3D5A73"; KHAKI = "#8E7034"; PLUM = "#76507F"; TEAL = "#2C7A74"; GREY = "#6E6F68"; GONE = "#BDB59B"
FAMC = [PILL, SLATE, PLUM, KHAKI, TEAL, GREY]

D = "../data"
R = json.load(open(f"{D}/results.json"))
S = pd.read_csv(f"{D}/dob_sites_derived.csv"); FAM = R["families"]; S["fi"] = S.family.map({f: i for i, f in enumerate(FAM)})
SLG = json.load(open(f"{D}/stop_lines.geojson"))["features"]; SEA = json.load(open(f"{D}/sealion_coast.geojson"))["features"]
KX = np.cos(np.radians(53.5))
BOX = (-6.0, 49.85, 1.95, 55.95)
LANDP = []
for f in json.load(open("/home/claude/hist/_data3/ne/geojson/ne_10m_land.geojson"))["features"]:
    g = f["geometry"]
    for pg in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(pg[0])
        if a[:, 0].max() < BOX[0] - 2 or a[:, 0].min() > BOX[2] + 2 or a[:, 1].max() < BOX[1] - 1 or a[:, 1].min() > BOX[3] + 1: continue
        LANDP.append(a)


def base(ax, box, lw=.6):
    for a in LANDP:
        ax.add_patch(Polygon(np.c_[a[:, 0] * KX, a[:, 1]], closed=True, fc=LAND, ec=COAST, lw=lw, zorder=1))
    ax.set_xlim(box[0] * KX, box[2] * KX); ax.set_ylim(box[1], box[3]); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(12, 15), dpi=200)
grad = fig.add_axes([0, 0, 1, 1], zorder=-5); grad.axis("off")
grad.imshow(np.linspace(0, 1, 256)[:, None], cmap=LinearSegmentedColormap.from_list("d", ["#F5F2E7", "#E9E4D0"]), aspect="auto", extent=[0, 1, 0, 1])
fig.text(0.04, 0.968, "Did Britain fortify the right beaches?", fontproperties=DISP, fontsize=40, color=FG, va="top")
fig.text(0.04, 0.918, f"In 1940 Britain built pillboxes, anti-tank blocks and stop lines against invasion. Fifty years on,\n"
         f"volunteers recorded {R['n_sites']:,} of them. Here they are, with the beaches the Germans planned to land on.",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.15)

# ---------- hero map
ax = fig.add_axes([0.0, 0.33, 0.62, 0.545]); base(ax, BOX)
for i in [5, 4, 3, 2, 1]:
    g = S[S.fi == i]; ax.scatter(g.lon * KX, g.lat, s=2.4, c=FAMC[i], lw=0, alpha=.7, zorder=3)
pb = S[S.fi == 0]
ax.scatter(pb.lon * KX, pb.lat, s=7, marker="h", c=PILL, edgecolors="none", alpha=.75, zorder=3)
segs = [[(c[0][0] * KX, c[0][1]), (c[1][0] * KX, c[1][1])] for f in SLG for c in f["geometry"]["coordinates"]]
ax.add_collection(LineCollection(segs, colors=HOT, linewidths=1.5, alpha=.95, zorder=4, capstyle="round"))
for f in SEA:
    c = np.array(f["geometry"]["coordinates"])
    ax.plot(c[:, 0] * KX, c[:, 1], color=HOT, lw=16, alpha=.28, solid_capstyle="round", zorder=5)
    ax.plot(c[:, 0] * KX, c[:, 1], color=HOT, lw=3.4, zorder=6)
ax.annotate("Sea Lion beaches, 30 August 1940 plan:\nFolkestone to Brighton", (0.55 * KX, 50.78), xytext=(-0.6 * KX, 50.2), fontsize=11.5, family=MONO, color=HOT, ha="center",
            arrowprops=dict(arrowstyle="-", color=HOT, lw=1))
ax.annotate("GHQ Line", (-1.2 * KX, 51.37), xytext=(-2.4 * KX, 52.2), fontsize=11.5, family=MONO, color=FG, ha="center", zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="#F3EFE3", ec="none", alpha=.9), arrowprops=dict(arrowstyle="-", color=FG, lw=.8))
ax.annotate("Taunton\nStop Line", (-3.05 * KX, 50.95), xytext=(-4.75 * KX, 51.3), fontsize=11.5, family=MONO, color=FG, ha="center", zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="#F3EFE3", ec="none", alpha=.9), arrowprops=dict(arrowstyle="-", color=FG, lw=.8))
ax.annotate("London's\nrings", (-0.15 * KX, 51.75), xytext=(0.15 * KX, 52.5), fontsize=11.5, family=MONO, color=FG, ha="center", zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="#F3EFE3", ec="none", alpha=.9), arrowprops=dict(arrowstyle="-", color=FG, lw=.8))
t1 = R["coast_seg_top"][0]
ax.annotate("Redcar: the densest\nrecorded coast", (t1["lon"] * KX, t1["lat"]), xytext=(0.5 * KX, 55.35), fontsize=11.5, family=MONO, color=FG, ha="center", zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="#F3EFE3", ec="none", alpha=.9), arrowprops=dict(arrowstyle="-", color=FG, lw=.8))
hs = [plt.Line2D([], [], marker="h" if i == 0 else "o", ls="", ms=7, mfc=FAMC[i], mec="none", label=["Pillboxes", "Anti-tank obstacles", "Guns and batteries", "Trenches and posts", "Beach obstacles, mines", "Command and support"][i]) for i in range(6)]
hs.append(plt.Line2D([], [], color=HOT, lw=2, label="Stop lines"))
ax.legend(handles=hs, loc="lower left", bbox_to_anchor=(0.0, 0.585), frameon=True, facecolor="#F3EFE3", edgecolor="none", framealpha=.92, prop={"family": MONO, "size": 10.5}, labelcolor=FG, handletextpad=.3, borderaxespad=0)

# ---------- headline numbers
X0 = 0.645
nums = [(f"{R['n_sites']:,}", f"wartime defence sites recorded by\nDefence of Britain volunteers,\n1995 to 2002. {R['n_pillbox']:,} are pillboxes."),
        (f"{R['sealion']['all']['10']['ratio']:.1f}×", f"the density of recorded defence along\nthe planned landing beaches, compared\nwith the rest of the south and east coast."),
        (f"{R['share_standing_known'] * 100:.0f}%", f"still standing when recorded (of sites\nwith a known condition). Pillboxes {R['fam_status'][0]['share_standing_known'] * 100:.0f}%;\nbeach obstacles and mines {R['fam_status'][4]['share_standing_known'] * 100:.0f}%."),
        (f"{R['n_stop_line_groups']}", f"named stop lines, holding {R['share_on_stop_lines'] * 100:.0f}% of\nall sites. The GHQ Line alone has\n{R['ghq_sites']:,} recorded sites.")]
y = 0.855
for big, small in nums:
    fig.text(X0, y, big, fontproperties=DISP, fontsize=46, color=HOT, va="top")
    fig.text(X0, y - 0.052, small, family=SER, fontsize=14, color=FG, va="top", linespacing=1.25)
    y -= 0.135

# ---------- small multiples
ax2 = fig.add_axes([0.06, 0.135, 0.52, 0.14]); ax2.set_facecolor("none")
C = pd.DataFrame(R["coast_segments"])
col = [HOT if r.landing else ("#E0A596" if r.landing_share > .05 else SLATE) for r in C.itertuples()]
ax2.bar(C.start_km + C.km / 2, C.per_km, width=C.km * .85, color=col)
avg = R["sealion"]["all"]["10"]["per_km_rest"]; ax2.axhline(avg, color=FG, ls=(0, (3, 3)), lw=1)
for s in ["top", "right"]: ax2.spines[s].set_visible(False)
ax2.spines["left"].set_color(MUT); ax2.spines["bottom"].set_color(MUT)
def near(la, lo):
    d = (C.lat - la) ** 2 + ((C.lon - lo) * .62) ** 2; r = C.loc[d.idxmin()]; return r.start_km + r.km / 2
ticks = [(0, "Land's End"), (near(51.12, 1.32), "Dover"), (near(52.95, 1.1), "Norfolk"), (C.start_km.iloc[-1] + C.km.iloc[-1], "Berwick")]
ax2.set_xticks([t[0] for t in ticks], [t[1] for t in ticks], family=MONO, fontsize=11); ax2.tick_params(axis="y", labelsize=11, colors=FG); ax2.tick_params(axis="x", colors=FG)
for lab in ax2.get_yticklabels(): lab.set_family(MONO)
ax2.set_xlim(-10, ticks[-1][0] + 10)
fig.text(0.04, 0.322, "ALONG THE COAST", family=MONO, fontsize=12.5, color=FG, va="top")
fig.text(0.04, 0.304, "recorded sites per km, Land's End to Berwick; red = Sea Lion beaches", family=MONO, fontsize=11, color=MUT, va="top")
t2 = R["coast_seg_top"][1]
ax2.text(t2["start_km"] + 40, t2["per_km"], "Folkestone\nto Dover", family=MONO, fontsize=10.5, color=FG, va="top")
ax2.text(t1["start_km"] - 30, t1["per_km"], "Redcar", family=MONO, fontsize=10.5, color=FG, va="top", ha="right")

ax3 = fig.add_axes([0.70, 0.135, 0.26, 0.14]); ax3.set_facecolor("none")
fs = R["fam_status"]; lab = ["Pillboxes", "Anti-tank", "Guns", "Trenches, posts", "Beach, mines", "Command"]
yy = np.arange(len(fs))[::-1]
ax3.barh(yy, [f["share_standing_known"] * 100 for f in fs], color=[FAMC[i] for i in range(6)], height=.62)
for i, f in enumerate(fs): ax3.text(f["share_standing_known"] * 100 + 2, yy[i], f"{f['share_standing_known'] * 100:.0f}%", va="center", family=MONO, fontsize=11, color=FG)
ax3.set_yticks(yy, lab, family=MONO, fontsize=11); ax3.set_xlim(0, 112); ax3.set_xticks([])
for s in ["top", "right", "bottom"]: ax3.spines[s].set_visible(False)
ax3.spines["left"].set_color(MUT); ax3.tick_params(axis="y", length=0, colors=FG)
fig.text(0.60, 0.322, "WHAT SURVIVED", family=MONO, fontsize=12.5, color=FG, va="top")
fig.text(0.60, 0.304, "standing, of sites with a known condition", family=MONO, fontsize=11, color=MUT, va="top")

fig.text(0.04, 0.088, "Data: Defence of Britain Archive, Council for British Archaeology (2002, updated 2006), Archaeology Data\n"
         "Service, doi.org/10.5284/1000327 (non-commercial reuse with acknowledgement); Sea Lion beaches as summarised\n"
         "in Wikipedia, 'Operation Sea Lion'; towns placed with OS Open Names (OGL v3); Natural Earth coastline. This maps\n"
         "what volunteers recorded, mostly 1994 to 2002, not all that was built; recording effort varied by county.\n"
         "Stop lines are drawn through recorded sites. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=10, color=MUT, va="top", linespacing=1.4)
fig.savefig("britains_last_line.png", dpi=200, facecolor="#F0ECDD")
print("written")
