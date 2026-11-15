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

Scripts here cover temperature anomaly, night lights and precipitation (the source of the rain and snow folders), plus the shared grid. The other folders of the `datasets` repository (CO2, fires, lightning, sea ice, vegetation NDVI, carbon monoxide, chlorophyll, rain belt) were committed there directly; their processing scripts are not in this repository.

## Quick start
```
pip install numpy pyproj pillow matplotlib scipy
```
This covers `common_grid/`. The other folders have their own `requirements.txt` (`nightlights/`: opencv-python, tqdm; `temperature_anomaly/`: xarray, netcdf4, cmcrameri, ...): run `pip install -r <folder>/requirements.txt` there.
```python
import sys; sys.path.insert(0, "common_grid")
from common_grid import *
```

## AI assistance

This data processing work was developed with the help of AI assistants, Google Gemini and Anthropic Claude. In this repository they were used for:

- **Research and information gathering:** NASA data formats and access (GISTEMP NetCDF, GPM IMERG through NASA GIBS, SVS 5276 Earth at Night) and map projections.
- **Data analysis and interpretation:** regridding every source onto the common 0.25° grid and checking the extracted values against the originals.
- **Coding, debugging and troubleshooting:** the extraction scripts and the `common_grid` helpers.
- **Writing, editing and translating:** the READMEs in this repository.

The team checked what the AI suggested and is responsible for the content of this repository. The data values come from NASA sources; the AI helped write and check the processing but did not generate any values.
