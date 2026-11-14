"""
Download REAL NASA maps of the SAME DAY in THREE DIFFERENT PROJECTIONS (NASA GIBS).
Run in Terminal, inside the TEST_common_grid folder:
    python3 download_test_maps.py
"""
import json, os, urllib.request

DAY = "2024-07-15"          # fire season in the north; MOPITT still running
SIZE = 2048
P = 20037508.34             # Web Mercator half-width (m)
A = 4194304                 # GIBS Arctic polar half-width (m)
OUT = "maps"
os.makedirs(OUT, exist_ok=True)

FLAT  = ("epsg4326", "EPSG:4326", (-180, -90, 180, 90), (SIZE, SIZE // 2))
MERC  = ("epsg3857", "EPSG:3857", (-P, -P, P, P),       (SIZE, SIZE))
POLAR = ("epsg3413", "EPSG:3413", (-A, -A, A, A),       (SIZE, SIZE))

MAPS = {
    # the three main maps, each in a DIFFERENT projection
    "temperature_flat":      ("AIRS_L3_Surface_Air_Temperature_Daily_Day", FLAT,  DAY),
    "precipitation_mercator":("IMERG_Precipitation_Rate",                  MERC,  DAY),
    "fires_polar":           ("VIIRS_NOAA20_Thermal_Anomalies_375m_All",   POLAR, DAY),
    # carbon monoxide like the Earth Observatory page (MOPITT, monthly July 2024)
    "co_flat":               ("MOPITT_CO_Monthly_Total_Column_Day",        FLAT,  "2024-07-01"),
    # proof: the same data again, but flat, to compare cell by cell
    "precipitation_flat":    ("IMERG_Precipitation_Rate",                  FLAT,  DAY),
    "fires_flat":            ("VIIRS_NOAA20_Thermal_Anomalies_375m_All",   FLAT,  DAY),
    # coastlines in all three projections (must land on top of each other)
    "coast_flat":            ("Coastlines_15m", FLAT,  None),
    "coast_mercator":        ("Coastlines_15m", MERC,  None),
    "coast_polar":           ("Coastlines",     POLAR, None),
}

info = {}
for name, (layer, (ep, crs, bbox, (w, h)), time) in MAPS.items():
    b = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}" if crs == "EPSG:4326" else ",".join(map(str, bbox))
    url = (f"https://gibs.earthdata.nasa.gov/wms/{ep}/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap"
           f"&VERSION=1.3.0&LAYERS={layer}&CRS={crs}&BBOX={b}&WIDTH={w}&HEIGHT={h}"
           f"&FORMAT=image/png&TRANSPARENT=TRUE" + (f"&TIME={time}" if time else ""))
    path = os.path.join(OUT, name + ".png")
    print("downloading", name, "...")
    urllib.request.urlretrieve(url, path)
    info[name] = dict(layer=layer, crs=crs, bbox=bbox, time=time, file=path)

json.dump(info, open(os.path.join(OUT, "maps.json"), "w"), indent=2)
print("Done. Maps + maps.json are in", OUT, "  (source: NASA GIBS, https://gibs.earthdata.nasa.gov)")
