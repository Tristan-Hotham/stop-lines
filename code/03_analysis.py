"""Step 3: the analysis. Families of defences, survival, stop lines as lines, the Sea Lion coast
test, the OpenStreetMap check, recording coverage and the wider wartime layers.

Inputs: ../data/dob_sites.csv, ../data/dob_groups.csv and the step 2 layers; Natural Earth 1:10m
land (public domain) for the coastline; OS Open Names (OGL v3) to place the towns named in the
Operation Sea Lion article.
Outputs: ../data/results.json (every number used anywhere), ../data/stop_lines.geojson,
../data/stop_lines.csv, ../data/sealion_coast.geojson, ../data/coast_segments.csv,
../data/dob_sites_derived.csv (sites with family, status, coastal distances, nearest OSM pillbox),
../work/site.json (compact data for the page).
Run: python3 03_analysis.py
"""
import csv, json, os, collections, math
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import minimum_spanning_tree
import shapely
from shapely.geometry import shape, Point, LineString, MultiLineString, mapping
from shapely.ops import substring, unary_union, transform as stransform

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); D = os.path.join(ROOT, "data")
fwd = Transformer.from_crs(4326, 27700, always_xy=True); inv = Transformer.from_crs(27700, 4326, always_xy=True)
R = {}

# ======================================================== families and status
S = pd.read_csv(os.path.join(D, "dob_sites.csv"), dtype={"groups": str, "group_ids": str, "county": str})
S["groups"] = S["groups"].fillna(""); S["group_ids"] = S["group_ids"].fillna(""); S["county"] = S["county"].fillna("")
FAM = ["Pillboxes", "Anti-tank obstacles", "Guns and batteries", "Trenches, posts and defended places",
       "Landing obstacles, mines and flame", "Command, observation and support"]


def family(t):
    t = t.upper()
    if t.startswith("PILLBOX") or "WILLIAMS TURRET" in t or "PICKETT HAMILTON" in t: return 0
    if any(k in t for k in ["ANTI SEAPLANE", "ANTI LANDING", "ANTI BOAT", "BEACH SCAFFOLDING", "MINEFIELD", "PIPE MINE", "MINED ", "FLAME", "FOUGASSE",
                            "PETROLEUM WARFARE", "DEPTH CHARGE", "DEMOLITION"]): return 4
    if t == "ANTI TANK ISLAND": return 3
    if "GUN EMPLACEMENT" in t and "MACHINE" not in t: return 2
    if any(k in t for k in ["ANTI TANK", "ROADBLOCK", "CUBE", "CYLINDER", "PIMPLE", "CONE", "COFFIN", "RAILBLOCK", "CALTROP", "DRAGON", "HAIRPIN", "TETRAHEDR"]): return 1
    if any(k in t for k in ["BATTERY", "GUN POST", "SEARCHLIGHT", "DEFENCE LIGHT", "MORTAR", "HOLDFAST", "GUN PIT", "ARTILLERY"]): return 2
    if any(k in t for k in ["TRENCH", "WEAPON PIT", "RIFLE PIT", "INFANTRY POST", "MACHINE GUN", "FORTIFIED", "LOOPHOLED", "DEFENDED", "KEEP", "CENTRE OF RESISTANCE",
                            "BARBED WIRE", "SECTION POST", "DEFENCE SITE", "DEFENCE WORK", "STRONGPOINT", "REDOUBT", "NODAL POINT", "VULNERABLE", "BREASTWORK", "SANGAR"]): return 3
    return 5


S["fam"] = S["type"].map(family)
STAT = {"Good": "Standing", "Fair": "Standing", "Bad": "Standing", "Very Bad": "Standing", "Extant but condition unknown": "Standing",
        "Removed": "Gone", "Infilled": "Gone", "Unknown": "Not known"}
