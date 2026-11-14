"""
common_grid.py  -  one shared map grid for the whole Earth Jukebox team
=========================================================================

Why this file exists
--------------------
Every dataset comes as a different picture:
    IMERG rain      3600 x 1800 px  (0.1 deg per pixel)
    ISS lightning   4096 x 2048 px  (~0.088 deg per pixel)
    VIIRS fires     2048 x 1024 px  (~0.176 deg per pixel)
    AIRS temp       1440 x  720 px  (0.25 deg)  or a Europe box only

To show everything on ONE globe (or one flat map) and to compare places
cell by cell, we put every dataset on the SAME grid first.

The common grid
---------------
    * regular latitude / longitude grid (EPSG:4326, "plate carree")
    * 0.25 deg cells  ->  1440 x 720 cells  (change RES if you want)
    * row 0 = north (90N), column 0 = 180W   (same as all NASA flat maps)

Why lat/lon and not an equal-area projection?  Globe libraries (three.js,
Cesium, globe.gl, matplotlib/cartopy) wrap exactly this kind of 2:1 image
onto the sphere, so the grid IS the globe texture.  The fact that cells
near the poles are smaller is handled by AREA: pyproj gives the true area
of every cell on the WGS84 ellipsoid, and every statistic here is
weighted by it.  So the maps are display-ready and the numbers are
equal-area correct.

Quick start
-----------
    from common_grid import *
    grid = to_grid(my_values)                    # any flat global frame -> 720 x 1440
    grid = to_grid(eu_values, extent=(-10, 30, 35, 60))   # a regional box
    region_mean(grid, "europe")                  # area-weighted average
    region_fraction(grid > 0, "north")           # % of area where something happens
    save_layer("rain", "2026-11-04T12", grid)    # data/common/rain_2026-11-04T12.npz
    save_texture(grid, "rain.png", cmap="Blues", vmin=0, vmax=10)   # globe texture
"""

from pathlib import Path

import numpy as np
from pyproj import Geod

# ----------------------------------------------------------------------------
# 1. The grid
# ----------------------------------------------------------------------------
RES = 0.25                                   # degrees per cell
NY, NX = int(round(180 / RES)), int(round(360 / RES))   # 720 rows, 1440 columns
SHAPE = (NY, NX)

LAT = 90 - (np.arange(NY) + 0.5) * RES       # cell centres, north -> south
LON = -180 + (np.arange(NX) + 0.5) * RES     # cell centres, west -> east
LON2D, LAT2D = np.meshgrid(LON, LAT)

_GEOD = Geod(ellps="WGS84")


def _row_areas_km2(lat_edges, dlon):
    """True ellipsoid area (km2) of one cell in each latitude band."""
    areas = []
    for top, bottom in zip(lat_edges[:-1], lat_edges[1:]):
        a, _ = _GEOD.polygon_area_perimeter([0, dlon, dlon, 0], [bottom, bottom, top, top])
        areas.append(abs(a) / 1e6)
    return np.array(areas)


# area of every cell, km2 (same for all cells in a row)
CELL_AREA = np.repeat(_row_areas_km2(90 - np.arange(NY + 1) * RES, RES)[:, None], NX, axis=1)

# ----------------------------------------------------------------------------
# 2. Shared regions  (lon_min, lon_max, lat_min, lat_max)
#    Everyone uses THESE boxes, so our numbers are comparable.
# ----------------------------------------------------------------------------
REGIONS = {
    "global":        (-180, 180, -90, 90),
    "north":         (-180, 180, 0, 90),
    "south":         (-180, 180, -90, 0),
    "tropics":       (-180, 180, -23.5, 23.5),
    "arctic":        (-180, 180, 66.5, 90),
    "europe":        (-10, 30, 35, 60),
    "switzerland":   (5.9, 10.5, 45.8, 47.8),
    "americas":      (-170, -30, -60, 75),
    "africa_europe": (-30, 60, -40, 75),
    "asia_oceania":  (60, 180, -50, 75),
}


