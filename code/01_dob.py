"""Step 1: read the Defence of Britain (DoB) database exports and write clean site and group tables.

Source: Defence of Britain Archive, Council for British Archaeology (2002, updated 2006),
Archaeology Data Service, https://doi.org/10.5284/1000327 (ADS Terms of Use: free reuse for
non-commercial research and education with acknowledgement). Read in place from
/home/claude/hist/_data11/dob_bundle.json.gz (pipe-delimited exports of the Access database plus
the ADS Google Earth KMZ compiled by Steven Thompson).

Only derived variables are written: record number, type of site, the KMZ category, condition,
period, coordinates, the DoB groups a record belongs to, the county, and dates of construction
and of the latest field visit. No descriptions, locations text or personal data (Person.txt and
Company.txt are never read).

Outputs: ../data/dob_sites.csv, ../data/dob_groups.csv, ../work/dob_meta.json
Run: python3 01_dob.py
"""
import base64, csv, gzip, io, json, os, re, zipfile, collections
import xml.etree.ElementTree as ET
import numpy as np
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SRC = "/home/claude/hist/_data11/dob_bundle.json.gz"
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True); os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
B = json.load(gzip.open(SRC))


def table(name):
    return list(csv.DictReader(io.StringIO(B[name]), delimiter="|", quotechar='"'))


# ---- thesaurus and word lists
term = {r["the_te_uid"]: r["term"] for r in table("term.txt")}
term.update({r["TH_T_U_UID"]: r["TERM"] for r in table("uses.txt")})
WL = {r["RecNo"]: r["Word"] for r in table("WordList.txt")}

# ---- site records
objs = table("DOB_Object.txt")
sites = {}
for r in objs:
    t = term.get(r["TypeOfSite"], "")
    sites[r["RecNo"]] = dict(recno=int(r["RecNo"]), uorn=r["UORN"], type=t.strip() or "UNRECORDED",
                             condition=WL.get(r["Condition"], "Unknown"), period=WL.get(r["Period"], "Not recorded"))
print("site records", len(sites))

# ---- KMZ placemarks: coordinates and the KMZ's own category hierarchy
z = zipfile.ZipFile(io.BytesIO(base64.b64decode(B["dob.kmz.b64"])))
root = ET.fromstring(z.read("doc.kml")); NS = "{http://earth.google.com/kml/2.1}"
kmz = collections.defaultdict(list)


def walk(e, path):
    for c in e:
        if c.tag == NS + "Folder": walk(c, path + [c.findtext(NS + "name")])
        elif c.tag == NS + "Document": walk(c, path)
        elif c.tag == NS + "Placemark":
            nm = c.findtext(NS + "name"); co = c.find(".//" + NS + "coordinates")
            m = re.search(r"S(\d{7})", nm)
            if not m or co is None: continue
            lon, lat = [float(v) for v in co.text.strip().split(",")[:2]]
            kmz[str(int(m.group(1)))].append(dict(lat=lat, lon=lon, cat=path[1] if len(path) > 1 else "", sub=path[2] if len(path) > 2 else "",
                                                 ktype=nm.rsplit(":", 1)[0].strip()))


walk(root, [])
n_placemarks = sum(len(v) for v in kmz.values())
print("KMZ placemarks", n_placemarks, "records", len(kmz))

# ---- National Grid references (GB and Irish grids) as a cross-check and fallback
gb = Transformer.from_crs(27700, 4326, always_xy=True); ig = Transformer.from_crs(29903, 4326, always_xy=True)
L = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