S["status"] = S["condition"].map(STAT)
S = S[S.lat.notna()].copy()
S["x"], S["y"] = fwd.transform(S.lon.values, S.lat.values)
N = len(S); R["n_sites"] = N; R["n_records_all"] = int(json.load(open(os.path.join(ROOT, "work", "dob_meta.json")))["n_records"])
R["dob_meta"] = json.load(open(os.path.join(ROOT, "work", "dob_meta.json")))
R["n_ww2"] = int((S.period == "WW2").sum())
R["n_by_period"] = {k: int(v) for k, v in S.period.value_counts().items()}
R["families"] = FAM
R["fam_counts"] = [int((S.fam == i).sum()) for i in range(6)]
R["fam_share"] = [c / N for c in R["fam_counts"]]
tc = S.type.value_counts()
R["top_types"] = [{"type": k, "n": int(v), "fam": int(family(k))} for k, v in tc.head(20).items()]
R["n_types"] = int(len(tc))
pb = S[S.fam == 0]
R["pillbox_types"] = [{"type": k, "n": int(v)} for k, v in pb.type.value_counts().head(10).items()]
R["n_pillbox"] = int(len(pb)); R["n_pillbox_type22_24"] = int(pb.type.isin(["PILLBOX (TYPE FW3/22)", "PILLBOX (TYPE FW3/24)"]).sum())
R["n_pillbox_generic"] = int((pb.type == "PILLBOX").sum())

# survival
cond_order = ["Good", "Fair", "Bad", "Very Bad", "Extant but condition unknown", "Removed", "Infilled", "Unknown"]
R["condition"] = {c: int((S.condition == c).sum()) for c in cond_order}
for k in ["Standing", "Gone", "Not known"]: R["status_" + k.replace(" ", "_").lower()] = int((S.status == k).sum())
known = S[S.status != "Not known"]
R["share_standing_all"] = R["status_standing"] / N; R["share_standing_known"] = float((known.status == "Standing").mean())
R["share_gone_all"] = R["status_gone"] / N
R["fam_status"] = []
for i in range(6):
    g = S[S.fam == i]; k = g[g.status != "Not known"]
    R["fam_status"].append(dict(family=FAM[i], n=int(len(g)), standing=int((g.status == "Standing").sum()), gone=int((g.status == "Gone").sum()),
                                unknown=int((g.status == "Not known").sum()), share_standing_known=float((k.status == "Standing").mean()) if len(k) else None))
R["pillbox_standing"] = int((pb.status == "Standing").sum()); R["pillbox_gone"] = int((pb.status == "Gone").sum())
R["pillbox_good_fair"] = int(pb.condition.isin(["Good", "Fair"]).sum())
R["refs"] = {"built_total": 28000, "survive_total": 6500, "built_by_sept_1940": 18000,
             "built_note": "About 28,000 pillboxes and other hardened field fortifications were constructed in the United Kingdom of which about 6,500 still survive (Wikipedia, British anti-invasion preparations of the Second World War, citing the CBA review of the Defence of Britain Project)",
             "sept_note": "by the end of September 1940, 18,000 pillboxes and numerous other preparations had been completed (same article)"}

# dates of construction and of recording
by = S.built_year.dropna().astype(int)
R["n_built_year"] = int(len(by)); R["built_1940"] = int((by == 1940).sum()); R["share_built_1940"] = float((by == 1940).mean())
R["built_years"] = {str(k): int(v) for k, v in by.value_counts().sort_index().items() if 1935 <= k <= 1946}
lv = S.last_visit_year.dropna().astype(int)
R["n_visit_year"] = int(len(lv)); R["visit_median"] = int(np.median(lv)); R["visit_share_1994_2002"] = float(((lv >= 1994) & (lv <= 2002)).mean())
R["visit_years"] = {str(k): int(v) for k, v in lv.value_counts().sort_index().items()}

# recording coverage by county (the DoB's own county field)
cc = collections.Counter()
for c in S.county:
    for x in c.split(";"):
        if x: cc[x] += 1
