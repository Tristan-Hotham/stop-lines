# Britain's last line of defence

**Where Britain built its 1940 pillboxes, anti-tank obstacles and stop lines, how much was recorded as surviving, and whether they sat where the Germans planned to land.** With airfields, radar stations, naval dockyards and coastal batteries layered on, for a fuller picture of defended Britain.

Interactive page: https://tristan-hotham.github.io/stop-lines/
Paper: https://doi.org/10.5281/zenodo.23727131
Blog post: https://blog.tristanhotham.com/2026/10/28/stop-lines/

Dr Tristan Hotham, Independent researcher (ORCID 0000-0003-4931-9349)

## Headline results

- The Defence of Britain Project database holds {{n_sites|int}} located wartime defence sites, mostly recorded between 1994 and 2002. {{n_pillbox|int}} are pillboxes ({{fam_share.0|pct0}}) and {{fam_counts.1|int}} are anti-tank obstacles. {{share_built_1940|pct0}} of the records with a construction date are dated 1940.
- {{status_standing|int}} sites ({{share_standing_all|pct0}}) were recorded as standing, {{status_gone|int}} ({{share_gone_all|pct0}}) as removed or infilled, and {{status_not_known|int}} as unknown. Of those with a known condition, {{share_standing_known|pct0}} stood: {{fam_status.0.share_standing_known|pct0}} of pillboxes but only {{fam_status.4.share_standing_known|pct0}} of beach and landing obstacles, mines and flame traps. {{pillbox_standing|int}} pillboxes were recorded as standing, close to the commonly quoted figure of about {{refs.survive_total|int}} survivors (an estimate that rests largely on this survey).
- {{n_stop_line_groups|int}} named stop lines hold {{n_on_stop_lines|int}} sites ({{share_on_stop_lines|pct0}}); joining neighbouring sites draws {{stop_lines_drawn_km|int}} km of line. The GHQ Line's {{ghq_sections|int}} recorded sections hold {{ghq_sites|int}} sites. Stop line sites survived better ({{stop_line_share_standing_known|pct0}} standing of those known) than other sites ({{off_line_share_standing_known|pct0}}).
- The four Operation Sea Lion landing beaches of the 30 August 1940 plan (Folkestone to New Romney, Rye to Hastings, Bexhill to Eastbourne, Beachy Head to Brighton) are {{coast.landing_km|int}} km of coast. Within 10 km they have {{sealion.all.10.per_km_landing|f1}} recorded sites per km against {{sealion.all.10.per_km_rest|f1}} along the rest of the south and east coast from Land's End to Berwick: {{sealion.all.10.ratio|f1}} times the density ({{sealion.pillboxes.10.ratio|f1}} times for pillboxes; {{sealion.all.5.ratio|f1}} at 5 km, {{sealion.all.20.ratio|f1}} at 20 km).
- The lead comes from beach B, Folkestone to New Romney ({{coast.beaches.B.per_km|f1}} per km); beach C, Rye to Hastings, has {{coast.beaches.C.per_km|f1}}, no more than the average coast. The densest recorded {{coast_seg_km|int}} km of coast is Teesside around Redcar, a reminder that recording effort varied (Redcar and Cleveland has {{county_named.Redcar & Cleveland|int}} records, Devon {{county_named.Devon|int}}).
- Only {{osm.share50|pct0}} of recorded pillboxes have a pillbox mapped on OpenStreetMap within 50 m today ({{osm.share50_standing|pct0}} of those recorded standing, {{osm.share50_gone|pct1}} of those recorded gone).
- {{layers.pillbox_within2_airfield|int}} recorded pillboxes ({{layers.pillbox_within2_airfield_share|pct0}}) are within 2 km of one of the {{layers.airfields|int}} airfields and RAF stations in Wikidata; the Sea Lion coast has {{layers.airfields_per100km_landing|f1}} airfields within 10 km per 100 km of coast against {{layers.airfields_per100km_rest|f1}} elsewhere on the south and east coast.

## Files

