# data_processing

Data processing for **The Earth Information Jukebox** (NASA Space Apps Challenge 2026, team HEIG-VD).

## Contents
| Folder | What it is |
|---|---|
| [`precipitation/2024/`](precipitation/2024/) | NASA GPM IMERG daily precipitation 2024, whole globe, every pixel. See [`precipitation/2024/README.md`](precipitation/2024/README.md). |
| [`precipitation/monthly_2000_2026/`](precipitation/monthly_2000_2026/) | NASA GPM IMERG monthly precipitation June 2000 – Nov 2026, whole globe, every pixel, one file per year. See [`README`](precipitation/monthly_2000_2026/README.md). |
| [`nightlights/`](nightlights/) | NASA SVS 5276 Earth at Night video to one yearly `nightlights_YYYY.npy` (2012-2023). See [`README`](nightlights/README.md). |
| [`temperature_anomaly/`](temperature_anomaly/) | NASA GISTEMP NetCDF to one monthly `temperature_anomaly_YYYY_MM.npy` (1880-2025). See [`README`](temperature_anomaly/README.md). |
| [`common_grid/`](common_grid/) | one shared map grid for all datasets: put any NASA map (flat, Mercator, polar, Robinson…) on the same 0.25° grid and get comparable numbers for the music. See [`common_grid/README.md`](common_grid/README.md). |

## Quick start
```
pip install numpy pyproj pillow matplotlib scipy
```
This covers `common_grid/`. The other folders have their own `requirements.txt` (`nightlights/`: opencv-python, tqdm; `temperature_anomaly/`: xarray, netcdf4, cmcrameri, ...): run `pip install -r <folder>/requirements.txt` there.
```python
import sys; sys.path.insert(0, "common_grid")
from common_grid import *
```
