#!/usr/bin/env python3
"""
Script to inspect a NetCDF file and ensure coverage for interpolation.

- Loads a NetCDF file with a (lat, lon) grid in EPSG:4326.
- Converts query points (EPSG:3338) → EPSG:4326 and checks coverage.
- Automatically expands DEM subset using ncks if needed.
- Saves diagnostic plots for coverage and NaN distributions.

Author: [Author]
Date: [Date]
"""

def wrap_longitudes(lon_array, mode='180'):
    """
    Wrap longitudes either to [-180, 180) or [0, 360).
    mode = '180'  → [-180, 180)
    mode = '360'  → [0, 360)
    """
    if mode == '180':
        return ((lon_array + 180) % 360) - 180
    elif mode == '360':
        return lon_array % 360
    else:
        raise ValueError("mode must be '180' or '360'")

import argparse
import netCDF4 as nc
import numpy as np
import os
import sys
import subprocess
import matplotlib.pyplot as plt
from pyproj import Transformer
from utils import read_points

help_epilog = '''
Example usage:
  hycom_compare.py -h
  hycom_compare.py --file ./datasets/alaska_bbox4.nc
  hycom_compare.py --file /path_to_hycom_file/hycom_file.nc
'''

parser = argparse.ArgumentParser(
    description="Inspect and expand NetCDF DEM coverage if needed.",
    epilog=help_epilog,
    formatter_class=argparse.RawDescriptionHelpFormatter
)

parser.add_argument(
    "-f", "--file",
    default="./datasets/alaska_bbox4.nc",
    help="Path to NetCDF file containing elevation data. (default: %(default)s)"
)

parser.add_argument(
    "-o", "--output",
    default="depth.dat-voro",
    help="Path to output file. (default: %(default)s)"
)

args = parser.parse_args()

output_file = args.output
nc_file = args.file
nc_basename = os.path.splitext(os.path.basename(nc_file))[0]

print('\n# Step 1: Load NetCDF Elevation Data')
ds = nc.Dataset(nc_file)
print("Variables:", ds.variables.keys())
print("Dimensions:", ds.dimensions.keys())

# --- Extract lat/lon and compute DEM bounds ---
lat = ds.variables['Latitude'][:]
lon = ds.variables['Longitude'][:]

lon_dmin, lon_dmax = lon.min(), lon.max()
lat_dmin, lat_dmax = lat.min(), lat.max()

print("\nDEM bounds (lon/lat):")
print(f"  lon: {lon_dmin:.4f} to {lon_dmax:.4f}")
print(f"  lat: {lat_dmin:.4f} to {lat_dmax:.4f}")

# Format coordinates with sensible precision and remove trailing zeros
lon_min_str = f"{lon_dmin:.2f}".rstrip('0').rstrip('.')
lon_max_str = f"{lon_dmax:.2f}".rstrip('0').rstrip('.')
lat_min_str = f"{lat_dmin:.2f}".rstrip('0').rstrip('.')
lat_max_str = f"{lat_dmax:.2f}".rstrip('0').rstrip('.')

print('\n# Step 2: Load Query Points (Projected EPSG:3338)')
projected_points = np.array(read_points('./points.dat'))
xv, yv = projected_points[:, 0], projected_points[:, 1]

print(f"Loaded {len(projected_points)} projected points.")
print(f"  X range: {xv.min():.2f} to {xv.max():.2f}")
print(f"  Y range: {yv.min():.2f} to {yv.max():.2f}")

print('\n# Step 3: Reproject Query Points EPSG:3338 → EPSG:4326')
transformer = Transformer.from_crs("EPSG:3338", "EPSG:4326", always_xy=True)
lon_query, lat_query = transformer.transform(xv, yv)

lon_qmin, lon_qmax = lon_query.min(), lon_query.max()
lat_qmin, lat_qmax = lat_query.min(), lat_query.max()

print("\nQuery bounds (lon/lat):")
print(f"  lon: {lon_qmin:.4f} to {lon_qmax:.4f}")
print(f"  lat: {lat_qmin:.4f} to {lat_qmax:.4f}")

# --- Compare coverage ---
outside = (
    lon_qmin < lon_dmin or lon_qmax > lon_dmax or
    lat_qmin < lat_dmin or lat_qmax > lat_dmax
)

if outside:
    print("\n⚠️  Query domain exceeds DEM coverage. Expanding DEM subset...")
    pad = 0.2  # degrees of safety padding

    lon_min_new = min(lon_dmin, lon_qmin) - pad
    lon_max_new = max(lon_dmax, lon_qmax) + pad
    lat_min_new = min(lat_dmin, lat_qmin) - pad
    lat_max_new = max(lat_dmax, lat_qmax) + pad

    lon_min_new = wrap_longitudes(lon_min_new, mode='180')
    lon_max_new = wrap_longitudes(lon_max_new, mode='180')

    print(f"Expanded DEM bounds:")
    print(f"  lon: {lon_min_new:.4f} to {lon_max_new:.4f}")
    print(f"  lat: {lat_min_new:.4f} to {lat_max_new:.4f}")

    lon_min_new = wrap_longitudes(lon_min_new, mode='360')
    lon_max_new = wrap_longitudes(lon_max_new, mode='360')

    print(f"Expanded DEM bounds:")
    print(f"  lon: {lon_min_new:.4f} to {lon_max_new:.4f}")
    print(f"  lat: {lat_min_new:.4f} to {lat_max_new:.4f}")

    #expanded_nc = f"{os.path.splitext(nc_file)[0]}_expanded.nc"

#    cmd = [
#        "ncks",
#        "-d", f"lon,{lon_min_new},{lon_max_new}",
#        "-d", f"lat,{lat_min_new},{lat_max_new}",
#        nc_file,
#        "-O", expanded_nc
#    ]
#    print("Running:", " ".join(cmd))
#    try:
#        subprocess.run(cmd, check=True)
#        print(f"✅ Expanded DEM written to {expanded_nc}")
#        nc_file = expanded_nc
#    except subprocess.CalledProcessError as e:
#        print(f"❌ ncks failed: {e}")
#        sys.exit(1)
else:
    print("✅ Query domain fully covered by DEM.")

print('\n# Step 4: Project DEM grid to EPSG:3338 (for visualization)')
transformer_to_proj = Transformer.from_crs("EPSG:4326", "EPSG:3338", always_xy=True)

# Reproject DEM lat/lon grid (sample or full, depending on size)
if lon.ndim == 2:
    xylon, xylat = transformer_to_proj.transform(lon, lat)
else:
    Lon, Lat = np.meshgrid(lon, lat)
    xylon, xylat = transformer_to_proj.transform(Lon, Lat)

# Construct coordinate range suffix
coord_suffix = f"{lon_min_str}-{lon_max_str}_{lat_min_str}-{lat_max_str}"

filename = f"source_vs_query_{nc_basename}_{coord_suffix}.png"

plt.figure(figsize=(8, 6))
plt.scatter(xylon, xylat, s=1, label='source DEM')
plt.scatter(xv, yv, s=1, label='query points', alpha=0.5)
plt.legend()
plt.xlabel("X (EPSG:3338)")
plt.ylabel("Y (EPSG:3338)")
plt.title("Source vs Query Coverage Check")
plt.tight_layout()
plt.savefig(filename, dpi=300)
plt.close()
print(f"Saved coverage diagnostic: {filename}")

# later continue with interpolation logic here...
sys.exit(0)

# Apply to your longitude coordinate column before UTM conversion:
#lon_checked = wrap_longitudes(lon_checked)
#coords_to_use[:, 1] = lon_checked


