import math
import os
import subprocess

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.windows import Window, from_bounds
from shapely.geometry import box

ROOT = os.path.dirname(os.path.abspath(__file__))
CSDS = os.path.join(ROOT, "inputs", "urban_csds", "urban_csds.gpkg")
TILELIST = os.path.join(ROOT, "outputs", "required_tiles.txt")
TILEDIR = os.path.join(ROOT, "outputs", "tiles")
CITYDIR = os.path.join(ROOT, "outputs", "cities")

BUCKET = "dataforgood-fb-data"
PREFIX = "forests/v2/global/dinov3_global_chm_v2_ml3/chm/"

CANOPY_M = 2
BLOCK = 2048


def clear_partials():
    for d in (TILEDIR, CITYDIR):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".part"):
                os.remove(os.path.join(d, f))
                print("removed partial %s" % f)


def download_tiles():
    os.makedirs(TILEDIR, exist_ok=True)
    ids = [l.strip() for l in open(TILELIST) if l.strip()]

    for i, t in enumerate(ids, 1):
        dest = os.path.join(TILEDIR, "%s.tif" % t)
        if os.path.exists(dest):
            continue
        print("[%d/%d] %s.tif" % (i, len(ids), t))
        part = dest + ".part"
        r = subprocess.run(["aws", "s3", "cp",
                            "s3://%s/%s%s.tif" % (BUCKET, PREFIX, t),
                            part, "--no-sign-request"],
                           capture_output=True, text=True)
        if r.returncode:
            if os.path.exists(part):
                os.remove(part)
            print("   not in bucket, skipped")
        else:
            os.replace(part, dest)

    paths = sorted(os.path.join(TILEDIR, f)
                   for f in os.listdir(TILEDIR) if f.endswith(".tif"))
    print("%d tiles on disk" % len(paths))
    return paths


def tile_index(paths):
    geoms, crs, res, origin = [], None, None, None
    for p in paths:
        with rasterio.open(p) as src:
            geoms.append(box(*src.bounds))
            crs, res = src.crs, src.res[0]
            origin = (src.transform.c, src.transform.f)
    return gpd.GeoDataFrame({"path": paths}, geometry=geoms, crs=crs), res, origin


def build_city(city, csduid, tiles, res, origin):
    out = os.path.join(CITYDIR, "%s.tif" % csduid)
    if os.path.exists(out):
        print("   have it")
        return

    hit = tiles[tiles.intersects(city)]
    if hit.empty:
        print("   no tiles cover this city")
        return

    # output grid: city bounds snapped to the source pixel grid
    ox, oy = origin
    xmin, ymin, xmax, ymax = city.bounds
    xmin = ox + math.floor((xmin - ox) / res) * res
    ymax = oy - math.floor((oy - ymax) / res) * res
    width = int(math.ceil((xmax - xmin) / res))
    height = int(math.ceil((ymax - ymin) / res))
    transform = from_origin(xmin, ymax, res, res)

    profile = dict(driver="GTiff", dtype="uint8", count=1, nodata=0,
                   width=width, height=height, transform=transform,
                   crs=tiles.crs, compress="deflate", zlevel=9,
                   tiled=True, blockxsize=512, blockysize=512, nbits=1)

    srcs = [rasterio.open(p) for p in hit["path"]]
    try:
        part = out + ".part"
        with rasterio.open(part, "w", **profile) as dst:
            for row in range(0, height, BLOCK):
                h = min(BLOCK, height - row)
                for col in range(0, width, BLOCK):
                    w = min(BLOCK, width - col)
                    win = Window(col, row, w, h)
                    wt = dst.window_transform(win)
                    bounds = rasterio.windows.bounds(win, transform)

                    canopy = np.zeros((h, w), "uint8")
                    for src in srcs:
                        if not box(*bounds).intersects(box(*src.bounds)):
                            continue
                        chm = src.read(1, window=from_bounds(*bounds, src.transform),
                                       out_shape=(h, w), boundless=True, fill_value=0)
                        canopy |= (chm >= CANOPY_M).astype("uint8")

                    if canopy.any():
                        inside = geometry_mask([city], out_shape=(h, w),
                                               transform=wt, invert=True)
                        canopy *= inside
                    dst.write(canopy, 1, window=win)
    finally:
        for src in srcs:
            src.close()

    os.replace(part, out)
    print("   %.2f MB" % (os.path.getsize(out) / 1024**2))


def main():
    clear_partials()
    paths = download_tiles()
    if not paths:
        raise SystemExit("No tiles on disk.")

    tiles, res, origin = tile_index(paths)
    csds = gpd.read_file(CSDS).to_crs(tiles.crs)
    os.makedirs(CITYDIR, exist_ok=True)

    for i, row in csds.reset_index().iterrows():
        print("[%d/%d] %s" % (i + 1, len(csds), row["CSDNAME"]))
        build_city(row.geometry, row["CSDUID"], tiles, res, origin)

    files = os.listdir(CITYDIR)
    total = sum(os.path.getsize(os.path.join(CITYDIR, f)) for f in files) / 1024**2
    print("done: %d cities, %.0f MB in outputs/cities" % (len(files), total))


if __name__ == "__main__":
    main()