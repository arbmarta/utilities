import os
import re

import geopandas as gpd

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "inputs", "index", "tiles.geojson")
CSDS = os.path.join(ROOT, "inputs", "urban_csds", "urban_csds.gpkg")
OUT = os.path.join(ROOT, "outputs", "needed_tiles.txt")

BUFFER_M = 2000

tiles = gpd.read_file(INDEX)
csds = gpd.read_file(CSDS)
print("index: %d tiles, crs %s" % (len(tiles), tiles.crs))
print("columns: %s" % ", ".join(tiles.columns))

# the tile id is whichever column holds quadkey-shaped values
col = None
for c in tiles.columns:
    if c != "geometry" and tiles[c].astype(str).head(50).str.fullmatch(r"[0-3]{6,14}").all():
        col = c
        break
if col is None:
    raise SystemExit("No quadkey column found in: %s" % ", ".join(tiles.columns))
print("tile id column: %s" % col)

buf = csds.to_crs(3347).buffer(BUFFER_M).to_crs(tiles.crs)
hits = gpd.sjoin(tiles, gpd.GeoDataFrame(geometry=buf, crs=tiles.crs),
                 predicate="intersects")

ids = sorted(set(hits[col].astype(str)))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write("\n".join(ids) + "\n")

print("%d tiles needed -> outputs/required_tiles.txt" % len(ids))