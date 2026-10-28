"""Step 2: the wider wartime map: airfields, radar, naval dockyards and bases, coastal forts and
batteries, and what OpenStreetMap maps today.

Sources (read in place):
- Wikidata (CC0) and OpenStreetMap (ODbL) via QLever: /home/claude/hist/_data11/wd_osm_bundle11.json.gz
  (wd_military, osm_military, osm_historic_military, osm_aerodromes).
- English Wikipedia (CC BY-SA 4.0): /home/claude/hist/_data11/wikipedia_batch11.json.gz
  ("Chain Home": the table of Chain Home sites with grid references; "Royal Navy Dockyard": the
  list of United Kingdom dockyards with dates; article coordinates for HMNB Portsmouth,
  HMNB Devonport and Rosyth Dockyard).
- OS Open Names (OGL v3) to place named towns: /home/claude/hist/osnames_gb.tsv

Wartime filter: a Wikidata item counts as wartime when its earliest inception or opening date is
1945 or earlier and its latest dissolution or closing date is 1939 or later; items with no dates
are kept and flagged "dates not recorded".
Outputs: ../data/airfields.csv, ../data/radar.csv, ../data/naval_ports.csv,
../data/coastal_forts.csv, ../data/osm_pillboxes.csv, ../work/layers_meta.json
Run: python3 02_layers.py
"""
import csv, gzip, io, json, os, re, collections
import numpy as np
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
WO = json.load(gzip.open("/home/claude/hist/_data11/wd_osm_bundle11.json.gz"))["results"]
WP = json.load(gzip.open("/home/claude/hist/_data11/wikipedia_batch11.json.gz"))["articles"]


def tsv(k): return list(csv.DictReader(io.StringIO(WO[k]["tsv"]), delimiter="\t"))


def yr(s):
    m = re.search(r"(-?\d{4})-", s or ""); return int(m.group(1)) if m else None


def inuk(lat, lon): return 49.8 <= lat <= 61.0 and -8.7 <= lon <= 2.0


