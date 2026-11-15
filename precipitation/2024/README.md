# Precipitation 2024

Daily precipitation (rain + snow) for the **whole globe**, all **366 days of 2024**.
Source: NASA GPM IMERG daily precipitation rate (NASA GIBS layer `IMERG_Precipitation_Rate`).
All values are **real values** in their own units (not scaled). Snow is included as melted water.

File: `precipitation_pixels_2024-01-01_2024-12-31.npz` (about 75 MB on disk, 0.8 GB in memory)

## The map

Each day is **one map of the whole globe** (all countries and oceans, pole to pole, all the way around),
made of **720 × 1440 pixels**: 1440 × 0.25° = 360° around the Earth, 720 × 0.25° = 180° from pole to pole.
Each pixel is a small square of **0.25° × 0.25°** (about 28 × 28 km at the equator, 19 × 28 km in Switzerland),
so Switzerland is about 144 pixels. Places smaller than one pixel share the value of that 28 km square.

| Array | Shape | Unit | Meaning |
|---|---|---|---|
| `dates` | 366 | text | `"2024-01-01"` … `"2024-12-31"` |
| `precip_mmh` | 366 × 720 × 1440 | mm/h | precipitation rate of the day, every pixel. **0 = nothing falls** |
| `is_snow` | 366 × 720 × 1440 | True/False | True where the precipitation is snow |
| `lat` | 720 | degrees | latitude of the centre of each row (89.875 … −89.875) |
| `lon` | 1440 | degrees | longitude of the centre of each column (−179.875 … 179.875) |
| `cell_area_km2` | 720 × 1440 | km² | true area of each pixel (for averages) |

**How the map is organised:** `precip_mmh[day, row, column]`
* row 0 = far north (90°N), row 719 = far south (90°S)
* column 0 = 180°W (Pacific), column 720 = 0° (Greenwich), column 1439 = 180°E
* any place: `row = int((90 - lat) / 0.25)`, `column = int((lon + 180) / 0.25)`
  (Lausanne, 46.5°N 6.6°E → row 174, column 746)

```python
import numpy as np
p = np.load("precipitation_pixels_2024-01-01_2024-12-31.npz")
precip = p["precip_mmh"]        # load ONCE into a variable (0.8 GB in memory, a few seconds)
dates  = p["dates"]

precip[0]                       # the whole globe on 1 January (720 x 1440)
precip[:, 174, 746]             # Lausanne, every day of the year (366 values)
i = list(dates).index("2024-07-15")
precip[i]                       # the whole globe on 15 July
```
Tip: write `precip = p["precip_mmh"]` once. Every `p["precip_mmh"]` unpacks the whole file again.

---

## Good to know
* **Daily average.** Each value is the average rate over that day, in mm per hour.
  Multiply by 24 for mm per day. A typical rainy day is 0.1–2 mm/h; 2 mm/h means 50 mm in a day (heavy).
* **Below 0.1 mm/h counts as 0.** NASA does not show smaller amounts.
* **Steps, not smooth values.** NASA stores 110 levels for rain and 110 for snow; we use the middle of each level.
  Neighbouring levels differ by about 6 %. The top level is "53 mm/h or more".
* **Most of the globe is dry** on any given day: about 15–20 % of pixels are wet.
* **Pixels are not all the same size.** Near the poles they are small. For an average over a region,
  weight by `cell_area_km2`: `(values * area).sum() / area.sum()`.
* **No missing days** in 2024.

> AI assistance: Google Gemini and Anthropic Claude helped with research, data analysis, coding and debugging, and writing for the 2024 daily precipitation extraction. See [AI assistance](../../README.md#ai-assistance).
