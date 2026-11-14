import os
import urllib.request
import xarray as np_xr  # or just xarray
import numpy as np
from tqdm import tqdm


def main():
    # Official NASA GISTEMPv4 gridded NetCDF URL
    nc_url = "https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz"
    nc_filename = "gistemp_native.nc.gz"

    # 1. Download the file if it doesn't exist locally
    if not os.path.exists(nc_filename) and not os.path.exists("gistemp_native.nc"):
        print(f"Downloading official GISTEMP netCDF data from NASA...")
        urllib.request.urlretrieve(nc_url, nc_filename)
        print("Download complete.")

    # 2. Open the dataset using xarray (handles .gz compression automatically)
    filename_to_open = (
        nc_filename if os.path.exists(nc_filename) else "gistemp_native.nc"
    )
    print(f"Opening dataset: {filename_to_open}...")

    import xarray as xr

    ds = xr.open_dataset(filename_to_open)

    # GISTEMP NetCDF typically has coordinates: 'time', 'lat', 'lon' and variable 'tempanomaly'
    print(ds)

    output_dir = "./netcdf_temperature_frames"
    os.makedirs(output_dir, exist_ok=True)

    # Extract time axis and temperature anomalies
    times = ds["time"].values
    temperatures = ds["tempanomaly"]  # Shape: (time, lat, lon)

    print(f"\nProcessing {len(times)} monthly time steps...")

    # 3. Loop through each month and export as a clean numpy array
    for i, t in enumerate(tqdm(times, desc="Exporting NetCDF Months")):
        # Convert numpy datetime64 to Year and Month
        dt = np.datetime_as_string(t, unit="M")  # returns 'YYYY-MM'
        year, month = dt.split("-")

        # Stop if we go beyond December 2025 (if the file includes newer data)
        if int(year) > 2025:
            break

        # Extract 2D grid for this specific month (Lat x Lon)
        # xarray automatically handles masked arrays and converts missing values to NaN
        temp_2d = temperatures.isel(time=i).values.astype(np.float32)

        # Save as individual .npy file
        output_filename = f"temperature_anomaly_{year}_{month}.npy"
        output_path = os.path.join(output_dir, output_filename)
        np.save(output_path, temp_2d)

    print(
        f"\nSuccess! All native NetCDF matrices saved as Celsius float32 arrays in '{output_dir}'."
    )


if __name__ == "__main__":
    main()
