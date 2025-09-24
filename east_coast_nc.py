#!/usr/bin/env python3

import xarray as xr
import rioxarray
import oceanmesh as om

# File paths
netcdf_file = "datasets/EastCoast.nc"
geotiff_file = "datasets/EastCoast.tif"

# Step 1: Convert NetCDF to GeoTIFF using xarray + rioxarray
ds = xr.open_dataset(netcdf_file)

# Extract the elevation variable - assumed as 'Band1' here
elevation = ds['Band1']

# Set spatial dimensions (lon, lat) and CRS (EPSG:4326)
elevation = elevation.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
elevation = elevation.rio.write_crs("EPSG:4326")

# Save to GeoTIFF
elevation.rio.to_raster(geotiff_file)

# Step 2: Load the generated GeoTIFF in OceanMesh
EPSG = 4326
dem = om.DEM(geotiff_file, crs=EPSG)

# Plot DEM
dem.plot(
    xlabel="longitude (WGS84 degrees)",
    ylabel="latitude (WGS84 degrees)",
    title="SRTM 30m from GeoTIFF",
    cbarlabel="elevation (meters)",
    vmin=-10,
    vmax=10,
)
