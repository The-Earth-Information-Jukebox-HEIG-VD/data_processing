# data_processing

Data processing for **The Earth Information Jukebox** (NASA Space Apps Challenge 2026, team HEIG-VD).

## Contents
| Folder | What it is |
|---|---|
| [`precipitation/2024/`](precipitation/2024/) | NASA GPM IMERG daily precipitation 2024, whole globe, every pixel. See [`precipitation/2024/README.md`](precipitation/2024/README.md). |
| [`common_grid/`](common_grid/) | one shared map grid for all datasets: put any NASA map (flat, Mercator, polar, Robinson…) on the same 0.25° grid and get comparable numbers for the music. See [`common_grid/README.md`](common_grid/README.md). |

## Quick start
```
pip install numpy pyproj pillow matplotlib scipy
```
```python
import sys; sys.path.insert(0, "common_grid")
from common_grid import *
```
