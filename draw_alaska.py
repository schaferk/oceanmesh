#!/usr/bin/env python3

import time
import oceanmesh as om
import zipfile
import requests
import os

start_time = time.perf_counter()  # Start timing

print(om.__version__)

# Alaska region in WGS84 coordinates (lon/lat)
bbox_wgs84 = (-138.0, -129.0, 53.5, 57.0)  # xmin, xmax, ymin, ymax

# Create region in WGS84
crs_wgs84 = 4326
target_epsg = 3338

region_wgs84 = om.Region(extent=bbox_wgs84, crs=4326)
region_proj = region_wgs84.transform_to(target_epsg)
print("Projected bbox (Albers):", region_proj.bbox)

# Alaska Albers Equal Area (recommended native projection for Alaska)

print("WGS84 Region bbox:", region_wgs84.bbox)

# Transform region to Alaska Albers for correct meshing and plotting
# Ensure bbox order is correct after projection
xmin, ymin, xmax, ymax = region_proj.bbox
xmin, xmax = min(xmin, xmax), max(xmin, xmax)
ymin, ymax = min(ymin, ymax), max(ymin, ymax)
region_proj.bbox = (xmin, ymin, xmax, ymax)
print("Projected bbox (Albers):", region_proj.bbox)

# Download and extract GSHHS data if needed
url = "http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.7.zip"
filename = url.split("/")[-1]
if not os.path.exists(filename):
    with open(filename, "wb") as f:
        r = requests.get(url)
        f.write(r.content)
else:
    print(f"{filename} already exists, skipping download.")

extract_dir = "gshhg-shp-2.3.7"
if not os.path.exists(extract_dir):
    with zipfile.ZipFile(filename, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
else:
    print(f"{extract_dir} already exists, skipping extraction.")

# Full path to GSHHS shapefile
fname = "gshhg-shp-2.3.7/GSHHS_shp/f/GSHHS_f_L1.shp"

# Adjust minimum edge length to match projection units (meters for EPSG:3338)
min_edge_length = 1000  # 1 km minimum edge length (can adjust for detail)

# Initialize Shoreline object using projected bbox and Alaska Albers CRS
shoreline = om.Shoreline(
    fname, region_proj.bbox, min_edge_length, crs=target_epsg
)

# Plot in projected units (meters)
shoreline.plot(
    xlabel="Easting (meters, Alaska Albers)",
    ylabel="Northing (meters, Alaska Albers)",
    title="Shoreline boundaries - Southeast Alaska (EPSG:3338)"
)

# Create signed distance function for meshing
sdf = om.signed_distance_function(shoreline)

end_time = time.perf_counter()  # End timing

print(f"Script execution time: {end_time - start_time:.2f} seconds")

