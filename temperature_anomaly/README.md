# NASA GISTEMP NetCDF to NumPy Extractor

A lightweight Python tool to download, parse, and convert NASA's official GISTEMPv4 gridded dataset into clean, scientific-grade, Celsius-valued 2D NumPy arrays (`.npy`). 

Instead of relying on video rasterization or approximated color-matching, this tool extracts precision scientific data from NASA's official NetCDF source files, mapping monthly global surface air temperature anomalies ($2^\circ \times 2^\circ$ spatial grid) from 1880 to 2025.

---

## Features

* **Official Scientific Data:** Downloads and parses NASA's official `gistemp1200_GHCNv4_ERSSTv5.nc.gz` dataset.
* **Low Memory Footprint:** Streams data month-by-month, writing individual `.npy` files directly to disk to prevent Out-Of-Memory (OOM) crashes.
* **Clean Data Handling:** Automatically converts missing values and regions without data into standard NumPy `NaN` values.
* **Verification Utilities:** Includes a built-in plotting script to quickly render and verify any monthly temperature grid using `matplotlib` and the scientific Vik colormap (`cmcrameri`).

---

## Project Structure

```text
├── netcdf_to_numpy.py       # Main script to download and extract NetCDF data into .npy matrices
├── requirements.txt         # Project dependencies
````