R["county_top"] = [{"county": k, "n": v} for k, v in cc.most_common(20)]
R["n_counties"] = len(cc)
R["county_named"] = {k: cc.get(k, 0) for k in ["Kent", "Norfolk", "Redcar & Cleveland", "Devon", "Essex", "Worcestershire", "Lancashire", "Sussex, East", "Cornwall"]}

# ======================================================== groups and stop lines
G = pd.read_csv(os.path.join(D, "dob_groups.csv"))
R["n_groups"] = int(len(G)); R["groups_by_kind"] = {k: int(v) for k, v in G.kind.value_counts().items()}
mem = collections.defaultdict(list)
for idx, ids in zip(S.index, S.group_ids):
    for g in str(ids).split(";"):
        if g: mem[int(g)].append(idx)
R["n_in_any_group"] = int((S.group_ids != "").sum()); R["share_in_any_group"] = R["n_in_any_group"] / N
SLG = G[G.kind == "stop line"].copy()
CUT = 10000.0  # metres: longest gap drawn between neighbouring recorded sites
feats = []; slrows = []
for _, g in SLG.iterrows():
    ids = mem.get(int(g.group_id), [])
    sub = S.loc[ids]
    if len(sub) < 2: continue
    P = np.c_[sub.x.values, sub.y.values]
    Dm = np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1)); Dm[Dm == 0] = 0.01
    T = minimum_spanning_tree(Dm).tocoo()
    segs = [(i, j, d) for i, j, d in zip(T.row, T.col, T.data) if d <= CUT]
    length = sum(d for _, _, d in segs) / 1000
    span = float(Dm.max()) / 1000
    k = sub[sub.status != "Not known"]
    lines = [[[round(v, 5) for v in inv.transform(*P[i])], [round(v, 5) for v in inv.transform(*P[j])]] for i, j, _ in segs]
    row = dict(group_id=int(g.group_id), name=g["name"].strip(), n_sites=int(len(sub)), drawn_km=round(length, 1), span_km=round(span, 1),
               n_pillbox=int((sub.fam == 0).sum()), n_antitank=int((sub.fam == 1).sum()), standing=int((sub.status == "Standing").sum()),
               gone=int((sub.status == "Gone").sum()), share_standing_known=round(float((k.status == "Standing").mean()), 3) if len(k) else "",
               lat=round(float(sub.lat.mean()), 4), lon=round(float(sub.lon.mean()), 4))
    slrows.append(row)
    feats.append({"type": "Feature", "properties": row, "geometry": {"type": "MultiLineString", "coordinates": lines}})
slrows.sort(key=lambda r: -r["n_sites"])
pd.DataFrame(slrows).to_csv(os.path.join(D, "stop_lines.csv"), index=False)
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(D, "stop_lines.geojson"), "w"))
sl_ids = set()
for r in slrows: sl_ids |= set(mem[r["group_id"]])
R["n_stop_line_groups"] = len(slrows); R["n_on_stop_lines"] = len(sl_ids); R["share_on_stop_lines"] = len(sl_ids) / N
R["stop_lines_drawn_km"] = float(sum(r["drawn_km"] for r in slrows))
R["stop_lines_top"] = slrows[:15]
ghq = [r for r in slrows if "GHQ Line" in r["name"]]
R["ghq_sections"] = len(ghq); R["ghq_sites"] = int(len(set().union(*[set(mem[r["group_id"]]) for r in ghq])))
R["ghq_drawn_km"] = float(sum(r["drawn_km"] for r in ghq))
gq = S.loc[list(set().union(*[set(mem[r["group_id"]]) for r in ghq]))]; gk = gq[gq.status != "Not known"]
R["ghq_share_standing_known"] = float((gk.status == "Standing").mean())
tl = [r for r in slrows if r["name"] == "Southern Command: Taunton Stop Line"][0]; R["taunton"] = tl
R["taunton_wiki_pillboxes_1942"] = 309
sl = S.loc[list(sl_ids)]; slk = sl[sl.status != "Not known"]; nsl = S.drop(index=list(sl_ids)); nslk = nsl[nsl.status != "Not known"]
R["stop_line_share_standing_known"] = float((slk.status == "Standing").mean()); R["off_line_share_standing_known"] = float((nslk.status == "Standing").mean())
best = [r for r in slrows if r["n_sites"] >= 40 and r["share_standing_known"] != ""]
best.sort(key=lambda r: -r["share_standing_known"])
R["stop_lines_best_survival"] = best[:5]; R["stop_lines_worst_survival"] = best[-5:][::-1]; R["n_stop_lines_40plus"] = len(best)
R["stop_line_cut_km"] = CUT / 1000

