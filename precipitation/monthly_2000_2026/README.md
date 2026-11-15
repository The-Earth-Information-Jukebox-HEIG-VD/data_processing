# Monthly precipitation 2000 – 2026, every pixel

Average precipitation (rain + snow) of every month, for the **whole globe**, from **June 2000 to November 2026**.
Source: NASA GPM IMERG daily precipitation rate (NASA GIBS layer `IMERG_Precipitation_Rate`), averaged per month.
All values are **real values** in their own units (not scaled). Snow is included as melted water.

**One file per year:** `precipitation_monthly_YYYY.npz` (about 15 MB each, 27 files, 387 MB in total).

## The map
Each month is **one map of the whole globe** (all countries and oceans, pole to pole, all the way around),
made of **720 × 1440 pixels**: 1440 × 0.25° = 360° around the Earth, 720 × 0.25° = 180° from pole to pole.
Each pixel is a small square of **0.25° × 0.25°** (about 28 × 28 km at the equator, 19 × 28 km in Switzerland).
This is the team's common grid: the same `[row, column]` is the same place in every dataset.

| Array | Shape | Unit | Meaning |
|---|---|---|---|
| `months` | 12 | text | `"2024-01"` … `"2024-12"` |
| `precip_mmh` | 12 × 720 × 1440 | mm/h | average precipitation rate of the month, every pixel |
| `snow_days` | 12 × 720 × 1440 | days | on how many days of the month it snowed there |
| `n_days` | 12 | days | days with data in that month |
| `lat` | 720 | degrees | latitude of the centre of each row (89.875 … −89.875) |
| `lon` | 1440 | degrees | longitude of the centre of each column (−179.875 … 179.875) |
| `cell_area_km2` | 720 × 1440 | km² | true area of each pixel (for averages) |

**How the map is organised:** `precip_mmh[month, row, column]`
* row 0 = far north (90°N), row 719 = far south (90°S)
* column 0 = 180°W, column 720 = 0° (Greenwich), column 1439 = 180°E
* any place: `row = int((90 - lat) / 0.25)`, `column = int((lon + 180) / 0.25)`
  (Lausanne, 46.5°N 6.6°E → row 174, column 746)

```python
import numpy as np
d = np.load("precipitation_monthly_2024.npz")
p = d["precip_mmh"]          # load ONCE into a variable
p[6]                         # the whole globe, July 2024 (720 x 1440)
p[:, 174, 746]               # Lausanne, the 12 months of 2024

# all years, one place
import glob
lausanne = np.concatenate([np.load(f)["precip_mmh"][:, 174, 746]
                           for f in sorted(glob.glob("precipitation_monthly_*.npz"))])   # 318 months
```

## Good to know
* **Monthly average rate** in mm per hour. Monthly total in mm = `precip_mmh × 24 × days in the month`.
  Example: 0.12 mm/h in July ≈ 89 mm in the month.
* **First and last year are partial:** 2000 starts in June; 2026 ends in November, and November 2026 has only
  13 days (1–13 Nov). `n_days` shows how many days each month uses.
* **A few days are missing** in NASA's archive (e.g. 23–29 Oct 2025): those months are averaged over the days that exist.
* **Below 0.1 mm/h on a single day counts as 0** (NASA does not show smaller amounts), so very dry places can be slightly underestimated.
* **Pixels are not all the same size.** Near the poles they are small. For an average over a region,
  weight by `cell_area_km2`: `(values * area).sum() / area.sum()`.
* Check: the global average is about 2.6 mm per day in every year.

> AI assistance: Google Gemini and Anthropic Claude helped with research, data analysis, coding and debugging, and writing for the monthly precipitation extraction. See [AI assistance](../../README.md#ai-assistance).
