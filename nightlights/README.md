## NASA Earth at Night: Annual Nightlights Extractor

A lightweight Python tool to process, resample, and convert NASA's high-resolution global Earth at Night dataset into clean, normalized 2D NumPy float arrays (.npy) spanning from 2012 to 2023.

Instead of handling massive 4K frames in memory, this tool streams the video frame-by-frame, downsamples it to a manageable equirectangular grid, normalizes radiance values between 0.0 and 1.0, and saves each year instantly to disk.

## Features

- Direct NASA SVS Source: Ingests the official high-resolution 4K nightlights MP4 video.
- On-The-Fly Resampling: Downsamples frames (defaulting to a clean 1440x720 spatial grid) using area interpolation to maintain clarity while avoiding memory crashes.
- Low Memory Footprint: Processes and saves each annual frame streaming-style using numpy and OpenCV.
- Normalized Data: Converts RGB frames into single-channel grayscale radiance matrices scaled to float32 values ([0.0, 1.0]).

## Project Structure

```text
├── nightlights_extractor.py     # Main script to process the video and export annual .npy arrays
├── requirements.txt             # Project dependencies
└── nightlights_frames/          # Output directory generated upon extraction
```

## Source Data

Dataset Video URL: https://svs.gsfc.nasa.gov/vis/a000000/a005200/a005276/nightlights_flat_series_stills_only_lights_2160p3_h265.mp4

Temporal Range: Annual frames spanning from 2012 to 2023 (12 frames total).

## Install and run

```bash
pip install -r requirements.txt
python nightlights_extractor.py nightlights_flat_series_stills_only_lights_2160p3_h265.mp4
```

The video (path or URL readable by OpenCV) is the positional argument; download it from the URL above. Options:

| Option | Default | Meaning |
|---|---|---|
| `--output_dir` | `./nightlights_frames` | folder for the `.npy` files |
| `--target_width` | `1440` | grid width |
| `--target_height` | `720` | grid height |
| `--start_year` | `2012` | year of the first frame |

Output: `nightlights_<YYYY>.npy` (float32, 0.0-1.0), one per frame; the script stops after 2023.

> AI assistance: Google Gemini and Anthropic Claude helped with research, data analysis, coding and debugging, and writing for the night lights extractor. See [AI assistance](../README.md#ai-assistance).