# ======================================================== the coast and Operation Sea Lion
land = json.load(open("/home/claude/hist/_data3/ne/geojson/ne_10m_land.geojson"))["features"]
polys = []
for f in land:
    g = shape(f["geometry"])
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        b = p.bounds
        if b[0] < -11 or b[2] > 2.5 or b[1] < 49.5 or b[3] > 61.5: continue
        polys.append(shapely.transform(p, lambda c: np.c_[fwd.transform(c[:, 0], c[:, 1])]))
gbp = [p for p in polys if p.contains(Point(fwd.transform(-1.9, 52.5)))][0]
ring = LineString(gbp.exterior.coords); L = ring.length
OSN = {}
for r in csv.reader(open("/home/claude/hist/osnames_gb.tsv"), delimiter="\t"):
    if r[0] == "name1" or r[4] not in ("populatedPlace", "landform"): continue
    OSN.setdefault((r[0], r[12]), (float(r[8]), float(r[9])))
PL = {"Land's End": ("Land's End", "Cornwall"), "Berwick-upon-Tweed": ("Berwick-upon-Tweed", "Northumberland"), "Dover": ("Dover", "Kent"),
      "Folkestone": ("Folkestone", "Kent"), "New Romney": ("New Romney", "Kent"), "Rye": ("Rye", "East Sussex"), "Hastings": ("Hastings", "East Sussex"),
      "Bexhill": ("Bexhill-on-Sea", "East Sussex"), "Eastbourne": ("Eastbourne", "East Sussex"), "Beachy Head": ("Beachy Head", "East Sussex"),
      "Brighton": ("Brighton", "The City of Brighton and Hove"), "Hythe": ("Hythe", "Kent"), "Ramsgate": ("Ramsgate", "Kent")}
pos = {k: ring.project(Point(OSN[v])) for k, v in PL.items()}


def arc(a, b, via=None):
    """Coast between positions a and b; the shorter way round unless `via` must be on it."""
    lo, hi = sorted((a, b))
    inner = substring(ring, lo, hi)
    outer = MultiLineString([substring(ring, hi, L), substring(ring, 0, lo)])
    if via is not None: return inner if lo <= via <= hi else outer
    return inner if inner.length <= outer.length else outer


SE = arc(pos["Land's End"], pos["Berwick-upon-Tweed"], via=pos["Dover"])
BEACH = {"B": ("Folkestone", "New Romney"), "C": ("Rye", "Hastings"), "D": ("Bexhill", "Eastbourne"), "E": ("Beachy Head", "Brighton")}
beach_lines = {k: arc(pos[a], pos[b]) for k, (a, b) in BEACH.items()}
LAND = unary_union(list(beach_lines.values()))
REST = SE.difference(LAND.buffer(1))
R["coast"] = dict(se_km=SE.length / 1000, landing_km=LAND.length / 1000, rest_km=REST.length / 1000, landing_share_of_se=LAND.length / SE.length,
                  beaches={k: dict(start=a, end=b, km=beach_lines[k].length / 1000) for k, (a, b) in BEACH.items()})
