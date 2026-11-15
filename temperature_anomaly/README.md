# NASA GISTEMP NetCDF to NumPy Extractor

A lightweight Python tool to download, parse, and convert NASA's official GISTEMPv4 gridded dataset into clean, scientific-grade, Celsius-valued 2D NumPy arrays (`.npy`). 

Instead of relying on video rasterization or approximated color-matching, this tool extracts precision scientific data from NASA's official NetCDF source files, mapping monthly global surface air temperature anomalies ($2^\circ \times 2^\circ$ spatial grid) from 1880 to 2025.

---

## Features

* **Official Scientific Data:** Downloads and parses NASA's official `gistemp1200_GHCNv4_ERSSTv5.nc.gz` dataset.
* **Low Memory Footprint:** Streams data month-by-month, writing individual `.npy` files directly to disk to prevent Out-Of-Memory (OOM) crashes.
* **Clean Data Handling:** Automatically converts missing values and regions without data into standard NumPy `NaN` values.

---

## Project Structure

```text
├── netcdf_to_numpy.py       # Main script to download and extract NetCDF data into .npy matrices
├── requirements.txt         # Project dependencies
````

---

## Install and run

```bash
pip install -r requirements.txt
python netcdf_to_numpy.py
```

The script takes no arguments. It downloads `gistemp1200_GHCNv4_ERSSTv5.nc.gz` as `gistemp_native.nc.gz` in the current folder (skipped if already present), then writes `./netcdf_temperature_frames/temperature_anomaly_YYYY_MM.npy` (float32, degrees C, NaN where there is no data), from 1880-01 up to 2025-12. Note that `requirements.txt` also lists `matplotlib` and `cmcrameri`, which the script does not use.

## Relation to the published data

The script outputs the native 2 degree grid, **90 x 180, row 0 = South**. The published files in `datasets/data/temperature_anomaly_1880_2025` are **720 x 1440 (0.25 degree), row 0 = North**, float16. The regridding step (copying each 2 degree value onto 8 x 8 pixels and flipping the rows) is **not in this repository**.