def region_mask(region):
    """Boolean 720 x 1440 mask for a region name or a (lon0, lon1, lat0, lat1) box."""
    lon0, lon1, lat0, lat1 = REGIONS[region] if isinstance(region, str) else region
    return (LON2D >= lon0) & (LON2D < lon1) & (LAT2D >= lat0) & (LAT2D < lat1)


# ----------------------------------------------------------------------------
# 3. Put any flat frame on the common grid
# ----------------------------------------------------------------------------
_CACHE = {}


def _index_map(h, w, extent):
    """For a source image of size h x w covering `extent`, find for every
    source pixel the common-grid cell its centre falls in (cached)."""
    key = (h, w, tuple(extent))
    if key not in _CACHE:
        lon0, lon1, lat0, lat1 = extent
        lat = lat1 - (np.arange(h) + 0.5) * (lat1 - lat0) / h
        lon = lon0 + (np.arange(w) + 0.5) * (lon1 - lon0) / w
        r = np.clip(((90 - lat) / RES).astype(int), 0, NY - 1)
        c = np.clip(((lon + 180) / RES).astype(int), 0, NX - 1)
        idx = (r[:, None] * NX + c[None, :]).ravel()
        # source pixel area, so a big pixel counts more than a small one
        dlat = (lat1 - lat0) / h
        edges = lat1 - np.arange(h + 1) * dlat
        w_area = np.repeat(_row_areas_km2(edges, (lon1 - lon0) / w)[:, None], w, axis=1).ravel()
        _CACHE[key] = (idx, w_area, lat, lon)
    return _CACHE[key]


def to_grid(values, extent=(-180, 180, -90, 90), how="mean"):
    """Resample a flat (equirectangular) frame onto the common grid.

    values : 2-D array (h x w), numbers or booleans.  Use np.nan for "no data".
    extent : (lon_min, lon_max, lat_min, lat_max) the image covers.
             Default = whole Earth.  Europe box from GIBS = (-10, 30, 35, 60).
    how    : "mean" -> area-weighted average of source pixels in each cell
                       (for rates, temperature, or a boolean -> fraction 0..1)
             "max"  -> strongest source pixel in each cell (for hot spots)

    Returns a 720 x 1440 float array, NaN where there is no data.
    Finer images are averaged down; coarser images (e.g. AIRS 1 deg) are
    copied into every cell they cover (nearest neighbour), no smoothing.
    """
    v = np.asarray(values, dtype=float)
    h, w = v.shape
    lon0, lon1, lat0, lat1 = extent
    src_res = min((lat1 - lat0) / h, (lon1 - lon0) / w)
    out = np.full(NY * NX, np.nan)

    if src_res <= RES * 1.0001:                       # finer than grid -> aggregate
        idx, area, _, _ = _index_map(h, w, extent)
        flat = v.ravel()
        ok = ~np.isnan(flat)
        if how == "mean":
            s = np.bincount(idx[ok], weights=flat[ok] * area[ok], minlength=NY * NX)
            n = np.bincount(idx[ok], weights=area[ok], minlength=NY * NX)
            has = n > 0
            out[has] = s[has] / n[has]
        elif how == "max":
            np.fmax.at(out, idx[ok], flat[ok])
        else:
            raise ValueError("how must be 'mean' or 'max'")
    else:                                             # coarser than grid -> nearest
        inside = region_mask((lon0, lon1, lat0, lat1)).ravel()
        r = ((lat1 - LAT2D.ravel()[inside]) / (lat1 - lat0) * h).astype(int).clip(0, h - 1)
        c = ((LON2D.ravel()[inside] - lon0) / (lon1 - lon0) * w).astype(int).clip(0, w - 1)
        out[inside] = v[r, c]
    return out.reshape(NY, NX)