R["coast"]["note"] = ("The definitive order of battle adopted on 30 August 1940 envisaged landings on beach B between Folkestone and New Romney, "
                      "beach C between Rye and Hastings, beach D between Bexhill and Eastbourne and beach E between Beachy Head and Brighton "
                      "(Wikipedia, Operation Sea Lion, citing McKinstry 2014, p. 315). A single airborne division would land in Kent north of Hythe.")
pts = shapely.points(S.x.values, S.y.values)
S["d_landing_km"] = shapely.distance(pts, LAND) / 1000; S["d_rest_km"] = shapely.distance(pts, REST) / 1000
S["d_se_km"] = np.minimum(S.d_landing_km, S.d_rest_km)
S["d_coast_km"] = shapely.distance(pts, shapely.boundary(shapely.union_all([p for p in polys if p.area > 5e6]))) / 1000


def coastal(df, km):
    land_ = (df.d_landing_km <= km) & (df.d_landing_km <= df.d_rest_km)
    rest_ = (df.d_rest_km <= km) & ~land_
    nl, nr = int(land_.sum()), int(rest_.sum())
    dl = nl / R["coast"]["landing_km"]; dr = nr / R["coast"]["rest_km"]
    return dict(km=km, landing=nl, rest=nr, per_km_landing=dl, per_km_rest=dr, ratio=dl / dr if dr else None,
                share_of_se_coastal_in_landing=nl / (nl + nr) if nl + nr else None)


R["sealion"] = {}
for nm, mask in [("all", S.fam >= 0), ("pillboxes", S.fam == 0), ("antitank", S.fam == 1), ("guns", S.fam == 2), ("landing_obstacles", S.fam == 4)]:
    R["sealion"][nm] = {str(km): coastal(S[mask], km) for km in (5, 10, 20)}
# sensitivity: one continuous front from Folkestone to Brighton (filling the gap at Dungeness)
LAND2 = arc(pos["Folkestone"], pos["Brighton"]); REST2 = SE.difference(LAND2.buffer(1))
dl2 = shapely.distance(pts, LAND2) / 1000; dr2 = shapely.distance(pts, REST2) / 1000
R["sealion_continuous"] = {"landing_km": LAND2.length / 1000, "rest_km": REST2.length / 1000}
for nm, mask in [("all", (S.fam >= 0).values), ("pillboxes", (S.fam == 0).values)]:
    l2 = (dl2 <= 10) & (dl2 <= dr2) & mask; r2 = (dr2 <= 10) & ~((dl2 <= 10) & (dl2 <= dr2)) & mask
    R["sealion_continuous"][nm] = dict(landing=int(l2.sum()), rest=int(r2.sum()), ratio=(l2.sum() / (LAND2.length / 1000)) / (r2.sum() / (REST2.length / 1000)))
R["n_within10_se"] = int((S.d_se_km <= 10).sum()); R["share_within10_se"] = R["n_within10_se"] / N
R["n_within10_anycoast"] = int((S.d_coast_km <= 10).sum()); R["share_within10_anycoast"] = R["n_within10_anycoast"] / N
land10 = ((S.d_landing_km <= 10) & (S.d_landing_km <= S.d_rest_km)).values
bd = np.vstack([shapely.distance(pts, beach_lines[k]) for k in BEACH]); nb = bd.argmin(0)
for bi, (k, ln) in enumerate(beach_lines.items()):
    n = int((land10 & (nb == bi)).sum())
    R["coast"]["beaches"][k]["n10"] = n; R["coast"]["beaches"][k]["per_km"] = n / (ln.length / 1000)