def hav(la1, lo1, la2, lo2):
    p = np.radians; a = np.sin(p(la2 - la1) / 2) ** 2 + np.cos(p(la1)) * np.cos(p(la2)) * np.sin(p(lo2 - lo1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def write(name, rows):
    with open(os.path.join(ROOT, "data", name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


# ---------------- Wikidata military items
items = collections.defaultdict(list)
for r in tsv("wd_military"): items[r["?s"]].append(r)
wd = []
for s, rs in items.items():
    m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", rs[0]["?coord"] or "")
    if not m: continue
    lon, lat = float(m.group(1)), float(m.group(2))
    if not inuk(lat, lon): continue
    st = [y for r in rs for y in (yr(r["?inc"]), yr(r["?open"])) if y]; en = [y for r in rs for y in (yr(r["?dis"]), yr(r["?close"])) if y]
    s0 = min(st) if st else None; e0 = max(en) if en else None
    if s0 is None and e0 is None: era = "dates not recorded"
    elif (s0 is None or s0 <= 1945) and (e0 is None or e0 >= 1939): era = "wartime"
    else: era = "outside 1939 to 1945"
    wd.append(dict(qid=s.rsplit("/", 1)[-1].strip(">"), label=re.sub(r"@en$", "", rs[0]["?label"]),
                   classes=";".join(sorted({re.sub(r"@en$", "", r["?clsl"]) for r in rs})), lat=round(lat, 5), lon=round(lon, 5),
                   start=s0 or "", end=e0 or "", era=era))
print("Wikidata UK military items", len(wd))

# ---------------- airfields: RAF stations, aerodromes, naval air stations, seaplane bases
AIR = {"Royal Air Force station", "aerodrome", "Royal Naval Air Station", "seaplane base", "airship hangar"}
air = [dict(r, source="Wikidata") for r in wd if set(r["classes"].split(";")) & AIR and "radar station" not in r["classes"]]
# drop near-duplicates (an RAF station and an aerodrome item for the same field) within 1.5 km
air.sort(key=lambda r: (0 if "Royal Air Force station" in r["classes"] else 1, {"wartime": 0, "dates not recorded": 1}.get(r["era"], 2)))
kept = []
for r in air:
    if any(hav(r["lat"], r["lon"], k["lat"], k["lon"]) < 1.5 for k in kept): continue
    kept.append(r)
air = sorted(kept, key=lambda r: r["label"])
write("airfields.csv", air)

# ---------------- radar: Wikipedia Chain Home table plus Wikidata radar stations
gb = Transformer.from_crs(27700, 4326, always_xy=True); LET = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


def gridref(s):
    s = s.replace(" ", "").upper(); m = re.match(r"^([A-Z]{2})(\d+)$", s)
    if not m or len(m.group(2)) % 2: return None
    a, b = LET.index(m.group(1)[0]), LET.index(m.group(1)[1])
    E0 = (((a - 2) % 5) * 5 + (b % 5)) * 100000; N0 = (19 - (a // 5) * 5 - (b // 5)) * 100000
    k = len(m.group(2)) // 2; p = 10 ** (5 - k)
    e = int(m.group(2)[:k]) * p + p / 2; n = int(m.group(2)[k:]) * p + p / 2
    lon, lat = gb.transform(E0 + e, N0 + n); return lat, lon


ch = WP["Chain Home"]["text"]; i = ch.find("==Chain Home sites=="); tab = ch[i:ch.find("|}", i)]
radar = []; ch_nocoord = []
for row in tab.split("\n|-")[1:]:
    cells = [c.strip() for c in re.split(r"\|\|", row.strip().lstrip("|"))]
    if len(cells) < 5: continue
    clean = lambda c: re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", c).strip()
    site = clean(cells[0]); region = clean(cells[3])
    g = re.search(r"gbmappingsmall\|([A-Z]{2}\s*\d+)", cells[4]) or re.match(r"^\s*([A-Z]{2}\d{4,10})\s*$", cells[4])
    ll = gridref(g.group(1)) if g else None
    if not ll: ch_nocoord.append(site); continue
    radar.append(dict(name=site, region=region, lat=round(ll[0], 5), lon=round(ll[1], 5), source="Wikipedia, Chain Home (table of sites, grid reference)", qid=""))
n_ch = len(radar)
for r in wd:
    if "radar station" not in r["classes"] or r["era"] == "outside 1939 to 1945": continue
    if any(hav(r["lat"], r["lon"], k["lat"], k["lon"]) < 3 for k in radar): continue
    radar.append(dict(name=r["label"], region="", lat=r["lat"], lon=r["lon"], source="Wikidata", qid=r["qid"]))
write("radar.csv", radar)
print("radar", len(radar), "from Chain Home table", n_ch, "without coordinates", ch_nocoord)

# ---------------- naval dockyards (Wikipedia "Royal Navy Dockyard", UK yards open in 1939 to 1945) and Wikidata naval bases
OSN = {}
for r in csv.reader(open("/home/claude/hist/osnames_gb.tsv"), delimiter="\t"):
    if r[4] == "populatedPlace" and r[5] in ("Town", "City", "Other Settlement"): OSN.setdefault((r[0], r[12]), (float(r[6]), float(r[7])))
art = lambda t: (WP[t]["coord"]["lat"], WP[t]["coord"]["lon"])
DOCK = [  # name, how the article describes it in the Second World War, coordinate source
    ("Portsmouth Dockyard", "Royal Dockyard since 1496; open throughout", "HMNB Portsmouth", None),
    ("Plymouth (Devonport) Dockyard", "Royal Dockyard since 1690; open throughout", "HMNB Devonport", None),
    ("Chatham Dockyard", "Royal Dockyard 1567 to 1984", None, ("Chatham", "Medway")),
    ("Sheerness Dockyard", "Royal Dockyard 1665 to 1960", None, ("Sheerness", "Kent")),
    ("Pembroke Dockyard", "reopened in the 1930s, closed 1947", None, ("Pembroke Dock", "Sir Benfro - Pembrokeshire")),
    ("Portland Dockyard", "very active through two World Wars, closed 1959", None, ("Fortuneswell", "Dorset")),
    ("Rosyth Dockyard", "reopened 1939", "Rosyth Dockyard", None),
    ("Dover Dockyard", "listed as a Naval Dockyard in both World Wars", None, ("Dover", "Kent")),
    ("Invergordon", "naval oiling station in the Second World War", None, ("Invergordon", "Highland")),
    ("Scapa Flow Dockyard, Lyness", "established 1939, operational through the war", None, ("Lyness", "Orkney Islands")),
]
ports = []
for nm, note, a, o in DOCK:
    if a: (lat, lon), src = art(a), f"Wikipedia, {a} (article coordinates)"
    else: (lat, lon), src = OSN[o], f"OS Open Names, {o[0]} (town point)"
    ports.append(dict(name=nm, kind="Naval dockyard", note=note, lat=round(lat, 5), lon=round(lon, 5), source=src, qid=""))
for r in wd:
    if "naval base" in r["classes"] and r["era"] != "outside 1939 to 1945" and not any(hav(r["lat"], r["lon"], k["lat"], k["lon"]) < 3 for k in ports):
        ports.append(dict(name=r["label"], kind="Naval base", note="Wikidata naval base", lat=r["lat"], lon=r["lon"], source="Wikidata", qid=r["qid"]))
write("naval_ports.csv", ports)
print("ports", len(ports))

# ---------------- coastal forts, batteries and Martello towers (Wikidata)
FORT = {"Martello tower", "artillery battery", "coastal battery", "anti-aircraft battery", "coastal artillery"}
forts = [dict(r, source="Wikidata") for r in wd if set(r["classes"].split(";")) & FORT and r["era"] != "outside 1939 to 1945"]
write("coastal_forts.csv", forts)

# ---------------- OpenStreetMap: pillboxes and other wartime features mapped today
osm_pb = {}; osm_counts = collections.Counter()
for r in tsv("osm_military"):
    osm_counts["military=" + r["?mil"]] += 1
    if "pillbox" in r["?bunker"].lower() or r["?hist"] == "pillbox":
        osm_pb[r["?osm"]] = (float(r["?lat"]), float(r["?lon"]))
for r in tsv("osm_historic_military"):
    if r["?hist"] == "pillbox" or "pillbox" in r["?bunker"].lower():
        osm_pb[r["?osm"]] = (float(r["?lat"]), float(r["?lon"]))
pb = [dict(osm=k.strip("<>").replace("https://www.openstreetmap.org/", ""), lat=round(v[0], 6), lon=round(v[1], 6)) for k, v in sorted(osm_pb.items()) if inuk(*v)]
write("osm_pillboxes.csv", pb)
aer = tsv("osm_aerodromes")
meta = dict(
    wd_items_uk=len(wd), wd_era=dict(collections.Counter(r["era"] for r in wd)),
    airfields=len(air), airfields_era=dict(collections.Counter(r["era"] for r in air)),
    airfields_raf=sum("Royal Air Force station" in r["classes"] for r in air),
    radar=len(radar), radar_chain_home_table=n_ch, radar_wikidata=len(radar) - n_ch, chain_home_rows_no_coords=len(ch_nocoord),
    ports=len(ports), dockyards=len(DOCK), forts=len(forts), forts_by_class=dict(collections.Counter(r["classes"] for r in forts)),
    osm_pillboxes=len(pb), osm_military_bunkers=osm_counts["military=bunker"],
    osm_aerodromes_disused=sum(1 for r in aer if not r["?k"].endswith("Key:aeroway>")),
    osm_aerodromes_military=sum(1 for r in aer if r["?mil"] in ("airfield", "base")),
    osm_historic_military=len(tsv("osm_historic_military")))
json.dump(meta, open(os.path.join(ROOT, "work", "layers_meta.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
