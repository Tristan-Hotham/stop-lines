# Reddit post

## Title

[OC] Did Britain fortify the right beaches in 1940? The 14,690 pillboxes, anti-tank blocks and stop lines recorded by Defence of Britain volunteers, with the beaches Operation Sea Lion planned to land on: 2.3 times the average density of defence, but the densest coast was elsewhere

## Body

In 1940 Britain built thousands of pillboxes and inland "stop lines". Between 1995 and 2002 volunteers recorded what was left, and I mapped their 14,690 records. Pillboxes are 55% of them, and 90 named stop lines hold 37% of all sites. The German plan of 30 August 1940 put the first wave between Folkestone and Brighton: within 10 km of those beaches there are 2.3 times as many recorded defences per km of coast as along the rest of the south and east coast, almost all of it at the Folkestone end. 71% of sites with a known condition were still standing: 81% of pillboxes but 12% of beach obstacles. Caveat: this maps what volunteers recorded, and some counties had far more volunteers than others (the densest recorded coast is Teesside).

Interactive version: https://tristan-hotham.github.io/stop-lines/

## Source comment

Source: Defence of Britain Archive, Council for British Archaeology (2002, updated 2006), Archaeology Data Service, https://doi.org/10.5284/1000327 (data copyright CBA; non-commercial reuse with acknowledgement; my derived data CC BY-NC 4.0); Operation Sea Lion landing beaches as summarised in Wikipedia's "Operation Sea Lion" article (CC BY-SA 4.0); towns placed with Ordnance Survey OS Open Names (Open Government Licence v3.0; contains OS data © Crown copyright and database right 2026); Natural Earth 1:10m coastline (public domain). Airfields, radar and dockyards on the interactive page from Wikidata (CC0), Wikipedia and OpenStreetMap (© OpenStreetMap contributors, ODbL).

Tools: Python (pandas, NumPy, SciPy, Shapely, pyproj, matplotlib). Stop lines drawn as minimum spanning trees through each named group's recorded sites; coast density counts sites within 10 km per km of coast, each site assigned to the nearer coast.

Interactive version: https://tristan-hotham.github.io/stop-lines/
Blog post: https://blog.tristanhotham.com/2026/10/28/stop-lines/
Paper: https://doi.org/10.5281/zenodo.23727131