# 25 km coastal segments from Land's End to Berwick: works within 10 km, nearest segment
segl = 25000.0
parts = list(SE.geoms) if SE.geom_type == "MultiLineString" else [SE]
seq = shapely.line_merge(MultiLineString(parts)) if len(parts) > 1 else parts[0]
if seq.geom_type == "MultiLineString": seq = max(seq.geoms, key=lambda g: g.length)
if Point(seq.coords[0]).distance(Point(OSN[PL["Land's End"]])) > Point(seq.coords[-1]).distance(Point(OSN[PL["Land's End"]])): seq = LineString(list(seq.coords)[::-1])
nseg = int(math.ceil(seq.length / segl))
segs = [substring(seq, i * segl, min((i + 1) * segl, seq.length)) for i in range(nseg)]
near = (S.d_se_km <= 10).values
idx_near = np.where(near)[0]
segtree = shapely.STRtree(segs)
nearest = segtree.query_nearest(pts[idx_near], return_distance=False)[1]
cnt = np.bincount(nearest, minlength=nseg)
cnt_pb = np.bincount(nearest[(S.fam.values[idx_near] == 0)], minlength=nseg)
srows = []
for i, sgm in enumerate(segs):
    mid = sgm.interpolate(0.5, normalized=True); lon, lat = inv.transform(mid.x, mid.y)
    ov = sgm.intersection(LAND.buffer(50)).length / sgm.length
    inl = ov > 0.5
    srows.append(dict(seg=i, start_km=i * segl / 1000, km=sgm.length / 1000, lat=round(lat, 4), lon=round(lon, 4), n10=int(cnt[i]), n10_pillbox=int(cnt_pb[i]),
                      per_km=cnt[i] / (sgm.length / 1000), landing=bool(inl), landing_share=round(min(1.0, ov), 3)))
pd.DataFrame(srows).to_csv(os.path.join(D, "coast_segments.csv"), index=False)
R["coast_segments"] = srows
rank = sorted(srows, key=lambda r: -r["per_km"])
R["coast_seg_n"] = nseg; R["coast_seg_km"] = segl / 1000
R["coast_seg_top"] = [dict(r, rank=i + 1) for i, r in enumerate(rank[:8])]
R["coast_seg_landing_ranks"] = [i + 1 for i, r in enumerate(rank) if r["landing"]]
R["coast_seg_touch_ranks"] = [dict(rank=i + 1, share=r["landing_share"], per_km=r["per_km"], lat=r["lat"], lon=r["lon"]) for i, r in enumerate(rank) if r["landing_share"] > 0.05]
json.dump({"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"beach": k, "from": BEACH[k][0], "to": BEACH[k][1], "km": round(beach_lines[k].length / 1000, 1)},
     "geometry": mapping(shapely.transform(beach_lines[k].simplify(100), lambda c: np.round(np.c_[inv.transform(c[:, 0], c[:, 1])], 5)))} for k in BEACH]},
    open(os.path.join(D, "sealion_coast.geojson"), "w"))
R["places_used"] = {k: dict(zip(["lat", "lon"], [round(v, 5) for v in inv.transform(*OSN[v])[::-1]])) for k, v in PL.items()}

# ======================================================== OpenStreetMap: pillboxes mapped today
O = pd.read_csv(os.path.join(D, "osm_pillboxes.csv")); ox, oy = fwd.transform(O.lon.values, O.lat.values)
tree = cKDTree(np.c_[ox, oy]); dd, ii = tree.query(np.c_[S.x.values, S.y.values])
S["osm_pillbox_m"] = np.round(dd, 1)
pbm = S[S.fam == 0]
R["osm"] = dict(n_osm_pillboxes=int(len(O)))
for m in (50, 100, 250):
    R["osm"][f"within{m}"] = int((pbm.osm_pillbox_m <= m).sum()); R["osm"][f"share{m}"] = float((pbm.osm_pillbox_m <= m).mean())
    for st in ["Standing", "Gone", "Not known"]:
        g = pbm[pbm.status == st]
        R["osm"][f"share{m}_{st.replace(' ', '_').lower()}"] = float((g.osm_pillbox_m <= m).mean()) if len(g) else None
