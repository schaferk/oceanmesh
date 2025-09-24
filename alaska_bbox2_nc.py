#!/usr/bin/env python3

import xarray as xr
import rioxarray
import oceanmesh as om

# File paths
netcdf_file = "datasets/alaska_bbox2.nc"
geotiff_file = "datasets/alasak_bbox2.tif"

# Step 1: Convert NetCDF to GeoTIFF using xarray + rioxarray
ds = xr.open_dataset(netcdf_file)

# Extract the elevation variable - assumed as 'elevation' here
elevation = ds['elevation']

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
    #title="SRTM 30m from GeoTIFF",
    title="GEBCO_2022 15arc sec from GeoTIFF",
    cbarlabel="elevation (meters)",
    vmin=-10,
    vmax=10,
)