- `index.html`: the interactive page (single file; Leaflet 1.9.4 from cdnjs; Esri Canvas tiles).
- `header.png`: social card.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage.
- `data/dob_sites.csv`: one row per Defence of Britain site record: record number, type, KMZ category, condition, period, coordinates and their source, grid reference precision, distance between the KMZ point and the grid reference, county, groups, construction and last visit years. Derived fields only.
- `data/dob_sites_derived.csv`: the same sites with my family, survival status, distances to the Sea Lion coast, the rest of the south and east coast and any coast, and the distance to the nearest OpenStreetMap pillbox.
- `data/dob_groups.csv`: the named DoB groups with my kind (stop line, coast defences, nodal point, anti-tank island, airfield defences, other) and member counts.
- `data/stop_lines.csv`, `data/stop_lines.geojson`: the stop lines as drawn (minimum spanning tree of member sites, links up to {{stop_line_cut_km|int}} km).
- `data/sealion_coast.geojson`, `data/coast_segments.csv`: the four landing beaches and the {{coast_seg_km|int}} km coastal stretches with their counts.
- `data/airfields.csv`, `data/radar.csv`, `data/naval_ports.csv`, `data/coastal_forts.csv`: the wider layers, with the source of every coordinate.
- `data/osm_pillboxes.csv`: OpenStreetMap pillboxes (ODbL).
- `code/`: the scripts, run in order.
- `release/`: paper (PDF and LaTeX), blog figures and post, Zenodo files. `reddit/`: the collage.

## How to rerun

Python 3 with pandas, numpy, scipy, shapely 2, pyproj and matplotlib (Playwright for the header). The input bundles are not redistributed here; paths at the top of each script point at local copies.

```
cd code
python3 01_dob.py        # Defence of Britain tables -> data/dob_sites.csv, dob_groups.csv
python3 02_layers.py     # airfields, radar, dockyards, batteries, OSM pillboxes
python3 03_analysis.py   # families, survival, stop lines, coast test, OSM check -> data/results.json
python3 04_build_site.py # index.html and README.md from the templates
python3 05_header.py     # header.png
```

## Method notes and caveats

- This is a map of what volunteers recorded, mostly between 1994 and 2002, not of what was built. Recording effort varied greatly between counties, and some areas were covered far more thoroughly than others. Condition was judged on a single visit and will have changed since.
- Coordinates come from the ADS Google Earth (KMZ) file of the whole dataset; half lie within {{dob_meta.kmz_vs_grid_median_m|int}} m of the database's own grid reference as I convert it, and {{dob_meta.kmz_vs_grid_share_within_100m|pct0}} within 100 m.
- The six families are my keyword groupings of {{n_types|int}} DoB site types (see `family()` in `03_analysis.py`).
- Stop lines are drawn through recorded sites only, so they understate the real lines where recording was thin and show branches where a group includes outlying sites.
- The Sea Lion beaches are as summarised in the Wikipedia article on Operation Sea Lion (citing McKinstry 2014); the towns are placed at OS Open Names points and the coast is the Natural Earth 1:10m coastline, so lengths are approximate. The gap between New Romney and Rye (Dungeness) is not a landing beach in this plan; treating Folkestone to Brighton as one front gives {{sealion_continuous.all.ratio|f1}} times the density.
- OpenStreetMap and Wikidata coverage is uneven; the OpenStreetMap check measures mapping, not survival. Wikidata "wartime" status depends on dates that many items lack.

## Sources and licences

- **Defence of Britain Archive**, Council for British Archaeology (2002, updated 2006), Archaeology Data Service, https://doi.org/10.5284/1000327. Data copyright Council for British Archaeology unless otherwise stated; reused under the ADS Terms of Use and Access (free reuse for non-commercial research and education with acknowledgement). KMZ compiled by Steven Thompson. No personal data (recorder or contact details) are used or published.
- **Wikidata** (CC0) and **OpenStreetMap** (© OpenStreetMap contributors, ODbL 1.0), retrieved 28 October 2026 via QLever.
- **Wikipedia** (CC BY-SA 4.0): Operation Sea Lion; British anti-invasion preparations of the Second World War; British hardened field defences of World War II; GHQ Line; Taunton Stop Line; Chain Home; Royal Navy Dockyard; HMNB Portsmouth; HMNB Devonport; Rosyth Dockyard.
- **OS Open Names**: contains OS data © Crown copyright and database right 2026 (Open Government Licence v3.0).
- **Natural Earth** 1:10m land (public domain).

Licence: derived data and text are released under **CC BY-NC 4.0**, because they derive from the Defence of Britain database, whose terms allow non-commercial reuse with acknowledgement; rows derived from OpenStreetMap remain under the ODbL. Code is MIT (see LICENSE).

## Citation

Hotham, T. (2026). Britain's Last Line of Defence: Pillboxes, Stop Lines and the Sea Lion Coast in the Defence of Britain Database. Zenodo. https://doi.org/10.5281/zenodo.23727131

## Use of AI

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