# OSM pillboxes with no DoB record of any kind within 250 m
dtree = cKDTree(np.c_[S.x.values, S.y.values]); d2, _ = dtree.query(np.c_[ox, oy])
R["osm"]["osm_without_dob_250"] = int((d2 > 250).sum()); R["osm"]["osm_without_dob_250_share"] = float((d2 > 250).mean())
R["osm_meta"] = json.load(open(os.path.join(ROOT, "work", "layers_meta.json")))

# ======================================================== wider layers
AF = pd.read_csv(os.path.join(D, "airfields.csv")); RA = pd.read_csv(os.path.join(D, "radar.csv")); PO = pd.read_csv(os.path.join(D, "naval_ports.csv")); FO = pd.read_csv(os.path.join(D, "coastal_forts.csv"))
R["layers"] = dict(airfields=int(len(AF)), airfields_wartime=int((AF.era == "wartime").sum()), airfields_nodate=int((AF.era == "dates not recorded").sum()),
                   airfields_post=int((AF.era == "outside 1939 to 1945").sum()), radar=int(len(RA)), radar_ch_table=int(RA.source.str.startswith("Wikipedia").sum()),
                   ports=int(len(PO)), dockyards=int((PO.kind == "Naval dockyard").sum()), forts=int(len(FO)),
                   martello=int(FO.classes.str.contains("Martello").sum()), batteries=int(FO.classes.str.contains("battery").sum()))
afx, afy = fwd.transform(AF.lon.values, AF.lat.values); afp = shapely.points(afx, afy)
afw = AF.era != "outside 1939 to 1945"
R["layers"]["airfields_within10_landing"] = int(((shapely.distance(afp, LAND) / 1000 <= 10) & afw).sum())
R["layers"]["airfields_within10_rest"] = int(((shapely.distance(afp, REST) / 1000 <= 10) & afw & ~(shapely.distance(afp, LAND) / 1000 <= 10)).sum())
R["layers"]["airfields_per100km_landing"] = R["layers"]["airfields_within10_landing"] / R["coast"]["landing_km"] * 100
R["layers"]["airfields_per100km_rest"] = R["layers"]["airfields_within10_rest"] / R["coast"]["rest_km"] * 100
# DoB airfield defence records within 2 km of a listed airfield
atree = cKDTree(np.c_[afx[afw.values], afy[afw.values]]); da, _ = atree.query(np.c_[S.x.values, S.y.values])
R["layers"]["dob_within2_airfield"] = int((da <= 2000).sum()); R["layers"]["dob_within2_airfield_share"] = float((da <= 2000).mean())
pbt = S.fam == 0
R["layers"]["pillbox_within2_airfield"] = int(((da <= 2000) & pbt).sum()); R["layers"]["pillbox_within2_airfield_share"] = float(((da <= 2000) & pbt).sum() / pbt.sum())
R["layers"]["air_ministry_pillboxes"] = int((S.type == "PILLBOX (AIR MINISTRY PATTERN)").sum())
R["layers"]["pickett_hamilton"] = int((S.type == "PICKETT HAMILTON FORT").sum())

