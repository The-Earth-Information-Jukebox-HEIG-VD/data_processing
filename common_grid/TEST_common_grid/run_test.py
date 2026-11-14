"""
Real-data test of the common grid: three NASA maps of the same day, in three
different projections, put on ONE grid.  Run after download_test_maps.py:
    python3 run_test.py
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                  # common_grid.py is in the project folder
import common_grid as cg

info = json.load(open(HERE / "maps" / "maps.json"))

def load(name):
    """Image as RGBA array + where there is data (alpha > 0)."""
    a = np.array(Image.open(HERE / info[name]["file"]).convert("RGBA"))
    return a, a[..., 3] > 0

def grid(name, values):
    m = info[name]
    return cg.from_crs(values, m["crs"], m["bbox"])

# ---- put everything on the common grid ----------------------------------
G = {}
for name in info:
    rgba, has = load(name)
    G[name] = grid(name, has.astype(float))           # fraction of each cell with data/feature
temp_rgb = np.dstack([np.nan_to_num(grid("temperature_flat", load("temperature_flat")[0][..., k].astype(float)))
                      for k in range(3)])

# ---- PROOF 1: coastlines from three projections land on the same cells ----
def near(a, b, cells=1):
    """Share of cells of line a that have line b within `cells` cells."""
    A, B = np.nan_to_num(a) > 0, np.nan_to_num(b) > 0
    Bd = B.copy()
    for dy in range(-cells, cells + 1):
        for dx in range(-cells, cells + 1):
            Bd |= np.roll(np.roll(B, dy, 0), dx, 1)
    return (A & Bd).sum() / max(A.sum(), 1)

lines = []
mid = np.abs(cg.LAT2D) < 80
polar_zone = np.isfinite(G["coast_polar"]) & (cg.LAT2D > 50)
lines.append(("Coastlines  Mercator vs flat (80S-80N)",
              near(G["coast_mercator"] * mid, G["coast_flat"])))
lines.append(("Coastlines  polar vs flat (north of 50N)",
              near(np.where(polar_zone, G["coast_polar"], 0), G["coast_flat"])))

# ---- PROOF 2: the SAME data in two projections gives the same cells -------
def agree(a, b, zone):
    A, B = np.nan_to_num(a) > 0, np.nan_to_num(b) > 0
    z = zone & np.isfinite(a) & np.isfinite(b)
    return (A & B & z).sum() / max(((A | B) & z).sum(), 1), (A == B)[z].mean()

for label, a, b, zone in [
        ("Precipitation  Mercator vs flat", G["precipitation_mercator"], G["precipitation_flat"], np.abs(cg.LAT2D) < 80),
        ("Fires  polar vs flat (north of 50N)", G["fires_polar"], G["fires_flat"], cg.LAT2D > 50)]:
    iou, same = agree(a, b, zone)
    lines.append((label, same))

# ---- PROOF 3: the numbers the music team would use ------------------------
# Fires are drawn as dots of a FIXED size in screen pixels (~22 px), so their
# area in km2 depends on the image resolution, not on the fire.  We therefore
# count fire spots and compare SHARES (what the sound uses after normalising).
from scipy import ndimage
from pyproj import Transformer

def fire_spots(name):
    m = info[name]
    a = load(name)[1]
    lab, k = ndimage.label(a)
    cy, cx = np.array(ndimage.center_of_mass(a, lab, range(1, k + 1))).T
    h, w = a.shape
    xmin, ymin, xmax, ymax = m["bbox"]
    x = xmin + (cx + .5) * (xmax - xmin) / w
    y = ymax - (cy + .5) * (ymax - ymin) / h
    lon, lat = Transformer.from_crs(m["crs"], "EPSG:4326", always_xy=True).transform(x, y)
    return np.asarray(lon), np.asarray(lat)

nums = []
for name, label in [("fires_polar", "POLAR"), ("fires_flat", "FLAT ")]:
    lon, lat = fire_spots(name)
    n50 = (lat > 50).sum()
    nums.append((f"Fires north of 50N  share in Siberia/Russia [%]  {label}", 100 * ((lat > 50) & (lon > 30)).sum() / n50))
    nums.append((f"Fires north of 50N  share in Canada/Alaska  [%]  {label}", 100 * ((lat > 50) & (lon < -50)).sum() / n50))
    nums.append((f"Fires north of 50N  share north of 60N     [%]  {label}", 100 * (lat > 60).sum() / n50))
nums += [
    ("Rain/snow cover 60S-60N [%]  MERCATOR", 100 * cg.region_fraction(G['precipitation_mercator'], (-180, 180, -60, 60))),
    ("Rain/snow cover 60S-60N [%]  FLAT    ", 100 * cg.region_fraction(G['precipitation_flat'], (-180, 180, -60, 60))),
    ("Rain/snow cover Europe  [%]  MERCATOR", 100 * cg.region_fraction(G['precipitation_mercator'], "europe")),
    ("Rain/snow cover Europe  [%]  FLAT    ", 100 * cg.region_fraction(G['precipitation_flat'], "europe")),
]

report = ["REAL-DATA TEST OF THE COMMON GRID  (NASA GIBS, " + info["temperature_flat"]["time"] + ")", ""]
report += [f"{k:55s} {v * 100:5.1f}% match" for k, v in lines]
report += [""] + [f"{k:55s} {v:8.1f}" for k, v in nums]
print("\n".join(report))
(HERE / "test_report.txt").write_text("\n".join(report))

# ---- the overlay: temperature (flat) + rain (Mercator) + fires (polar) ----
img = temp_rgb.copy() * 0.55                                # dimmed temperature colours
img[np.isnan(G["temperature_flat"]) | (np.nan_to_num(G["temperature_flat"]) == 0)] = (25, 25, 30)
rain = np.nan_to_num(G["precipitation_mercator"]) > 0.3
img[rain] = img[rain] * 0.3 + np.array([170, 210, 255]) * 0.7
coast = np.nan_to_num(G["coast_flat"]) > 0
img[coast] = (230, 230, 230)
fire = np.nan_to_num(G["fires_polar"]) > 0
img[fire] = (255, 40, 0)
Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(HERE / "overlay_one_grid.png")

# coastline check image: flat = white, Mercator = cyan, polar = magenta
chk = np.zeros(cg.SHAPE + (3,), np.uint8)
chk[np.nan_to_num(G["coast_flat"]) > 0] += np.array([90, 90, 90], np.uint8)
chk[np.nan_to_num(G["coast_mercator"]) > 0] += np.array([0, 140, 140], np.uint8)
chk[np.nan_to_num(G["coast_polar"]) > 0] += np.array([140, 0, 140], np.uint8)
Image.fromarray(chk).save(HERE / "coastlines_three_projections.png")

# panel: the three inputs + the overlay
thumbs = []
for name in ["temperature_flat", "precipitation_mercator", "fires_polar"]:
    a = Image.open(HERE / info[name]["file"]).convert("RGBA")
    bg = Image.new("RGBA", a.size, (25, 25, 30, 255)); bg.alpha_composite(a)
    if name != "temperature_flat":
        c = Image.open(HERE / info["coast_" + name.split("_")[1]]["file"]).convert("RGBA")
        bg.alpha_composite(c)
    thumbs.append(bg.convert("RGB").resize((600, int(600 * a.height / a.width))))
H = max(t.height for t in thumbs)
panel = Image.new("RGB", (1830, H + 30 + 900), (255, 255, 255))
for i, t in enumerate(thumbs):
    panel.paste(t, (i * 615, 0))
panel.paste(Image.open(HERE / "overlay_one_grid.png").resize((1800, 900)), (0, H + 30))
panel.save(HERE / "real_data_test_panel.png")
print("Saved: overlay_one_grid.png, coastlines_three_projections.png, real_data_test_panel.png, test_report.txt")
