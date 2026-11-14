# Common grid for the Earth Information Jukebox team

One shared map grid for all datasets, so that everything can be shown on one globe
and every dataset gives numbers the music team can compare.

## What is in here
| File | What it is |
|---|---|
| `common_grid.py` | the helper module (only needs `numpy`, `pyproj`, `pillow`; `matplotlib` for textures) |
| `TEST_common_grid/download_test_maps.py` | downloads 9 real NASA maps (15 July 2024) in 3 projections |
| `TEST_common_grid/run_test.py` | puts them on one grid and checks they agree |

Install once: `pip install numpy pyproj pillow matplotlib scipy`

## The grid
* Regular latitude/longitude grid, 0.25° cells, 1440 × 720 (row 0 = 90°N, column 0 = 180°W).
* Each cell has its **true area from pyproj** (WGS84), and all statistics are area-weighted. So the numbers are equal-area correct.
* The grid is also a **globe texture** (2:1), so every layer can be wrapped on one globe.

## How it works (no image is stretched)
For every pixel of your map:
1. find its position on the map (from the map's edges);
2. **pyproj** converts that position to latitude/longitude;
3. the pixel's value goes into the grid cell containing that point, and pixels in the same cell are averaged.

Nothing is smoothed or invented. Each cell only contains pixels that really fall inside it.
For a movie, the pixel→cell matching is computed on the first frame and reused,
so the next frames take about 0.05 s.

## Put your data on the grid, pick the function for your map
| Your map | Function |
|---|---|
| Flat 2:1 global map (most NASA SVS / EIC movies) | `to_grid(values)` |
| Flat regional box | `to_grid(values, extent=(lon0, lon1, lat0, lat1))` |
| Known projection + edges (NASA GIBS: EPSG:4326, 3857 Mercator, 3413 Arctic…) | `from_crs(values, "EPSG:3413", bbox)` |
| Curved world map / screenshot, edges unknown (Robinson, Mollweide, Equal Earth) | `d = detect_map(rgb)` then `from_projection(values, d["proj"], d["left"], d["right"], d["top"], d["bottom"])` |

Not supported: a rotating globe seen from space (half the Earth hidden). Use the flat version of the movie instead.

## One frame → numbers for the music
```python
from common_grid import *

rows = []
for date, frame in frames:                      # your loop
    mask = my_colour_to_value(frame)            # colours -> numbers / True-False, np.nan = no data
    g = to_grid(mask)                           # or from_crs(...)
    rows.append(dict(date=date,
                     north=region_fraction(g, "north"),
                     europe=region_fraction(g, "europe")))
    save_layer("mydataset", date, g)            # data/common/mydataset_<date>.npz  (for the globe)
```
Other numbers: `region_mean(g, region)`, `region_area_km2(g, region)`, `centroid_lon(g, region)` (for stereo pan).
Globe picture: `save_texture(g, "layer.png", cmap="Reds", vmin=0, vmax=1, transparent_below=0.01)`.

## Team rules
1. Use only the region names in `REGIONS` (add new ones there, so everyone has them).
2. Time labels: `YYYY-MM-DD` (daily) or `YYYY-MM-DDTHH` (hourly).
3. Hide labels, dates and colour bars (`np.nan`) before converting.
4. **Dot-type data (fires, lightning): use counts or shares, never the area in km².**
   NASA draws each fire/flash as a dot of a fixed size in pixels, so its area depends
   on the image resolution, not on the event (we measured 10× between two projections).
5. Check each new dataset once by looking at it on the grid (coastlines in the right place).

## Real-data test (run it yourself)
```
cd TEST_common_grid
python3 download_test_maps.py
python3 run_test.py
```
Our results (15 July 2024):

| Check | Result |
|---|---|
| Coastlines Mercator vs flat | 100% |
| Coastlines polar vs flat | 94.9% (the polar layer also draws lakes) |
| Same precipitation, Mercator vs flat | 98.3% of cells; rain cover 60°S–60°N 20.1% vs 20.1% |
| Same fires, polar vs flat | 98.4% of cells; Siberia share 66.7% vs 67.8%, north of 60°N 37.9% vs 37.9% |

Note: VIIRS "fires" are all hot spots, including agricultural and savanna burning.
That's why Africa is full of dots in July (southern dry season).
