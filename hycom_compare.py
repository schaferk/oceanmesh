#!/usr/bin/env python3

"""
Script to inspect a NetCDF file

- Loads a NetCDF file with a (lat, lon) grid in EPSG:4326.
- Prints variable and dimension information.
- Displays the shape and range of latitude, longitude, and elevation.
- Assumes elevation data is stored as a 2D variable: elevation[lat, lon].

Author: [Author]
Date: [Date]
"""

import argparse
import netCDF4 as nc
import numpy as np
import os
import sys

from utils  import read_points
from pyproj import Transformer

help_epilog = '''
Example usage:
   -h
  hycom_compare.py -h
  hycom_compare.py --file ./datasets/alaska_bbox4.nc
  hycom_compare.py --file ./datasets/alaska_bbox4.nc --output depth.dat-voro
'''

parser = argparse.ArgumentParser(
    description="Inspect and summarize NetCDF elevation data (lat/lon grid in EPSG:4326).",
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

# Automatically adds -h / --help option
args = parser.parse_args()

output_file = "./depth.dat-voro"
output_file = args.output

print('\n#Step 1: Load NetCDF Elevation Data')
nc_file = args.file
nc_basename = os.path.splitext(os.path.basename(nc_file))[0]

# Load NetCDF file
ds = nc.Dataset(nc_file)

# Print available variables and dimensions
print("Variables:", ds.variables.keys())
print("Dimensions:", ds.dimensions.keys())

# Extract variables
lat = ds.variables['Latitude'][:]      # 1D array
lon = ds.variables['Longitude'][:]      # 1D array

# Print shapes
print("lat shape:", lat.shape)
print("lon shape:", lon.shape)

# Print value ranges
print("Latitude range: {:.2f} to {:.2f}".format(lat.min(), lat.max()))
print("Longitude range: {:.2f} to {:.2f}".format(lon.min(), lon.max()))

print('\n#Step 3: Read ASCII ./points.dat File with Projected Coordinates')
# Call reader
projected_points = read_points('./points.dat')

# Convert to NumPy array
projected_points = np.array(projected_points)  # shape (N, 2)
x_proj = projected_points[:, 0]
y_proj = projected_points[:, 1]

# Print summary
print(f"\nLoaded {len(projected_points)} projected points from file points.dat.")

# Print value ranges
print("X projected range: {:.2f} to {:.2f}".format(x_proj.min(), x_proj.max()))
print("Y projected range: {:.2f} to {:.2f}".format(y_proj.min(), y_proj.max()))

print('\n#Step 4: Reproject EPSG:3338 (x, y) → EPSG:4326 (lon, lat)')
# EPSG:3338 (input) → EPSG:4326 (output)
transformer = Transformer.from_crs("EPSG:3338", "EPSG:4326", always_xy=True)

# Transform all projected (x, y) points to (lon, lat)
lon_query, lat_query = transformer.transform(x_proj, y_proj)

# Check Range
print("\nTransformed coordinate bounds:")
print(f"  Longitude: {lon_query.min():.4f} to {lon_query.max():.4f}")
print(f"  Latitude:  {lat_query.min():.4f} to {lat_query.max():.4f}")

print('\n# Step 4: Project NetCDF grid corners EPSG:4326 → EPSG:3338')
transformer_to_proj = Transformer.from_crs("EPSG:4326", "EPSG:3338", always_xy=True)

# Extract 4 corners
lon_corners = [lon[0,0], lon[0,-1], lon[-1,0], lon[-1,-1]]
lat_corners = [lat[0,0], lat[0,-1], lat[-1,0], lat[-1,-1]]

# Forward projection
x_corners, y_corners = transformer_to_proj.transform(lon_corners, lat_corners)

# Compute projected coordinate bounds
x_min, x_max = np.min(x_corners), np.max(x_corners)
y_min, y_max = np.min(y_corners), np.max(y_corners)

print("\nProjected grid coordinate bounds (corners only):")
print(f"  X range: {x_min:.2f} to {x_max:.2f}")
print(f"  Y range: {y_min:.2f} to {y_max:.2f}")

print("\n now use Longitude in -180,180")
# Extract corners as arrays
lon_corners = np.array([lon[0,0], lon[0,-1], lon[-1,0], lon[-1,-1]])
lat_corners = np.array([lat[0,0], lat[0,-1], lat[-1,0], lat[-1,-1]])

# Normalize longitudes from 0–360 to -180–180
lon_corners = np.where(lon_corners > 180, lon_corners - 360, lon_corners)

# Forward projection
x_corners, y_corners = transformer_to_proj.transform(lon_corners, lat_corners)

# Compute projected coordinate bounds
x_min, x_max = np.min(x_corners), np.max(x_corners)
y_min, y_max = np.min(y_corners), np.max(y_corners)

print("\nProjected grid coordinate bounds (corners only):")
print(f"  X range: {x_min:.2f} to {x_max:.2f}")
print(f"  Y range: {y_min:.2f} to {y_max:.2f}")

sys.exit()
if (lat_query.min() < lat.min() or lat_query.max() > lat.max() or
    lon_query.min() < lon.min() or lon_query.max() > lon.max()):
    print("⚠️  Warning: Query domain exceeds DEM coverage. Consider expanding DEM subset.")
    # add method to programatically extract bbox4
    #need environment with ncks
    #ncks -d lon,-143.0,-126.0 -d lat,48.0,60.0 GEBCO_2022_deflate.nc -O nc_file
else:
    print("✅ Query domain fully covered by DEM.")

print('\n#Step 5: Interpolate Elevation at (lat, lon)')

# Stack into shape (N, 2) — required by interp_func
query_points = np.column_stack((lat_query, lon_query))  # shape: (N, 2)

# Interpolate elevation at each (lat, lon) point
elev_interp = interp_func(query_points)  # returns array of shape (N,)

# Convention: depth is positive downward → depth = -elevation
depth = -elev_interp

# Print sample Output
print("\n--- Sample Depth Results ---")
for i in range(min(5, len(depth))):
    print(f"  x: {x_proj[i]:.2f}, y: {y_proj[i]:.2f}, depth: {depth[i]:.2f} m")

print('\n#Step 6: Write Output File (x,y,depth)')

output = np.column_stack((x_proj, y_proj, depth))

# Save to ASCII file
np.savetxt(output_file, output, fmt="%.3f", comments="")

# Confirm to user
print(f"Output file '{output_file}' written successfully.")

#Diagnose before fixing
# Identify NaN locations
mask_nan = np.isnan(depth)
frac_nan = np.mean(mask_nan)
#print(f"Fraction NaN: {np.mean(mask_nan):.2%}")
print(f"Fraction of NaN depth values: {frac_nan:.2%}")

import matplotlib.pyplot as plt

#plt.scatter(x_proj[mask_nan], y_proj[mask_nan], c='r', s=5, label='NaN points')
#plt.scatter(x_proj[~mask_nan], y_proj[~mask_nan], c='k', s=1, label='Valid')
#plt.legend()
#plt.title("NaN distribution in projected coordinates")
#plt.show()

# Create scatter plot of NaN vs valid points
plt.figure(figsize=(8, 6))
plt.scatter(x_proj[~mask_nan], y_proj[~mask_nan],
            c='k', s=2, label='Valid')
plt.scatter(x_proj[mask_nan], y_proj[mask_nan],
            c='r', s=6, label='NaN')
plt.xlabel("x (m, EPSG:3338)")
plt.ylabel("y (m, EPSG:3338)")
#plt.title(f"NaN Distribution in Depth Field ({frac_nan:.2%} NaN)")
plt.title(f"NaN Distribution in Depth Field ({frac_nan:.2%})\nSource: {nc_basename}")
plt.legend(markerscale=3)
plt.axis('equal')
plt.tight_layout()

# Save plot as PNG
png_name = f"nan_depth_distribution_{nc_basename}.png"
plt.savefig(png_name, dpi=300)
plt.close()

print(f"Saved NaN diagnostic plot: {png_name}")
