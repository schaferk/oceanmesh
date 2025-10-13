#!/usr/bin/env python3

import netCDF4 as nc
import numpy as np

#dataset_stem='/Users/schaferk/MDLOPS/repos/oceanmesh/datasets'
#os.path.join(dataset_stem, "alaska_bbox2.nc")

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