# ======================================================== density on a 10 km grid
gx = (S.x // 10000).astype(int); gy = (S.y // 10000).astype(int)
cells = collections.Counter(zip(gx, gy))
R["grid_cells_occupied"] = len(cells); R["grid_max"] = max(cells.values())
top = cells.most_common(5)
R["grid_top"] = [dict(n=v, lat=round(inv.transform(cx * 10000 + 5000, cy * 10000 + 5000)[1], 3), lon=round(inv.transform(cx * 10000 + 5000, cy * 10000 + 5000)[0], 3)) for (cx, cy), v in top]
grid = [[int(cx), int(cy), int(v)] for (cx, cy), v in cells.items()]

# ======================================================== write
keep = ["recno", "uorn", "type", "fam", "condition", "status", "period", "lat", "lon", "coord_source", "county", "groups", "built_year", "last_visit_year",
        "d_landing_km", "d_rest_km", "d_coast_km", "osm_pillbox_m"]
out = S[keep].copy(); out["family"] = out.fam.map(lambda i: FAM[i]); out = out.drop(columns="fam")
for c in ["d_landing_km", "d_rest_km", "d_coast_km"]: out[c] = out[c].round(2)
out.to_csv(os.path.join(D, "dob_sites_derived.csv"), index=False)


def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    return o


json.dump(clean(R), open(os.path.join(D, "results.json"), "w"), indent=1)

# compact page data
types = list(tc.index); tix = {t: i for i, t in enumerate(types)}
STI = {"Standing": 0, "Gone": 1, "Not known": 2}
gname = {int(r["group_id"]): i for i, r in enumerate(slrows)}
site_rows = []
for r in S.itertuples():
    gl = [gname[int(g)] for g in str(r.group_ids).split(";") if g and int(g) in gname]
    site_rows.append([round(r.lat, 4), round(r.lon, 4), int(r.fam), cond_order.index(r.condition), tix[r.type], (gl[0] if len(gl) == 1 else gl) if gl else -1, int(r.recno)])
def cellbox(cx, cy):
    lo0, la0 = inv.transform(cx * 10000, cy * 10000); lo1, la1 = inv.transform(cx * 10000 + 10000, cy * 10000 + 10000)
    return [round(la0, 4), round(lo0, 4), round(la1, 4), round(lo1, 4)]


site = dict(R=clean(R), s=site_rows, t=types, cond=cond_order, sl=[dict(n=r["name"], k=r["n_sites"], km=r["drawn_km"], st=r["share_standing_known"]) for r in slrows],
            slg=[{f["properties"]["group_id"]: f for f in feats}[r["group_id"]]["geometry"]["coordinates"] for r in slrows], grid=[cellbox(cx, cy) + [n] for cx, cy, n in grid],
            af=[[r.lat, r.lon, (r.label if isinstance(r.label, str) and r.label else "Airfield (no English label)"), r.era, (r.start if r.start == r.start else ""), (r.end if r.end == r.end else ""), r.qid] for r in AF.itertuples()],
            ra=[[r.lat, r.lon, r.name, r.source.split(",")[0], r.qid if isinstance(r.qid, str) else ""] for r in RA.itertuples()],
            po=[[r.lat, r.lon, r.name, r.kind, r.note] for r in PO.itertuples()],
            fo=[[r.lat, r.lon, (r.label if isinstance(r.label, str) and r.label else "unnamed"), r.classes, r.qid] for r in FO.itertuples()],
            op=[[round(a, 5), round(b, 5)] for a, b in zip(O.lat, O.lon)],
            sea=json.load(open(os.path.join(D, "sealion_coast.geojson"))))
json.dump(site, open(os.path.join(ROOT, "work", "site.json"), "w"), separators=(",", ":"))
print(json.dumps({k: R[k] for k in ["n_sites", "fam_counts", "condition", "share_standing_known", "n_stop_line_groups", "n_on_stop_lines"]}, indent=0))
print(json.dumps(R["coast"], indent=0)); print(json.dumps(R["sealion"]["all"], indent=0)); print(json.dumps(R["sealion"]["pillboxes"]["10"]))
print(R['sealion_continuous']); print(R["coast_seg_top"][:5], R["coast_seg_landing_ranks"]); print(json.dumps(R["osm"])); print(json.dumps(R["layers"]))
print(R["stop_lines_best_survival"], R["stop_lines_worst_survival"]); print(R["ghq_sites"], R["ghq_drawn_km"], R["stop_lines_drawn_km"])
print("site.json KB", os.path.getsize(os.path.join(ROOT, "work", "site.json")) // 1024)
