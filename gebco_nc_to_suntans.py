#!/usr/bin/env python3

"""
Script to inspect a NetCDF file containing elevation data.

- Loads a NetCDF file with a (lat, lon) grid in EPSG:4326.
- Prints variable and dimension information.
- Displays the shape and range of latitude, longitude, and elevation.
- Assumes elevation data is stored as a 2D variable: elevation[lat, lon].

Author: schaferkotter
Date: 20251013
"""

import netCDF4 as nc
import numpy as np

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

