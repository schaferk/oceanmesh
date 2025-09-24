#!/usr/bin/env python3

import xarray as xr
import rioxarray
import numpy as np
import oceanmesh as om

# File paths
netcdf_file = "datasets/alaska_bbox2.nc"
geotiff_file = "datasets/alaska_bbox2.tif"

# Step 1: Open the NetCDF dataset
ds = xr.open_dataset(netcdf_file)
elevation = ds['elevation']

# Choose rotation parameter k:
# k=1 for 90 degrees CCW, k=3 for 90 degrees CW (try which fits)
k_rotation = 3
elevation_rotated_data = np.rot90(elevation.values, k=k_rotation)

# Determine dimensions of rotated data
lat_len, lon_len = elevation_rotated_data.shape

# Create coordinate arrays explicitly covering target bounding box
lon_coords = np.linspace(-140.0, -127.0, lon_len)
lat_coords = np.linspace(51.0, 58.0, lat_len)

# Build DataArray with coords assigned
rotated_elevation = xr.DataArray(
    elevation_rotated_data,
    dims=("lat", "lon"),
    coords={
        "lat": lat_coords,
        "lon": lon_coords,
    }
)

# Set spatial dims and CRS for GeoTIFF export
rotated_elevation = rotated_elevation.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
rotated_elevation = rotated_elevation.rio.write_crs("EPSG:4326")

# Verify bounds
print("GeoTIFF bounds:", rotated_elevation.rio.bounds())

# Save to GeoTIFF
rotated_elevation.rio.to_raster(geotiff_file)

# Step 2: Load GeoTIFF in OceanMesh and plot
EPSG = 4326
dem = om.DEM(geotiff_file, crs=EPSG)

dem.plot(
    xlabel="longitude (WGS84 degrees)",
    ylabel="latitude (WGS84 degrees)",
    title="GEBCO_2022 15arc sec from GeoTIFF",
    cbarlabel="elevation (meters)",
    vmin=-100,
    vmax=10,
)