# ----------------------------------------------------------------------------
# 4. Numbers for the sound  (all area-weighted with true pyproj areas)
# ----------------------------------------------------------------------------
def region_mean(grid, region="global"):
    """Area-weighted mean of a common-grid layer inside a region (ignores NaN)."""
    m = region_mask(region) & ~np.isnan(grid)
    return float((grid[m] * CELL_AREA[m]).sum() / CELL_AREA[m].sum()) if m.any() else np.nan


def region_fraction(condition, region="global"):
    """Share of the region's area (0..1) where `condition` is True.
    `condition` can be a boolean grid, or a 0..1 fraction grid from to_grid."""
    c = np.nan_to_num(np.asarray(condition, dtype=float))
    m = region_mask(region)
    return float((c[m] * CELL_AREA[m]).sum() / CELL_AREA[m].sum())


def region_area_km2(condition, region="global"):
    """Area in km2 where `condition` is True (or the fraction-weighted area)."""
    c = np.nan_to_num(np.asarray(condition, dtype=float))
    m = region_mask(region)
    return float((c[m] * CELL_AREA[m]).sum())


def centroid_lon(grid, region="global"):
    """Where is the activity, west (-) or east (+)?  Area- and value-weighted
    mean longitude.  Handy for stereo panning."""
    g = np.nan_to_num(grid) * region_mask(region) * CELL_AREA
    return float((g * LON2D).sum() / g.sum()) if g.sum() > 0 else np.nan


# ----------------------------------------------------------------------------
# 5. Saving: one layer file per dataset + time, and globe textures
# ----------------------------------------------------------------------------
COMMON_DIR = Path("data/common")


