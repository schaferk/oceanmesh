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

#Step 1: Load NetCDF Elevation Data
nc_file = './datasets/alaska_bbox2.nc'  

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

#Step 2: Create Interpolator in (lat, lon)
from scipy.interpolate import RegularGridInterpolator

# Create interpolation function
interp_func = RegularGridInterpolator(
    (lat, lon),            # grid axes (lat, lon)
    elevation,             # grid values
    bounds_error=False,    # allows extrapolation (returns NaN)
    fill_value=np.nan      # fill value for out-of-bounds queries
)

print("\nInterpolator successfully created.")

