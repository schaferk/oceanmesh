#!/usr/bin/env python3

"""
Script to inspect a NetCDF file containing elevation data.

- Loads a NetCDF file with a (lat, lon) grid in EPSG:4326.
- Prints variable and dimension information.
- Displays the shape and range of latitude, longitude, and elevation.
- Assumes elevation data is stored as a 2D variable: elevation[lat, lon].

Author: [Author]
Date: [Date]
"""

import netCDF4 as nc
import numpy as np
import os

from utils  import read_points
from pyproj import Transformer

output_file = "./depth.dat-voro"

print('\n#Step 1: Load NetCDF Elevation Data')
nc_file = './datasets/alaska_bbox2.nc'  
nc_file = './datasets/alaska_bbox4.nc'
nc_basename = os.path.splitext(os.path.basename(nc_file))[0]

# Load NetCDF file
ds = nc.Dataset(nc_file)

# Print available variables and dimensions
print("Variables:", ds.variables.keys())
print("Dimensions:", ds.dimensions.keys())

# Extract variables
lat = ds.variables['lat'][:]      # 1D array
lon = ds.variables['lon'][:]      # 1D array
elevation = ds.variables['elevation'][:, :]  # 2D array (lat, lon)

# Print shapes
print("lat shape:", lat.shape)
print("lon shape:", lon.shape)
print("elevation shape:", elevation.shape)

# Print value ranges
print("Latitude range: {:.2f} to {:.2f}".format(lat.min(), lat.max()))
print("Longitude range: {:.2f} to {:.2f}".format(lon.min(), lon.max()))
print("Elevation range: {:.2f} to {:.2f}".format(np.nanmin(elevation), np.nanmax(elevation)))
print("Elevation units:", ds.variables['elevation'].units)

# Print sample values
print("\nSample latitudes:", lat[:5])
print("Sample longitudes:", lon[:5])
print("Sample elevation values (top-left corner):\n", elevation[:5, :5])

#test the spacing betwen latitudes
lat_diff = np.diff(lat)
lon_diff = np.diff(lon)

print("Latitude spacing stats:")
print("  min:", np.min(lat_diff))
print("  max:", np.max(lat_diff))
print("  unique values:", np.unique(lat_diff))

print("Longitude spacing stats:")
print("  min:", np.min(lon_diff))
print("  max:", np.max(lon_diff))
print("  unique values:", np.unique(lon_diff))

print('\n#Step 2: Create Interpolator in (lat, lon)')
from scipy.interpolate import RegularGridInterpolator

# Create interpolation function
interp_func = RegularGridInterpolator(
    (lat, lon),            # grid axes (lat, lon)
    elevation,             # grid values
    bounds_error=False,    # allows extrapolation (returns NaN)
    fill_value=np.nan      # fill value for out-of-bounds queries
)

print("\nInterpolator successfully created.")

#query the interpolator at known lat/lon points from the grid:

# Test indices into the grid (lat_idx, lon_idx)
test_indices = [
    (0, 0),
    (100, 100),
    (-1, -1)
]

# Prepare test points and true values
test_points = np.array([[lat[i], lon[j]] for i, j in test_indices])
true_values = np.array([elevation[i, j] for i, j in test_indices])

# Interpolate at those points
interp_values = interp_func(test_points)

# Compare
print("\n--- Interpolation Accuracy Check ---")
for idx, pt, interp_val, true_val in zip(test_indices, test_points, interp_values, true_values):
    diff = interp_val - true_val
    print(f"Grid index: {idx}")
    print(f"  Lat: {pt[0]:.6f}, Lon: {pt[1]:.6f}")
    print(f"  True Elevation:       {true_val:.3f} m")
    print(f"  Interpolated Elevation: {interp_val:.3f} m")
    print(f"  Difference:           {diff:.6e} m\n")

print('\n#Step 3: Read ASCII File with Projected Coordinates')
# Call reader
projected_points = read_points('./points.dat')

# Convert to NumPy array
projected_points = np.array(projected_points)  # shape (N, 2)
x_proj = projected_points[:, 0]
y_proj = projected_points[:, 1]

# Print summary
print(f"\nLoaded {len(projected_points)} projected points from file.")
print("Sample (x, y) points in EPSG:3338:")
for i in range(min(5, len(x_proj))):
    print(f"  x: {x_proj[i]:.2f}, y: {y_proj[i]:.2f}")

print('\n#Step 4: Reproject EPSG:3338 (x, y) → EPSG:4326 (lon, lat)')
# EPSG:3338 (input) → EPSG:4326 (output)
transformer = Transformer.from_crs("EPSG:3338", "EPSG:4326", always_xy=True)

# Transform all projected (x, y) points to (lon, lat)
lon_query, lat_query = transformer.transform(x_proj, y_proj)

# Check a few sample results
print("\nSample transformed coordinates (EPSG:4326):")
for i in range(min(5, len(lon_query))):
    print(f"  Lon: {lon_query[i]:.6f}, Lat: {lat_query[i]:.6f}")

# Check Range
print("\nTransformed coordinate bounds:")
print(f"  Latitude:  {lat_query.min():.4f} to {lat_query.max():.4f}")
print(f"  Longitude: {lon_query.min():.4f} to {lon_query.max():.4f}")

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