def save_layer(dataset, time_label, grid, folder=COMMON_DIR):
    """Save a layer as data/common/<dataset>_<time>.npz (float16, small)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{dataset}_{time_label}.npz"
    np.savez_compressed(path, grid=grid.astype(np.float16), res=RES,
                        dataset=dataset, time=time_label)
    return path


def load_layer(path):
    return np.load(path)["grid"].astype(float)


def save_texture(grid, path, cmap="viridis", vmin=None, vmax=None, transparent_below=None):
    """Save a 1440 x 720 RGBA PNG that wraps directly onto a globe.
    NaN (and values below `transparent_below`) become transparent, so
    several layers can be stacked on the same globe."""
    import matplotlib
    from PIL import Image
    g = np.array(grid, dtype=float)
    vmin = np.nanmin(g) if vmin is None else vmin
    vmax = np.nanmax(g) if vmax is None else vmax
    rgba = matplotlib.colormaps[cmap](np.clip((g - vmin) / (vmax - vmin + 1e-12), 0, 1))
    clear = np.isnan(g)
    if transparent_below is not None:
        clear |= g < transparent_below
    rgba[clear, 3] = 0
    Image.fromarray((rgba * 255).astype(np.uint8)).save(path)
    return path


# ----------------------------------------------------------------------------
# 6. Optional: equal-area version (EPSG:6933, EASE-Grid 2.0) for people who
#    want km-based cells, e.g. counting events per 100 km x 100 km.
# ----------------------------------------------------------------------------
def to_ease_cells(mask_or_values, extent=(-180, 180, -90, 90), cell_km=100):
    """Return (x_index, y_index, total) for 100 km equal-area cells."""
    from pyproj import Transformer
    v = np.asarray(mask_or_values, dtype=float)
    h, w = v.shape
    _, _, lat, lon = _index_map(h, w, extent)
    rows, cols = np.nonzero(np.nan_to_num(v))
    t = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    x, y = t.transform(lon[cols], lat[rows])
    xb = np.floor(x / (cell_km * 1000)).astype(int)
    yb = np.floor(y / (cell_km * 1000)).astype(int)
    cells, inv = np.unique(np.stack([xb, yb]), axis=1, return_inverse=True)
    totals = np.bincount(inv.ravel(), weights=v[rows, cols])
    return cells[0], cells[1], totals


if __name__ == "__main__":
    print(f"Common grid: {NY} x {NX} cells of {RES} deg")
    print(f"Total area  : {CELL_AREA.sum():,.0f} km2  (Earth = 510,065,622 km2)")
    print(f"Cell area   : {CELL_AREA[NY // 2, 0]:.0f} km2 at the equator, "
          f"{CELL_AREA[int((90 - 46.5) / RES), 0]:.0f} km2 at Lausanne")


# ----------------------------------------------------------------------------
# 7. Curved world maps (Robinson, Mollweide, ...) -> common grid
#    The map is "unbent" with pyproj: every image pixel gets its true
#    longitude/latitude, then it is binned into the common grid.
# ----------------------------------------------------------------------------
PROJ_ASPECT = {}   # filled on demand: height/width of the full map in that projection


def map_box(proj="+proj=robin"):
    """Full x/y extent (metres) of a world map in a projection."""
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", proj + " +datum=WGS84", always_xy=True)
    xmax = t.transform(180, 0)[0]
    ymax = max(abs(t.transform(lon, 90)[1]) for lon in (0, 90, 180))
    return xmax, ymax


def from_projection(values, proj="+proj=robin", left=0, right=None, top=0, bottom=None, how="mean"):
    """Put a curved world map on the common grid.

    values : 2-D array of the image (numbers / booleans, np.nan = ignore)
    proj   : "+proj=robin" (Robinson), "+proj=moll" (Mollweide), "+proj=eqearth" ...
    left, right, top, bottom : pixel columns/rows where the map's outline
             touches the image edge (the far-left and far-right tips at the
             equator, the top and bottom pole lines). Leave bottom=None to
             compute it from the projection's shape.
    """
    from pyproj import Transformer
    v = np.asarray(values, dtype=float)
    h, w = v.shape
    right = w - 1 if right is None else right
    xmax, ymax = map_box(proj)
    if bottom is None:
        bottom = top + (right - left) * ymax / xmax
    cols = np.arange(w)
    rows = np.arange(h)
    x = (cols + 0.5 - left) / (right + 1 - left) * 2 * xmax - xmax
    y = ymax - (rows + 0.5 - top) / (bottom + 1 - top) * 2 * ymax
    X, Y = np.meshgrid(x, y)
    t = Transformer.from_crs(proj + " +datum=WGS84", "EPSG:4326", always_xy=True)
    lon, lat = t.transform(X.ravel(), Y.ravel())
    lon, lat = np.asarray(lon), np.asarray(lat)
    # round trip: pixels outside the map outline do not come back to the same x
    x2, _ = Transformer.from_crs("EPSG:4326", proj + " +datum=WGS84", always_xy=True).transform(lon, lat)
    flat = v.ravel()
    ok = (np.isfinite(lon) & np.isfinite(lat) & (np.abs(np.asarray(x2) - X.ravel()) < 1000)
          & (np.abs(lat) <= 90) & ~np.isnan(flat))
    r = np.clip(((90 - lat[ok]) / RES).astype(int), 0, NY - 1)
    c = np.clip(((lon[ok] + 180) / RES).astype(int), 0, NX - 1)
    idx = r * NX + c
    out = np.full(NY * NX, np.nan)
    if how == "mean":
        s = np.bincount(idx, weights=flat[ok], minlength=NY * NX)
        n = np.bincount(idx, minlength=NY * NX)
        out[n > 0] = s[n > 0] / n[n > 0]
    else:
        np.fmax.at(out, idx, flat[ok])
    return out.reshape(NY, NX)


# ----------------------------------------------------------------------------
# 8. Automatic: find the map outline and guess the projection from its shape
# ----------------------------------------------------------------------------
CANDIDATES = {"equirectangular": "+proj=eqc", "robinson": "+proj=robin",
              "mollweide": "+proj=moll", "equal_earth": "+proj=eqearth"}


def _bg_colours(rgb):
    """Colours that cover more than 5% of the image border."""
    rgb = np.asarray(rgb)[..., :3].astype(int)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    cols, counts = np.unique(border // 8, axis=0, return_counts=True)
    return cols[counts > 0.05 * len(border)] * 8 + 4


def _map_pixels(rgb, bg=None, tol=25):
    """True where a pixel is part of the map (not the plain background)."""
    rgb = np.asarray(rgb)[..., :3].astype(int)
    bg = _bg_colours(rgb) if bg is None else bg
    is_bg = np.zeros(rgb.shape[:2], bool)
    for c in bg:
        is_bg |= (np.abs(rgb - c).max(axis=2) < tol)
    return ~is_bg


def _bbox(m, frac=0.01):
    """Bounding box of the map, ignoring stray pixels (< 1% of a row/column)."""
    rows = np.nonzero(m.sum(axis=1) >= max(3, frac * m.shape[1]))[0]
    cols = np.nonzero(m.sum(axis=0) >= max(3, frac * m.shape[0]))[0]
    return rows.min(), rows.max(), cols.min(), cols.max()


def _outline_mask(shape, proj, left, right, top, bottom, step=4):
    """Which (subsampled) pixels fall inside the world outline."""
    from pyproj import Transformer
    h, w = shape
    xmax, ymax = map_box(proj)
    rows, cols = np.arange(0, h, step), np.arange(0, w, step)
    X, Y = np.meshgrid((cols + 0.5 - left) / (right + 1 - left) * 2 * xmax - xmax,
                       ymax - (rows + 0.5 - top) / (bottom + 1 - top) * 2 * ymax)
    inv = Transformer.from_crs(proj + " +datum=WGS84", "EPSG:4326", always_xy=True)
    fwd = Transformer.from_crs("EPSG:4326", proj + " +datum=WGS84", always_xy=True)
    lon, lat = inv.transform(X.ravel(), Y.ravel())
    x2, y2 = fwd.transform(lon, lat)
    ok = (np.isfinite(lon) & (np.abs(np.asarray(x2) - X.ravel()) < 1000)
          & (np.abs(np.asarray(y2) - Y.ravel()) < 1000) & (np.abs(Y.ravel()) <= ymax))
    return ok.reshape(len(rows), len(cols))


def detect_map(rgb, step=4):
    """Find left/right/top of the map and the best-matching projection.
    Returns dict(projection, proj, left, right, top, bottom, score)."""
    rgb = np.asarray(rgb)[..., :3].astype(int)
    off_r = off_c = 0
    bg = _bg_colours(rgb)

    def uniform(line):
        """A frame edge = one plain colour that is NOT the background around it
        (the corners of a curved map are plain too, but in the background colour)."""
        med = np.median(line, axis=0)
        new_colour = all(np.abs(med - c).max() > 25 for c in bg)
        return new_colour and (np.abs(line - med).max(axis=1) < 25).mean() > 0.9

    for _ in range(6):                       # peel off frames (screenshot border, black box...)
        r0, r1, c0, c1 = _bbox(_map_pixels(rgb, bg))
        framed = False
        for k in range(4):                   # allow a few soft (anti-aliased) edge pixels
            crop = rgb[r0 + k:r1 + 1 - k, c0 + k:c1 + 1 - k]
            if sum(uniform(sd) for sd in (crop[0], crop[-1], crop[:, 0], crop[:, -1])) >= 3:
                framed = True
                break
        if not framed:
            break                            # what is left touches the map itself
        rgb, off_r, off_c, bg = crop, off_r + r0 + k, off_c + c0 + k, _bg_colours(crop)
    for _ in range(3):                       # thin plain lines along an edge (e.g. a soft frame border)
        m = _map_pixels(rgb, bg)
        r0, r1, c0, c1 = _bbox(m)
        crop = rgb[r0:r1 + 1, c0:c1 + 1]
        pairs = [(crop[0], crop[3]), (crop[-1], crop[-4]), (crop[:, 0], crop[:, 3]), (crop[:, -1], crop[:, -4])]
        # keep only THIN lines: the same colour must not continue 3 px further inside
        extra = [np.median(a, axis=0) for a, b in pairs
                 if uniform(a) and np.abs(np.median(b, axis=0) - np.median(a, axis=0)).max() > 25]
        if not extra:
            break
        bg = np.vstack([bg] + extra)
    m = _map_pixels(rgb, bg)
    top, _, left, right = _bbox(m)
    sub = m[::step, ::step]
    best = None
    for name, proj in CANDIDATES.items():
        xmax, ymax = map_box(proj)
        bottom = top + (right - left) * ymax / xmax
        exp = _outline_mask(m.shape, proj, left, right, top, bottom, step)
        # pixels of the map that fall OUTSIDE the expected outline are bad,
        # and so is expected outline area with no map pixels at its edges
        outside = (sub & ~exp).sum() / max(sub.sum(), 1)
        ring = exp & ~np.roll(exp, 3, 1) | exp & ~np.roll(exp, -3, 1)   # left/right edges of outline
        edge_hit = sub[ring].mean() if ring.any() else 0
        score = edge_hit - 3 * outside
        if best is None or score > best["score"]:
            best = dict(projection=name, proj=proj, left=int(left + off_c), right=int(right + off_c),
                        top=int(top + off_r), bottom=float(bottom + off_r), score=float(score))
    return best


# ----------------------------------------------------------------------------
# 9. Maps with KNOWN projection and bounds (the clean way, e.g. NASA GIBS):
#    give the CRS and the bounding box, pyproj does the rest.
# ----------------------------------------------------------------------------
def _crs_index(h, w, crs, bbox):
    """For an image of h x w in `crs` covering `bbox`: which pixels are on Earth
    and which common-grid cell each one falls in.  Cached: every frame of a movie
    reuses it, so only the first frame is slow."""
    key = ("crs", h, w, crs, bbox)
    if key not in _CACHE:
        from pyproj import Transformer
        xmin, ymin, xmax, ymax = bbox
        x = xmin + (np.arange(w) + 0.5) * (xmax - xmin) / w
        y = ymax - (np.arange(h) + 0.5) * (ymax - ymin) / h
        X, Y = np.meshgrid(x, y)
        t = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        lon, lat = (np.asarray(a) for a in t.transform(X.ravel(), Y.ravel()))
        ok = np.isfinite(lon) & np.isfinite(lat) & (np.abs(lat) <= 90)
        r = np.clip(((90 - lat[ok]) / RES).astype(int), 0, NY - 1)
        c = np.clip(((lon[ok] + 180) / RES).astype(int), 0, NX - 1)
        _CACHE[key] = (np.nonzero(ok)[0], r * NX + c)
    return _CACHE[key]


def from_crs(values, crs, bbox, how="mean"):
    """Put a map with a known projection on the common grid.

    crs  : "EPSG:4326" (flat), "EPSG:3857" (Web Mercator), "EPSG:3413" (Arctic polar), ...
    bbox : (xmin, ymin, xmax, ymax) of the image in that CRS's units
           (degrees lon/lat for EPSG:4326, metres for the others).
    """
    v = np.asarray(values, dtype=float)
    h, w = v.shape
    pix, cell = _crs_index(h, w, crs, tuple(bbox))     # computed once per image size, then reused
    flat = v.ravel()[pix]
    ok = ~np.isnan(flat)
    flat, idx = flat[ok], cell[ok]
    ok = slice(None)
    out = np.full(NY * NX, np.nan)
    if how == "mean":
        s = np.bincount(idx, weights=flat[ok], minlength=NY * NX)
        n = np.bincount(idx, minlength=NY * NX)
        out[n > 0] = s[n > 0] / n[n > 0]
    else:
        np.fmax.at(out, idx, flat[ok])
    return out.reshape(NY, NX)