def gb_square(p):
    a, b = L.index(p[0]), L.index(p[1])
    e = ((a - 2) % 5) * 5 + (b % 5); n = 19 - (a // 5) * 5 - (b // 5)
    return e * 100000, n * 100000


def ngr(prefix, c1, c2):
    p = prefix.strip().upper()
    if not c1.isdigit() or not c2.isdigit() or len(c1) != len(c2) or not 2 <= len(c1) <= 5: return None
    k = len(c1); prec = 10 ** (5 - k)
    e = int(c1) * prec + prec / 2; n = int(c2) * prec + prec / 2
    if len(p) == 2 and all(ch in L for ch in p):
        E0, N0 = gb_square(p); lon, lat = gb.transform(E0 + e, N0 + n)
    elif len(p) == 1 and p in L:
        i = L.index(p); E0 = (i % 5) * 100000; N0 = (4 - i // 5) * 100000
        lon, lat = ig.transform(E0 + e, N0 + n)
    else:
        return None
    return lat, lon, prec


cart = collections.defaultdict(list)
for r in table("Cartographic_Reference.txt"):
    g = ngr(r["Prefix"], r["Component1"], r["Component2"])
    if g: cart[r["UORN ID"]].append((int(r["Sequence Number"] or 0), g, WL.get(r["Reference Point"], "")))


def hav(la1, lo1, la2, lo2):
    p = np.radians; dl = p(la2 - la1); dn = p(lo2 - lo1)
    a = np.sin(dl / 2) ** 2 + np.cos(p(la1)) * np.cos(p(la2)) * np.sin(dn / 2) ** 2
    return 2 * 6371008.8 * np.arcsin(np.sqrt(a))


# ---- groups (named defence groupings) and links
groups = {r["RecNo"]: r["Name"].strip() for r in table("Groups.txt")}
areas = {r["RecNo"]: r for r in table("Area.txt")}
events = {r["RecNo"]: r for r in table("Event.txt")}
memb = collections.defaultdict(set); county = collections.defaultdict(set); ev = collections.defaultdict(list)
for r in table("Links.txt"):
    f, t, k = r["From"], r["To"], r["LinkTables"]
    if f not in sites: continue
    if k == "6" and t in groups: memb[f].add(t)
    elif k == "9" and t in areas: county[f].add(areas[t]["County"].strip())
    elif k == "2" and t in events: ev[f].append(events[t])


def year(s):
    m = re.match(r"(\d{4})", s or ""); return int(m.group(1)) if m else None


def kind(name):
    n = name.lower()
    if "stop line" in n or "ghq line" in n or "corps line" in n: return "stop line"
    if "coast" in n: return "coast defences"
    if "nodal point" in n: return "nodal point"
    if "anti-tank island" in n or "anti tank island" in n: return "anti-tank island"
    if "airfield" in n or "aerodrome" in n or "raf " in n: return "airfield defences"
    return "other"


rows = []; diffs = []; src_count = collections.Counter()
for rec, s in sites.items():
    pk = kmz.get(rec, []); cg = sorted(cart.get(rec, []))
    g = cg[0][1] if cg else None
    if pk:
        lat, lon = pk[0]["lat"], pk[0]["lon"]; src = "kmz"
        if g: diffs.append(float(hav(lat, lon, g[0], g[1])))
    elif g:
        lat, lon = g[0], g[1]; src = "grid reference"
    else:
        lat = lon = None; src = "none"
    src_count[src] += 1
    cons = [year(e["Start Date"]) for e in ev[rec] if WL.get(e["Type"]) == "Construction" and year(e["Start Date"])]
    vis = [year(e["Start Date"]) for e in ev[rec] if WL.get(e["Type"]) == "Field Visit" and year(e["Start Date"])]
    cat = pk[0]["cat"] if pk else ""; sub = pk[0]["sub"] if pk else ""
    rows.append(dict(recno=s["recno"], uorn=s["uorn"], type=s["type"], kmz_category=cat, kmz_subcategory=sub,
                     condition=s["condition"], period=s["period"],
                     lat=None if lat is None else round(lat, 6), lon=None if lon is None else round(lon, 6), coord_source=src,
                     grid_precision_m=g[2] if g else "", kmz_vs_grid_m=round(float(hav(lat, lon, g[0], g[1])), 1) if (pk and g) else "",
                     county=";".join(sorted(county[rec])), groups=";".join(sorted(groups[x] for x in memb[rec])),
                     group_ids=";".join(sorted(memb[rec], key=int)),
                     built_year=min(cons) if cons else "", last_visit_year=max(vis) if vis else ""))

# fill missing KMZ category from the type (same type in KMZ elsewhere)
t2c = collections.defaultdict(collections.Counter)
for r in rows:
    if r["kmz_category"]: t2c[r["type"]][(r["kmz_category"], r["kmz_subcategory"])] += 1
for r in rows:
    if not r["kmz_category"] and t2c[r["type"]]:
        r["kmz_category"], r["kmz_subcategory"] = t2c[r["type"]].most_common(1)[0][0]
    if not r["kmz_category"]: r["kmz_category"] = "Not categorised"

rows.sort(key=lambda r: r["recno"])
with open(os.path.join(ROOT, "data", "dob_sites.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

gc = collections.Counter(g for v in memb.values() for g in v)
with open(os.path.join(ROOT, "data", "dob_groups.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["group_id", "name", "kind", "members"])
    for gid, nm in sorted(groups.items(), key=lambda x: int(x[0])):
        if gc[gid]: w.writerow([gid, nm, kind(nm), gc[gid]])

d = np.array(diffs)
meta = dict(n_records=len(rows), n_placemarks=n_placemarks, n_kmz_records=len(kmz),
            n_with_grid=sum(1 for r in rows if r["grid_precision_m"] != ""),
            coord_source=dict(src_count), kmz_vs_grid_median_m=float(np.median(d)), kmz_vs_grid_p90_m=float(np.percentile(d, 90)),
            kmz_vs_grid_share_within_100m=float((d <= 100).mean()), kmz_vs_grid_share_within_1km=float((d <= 1000).mean()), n_compared=len(d),
            grid_precision=dict(collections.Counter(str(r["grid_precision_m"]) for r in rows)),
            n_groups=len([g for g in groups if gc[g]]))
json.dump(meta, open(os.path.join(ROOT, "work", "dob_meta.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
