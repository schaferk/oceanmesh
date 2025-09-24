#!/usr/bin/env python3

import logging
import xarray as xr
import rioxarray
import numpy as np
import oceanmesh as om

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Adjust level to DEBUG for verbose output
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# File paths
netcdf_file = "datasets/alaska_bbox2.nc"
geotiff_file = "datasets/alaska_bbox2.tif"

try:
    logger.info(f"Opening NetCDF: {netcdf_file}")
    ds = xr.open_dataset(netcdf_file)

    elevation = ds['elevation']
    logger.debug(f"Elevation shape before rotation: {elevation.shape}")
    logger.debug(f"Elevation dims: {elevation.dims}")
    logger.debug(f"Elevation coords summary:\n{elevation.coords}")

    # Rotation
    k_rotation = 3  # Adjust rotation as needed
    elevation_rotated_data = np.rot90(elevation.values, k=k_rotation)
    lat_len, lon_len = elevation_rotated_data.shape
    logger.info(f"Rotated data shape: {elevation_rotated_data.shape}")

    # Create coordinate arrays spanning desired bounds
    lon_coords = np.linspace(-140.0, -127.0, lon_len)
    lat_coords = np.linspace(51.0, 58.0, lat_len)

    logger.debug(f"Longitude coords first 5: {lon_coords[:5]}, last 5: {lon_coords[-5:]}")
    logger.debug(f"Latitude coords first 5: {lat_coords[:5]}, last 5: {lat_coords[-5:]}")

    # Check coordinate monotonicity and reverse if needed
    if not np.all(np.diff(lat_coords) > 0):
        logger.warning("Latitude coordinate array is not strictly increasing; reversing.")
        lat_coords = lat_coords[::-1]

    if not np.all(np.diff(lon_coords) > 0):
        logger.warning("Longitude coordinate array is not strictly increasing; reversing.")
        lon_coords = lon_coords[::-1]

    # Build DataArray with coords assigned
    rotated_elevation = xr.DataArray(
        elevation_rotated_data,
        dims=("lat", "lon"),
        coords={
            "lat": lat_coords,
            "lon": lon_coords,
        }
    )

    logger.debug(f"DataArray dims after assignment: {rotated_elevation.dims}")
    logger.debug(f"DataArray coords summary:\n{rotated_elevation.coords}")

    # Set spatial dims and CRS for GeoTIFF export
    rotated_elevation = rotated_elevation.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
    rotated_elevation = rotated_elevation.rio.write_crs("EPSG:4326")

    # Validate bounds
    bounds = rotated_elevation.rio.bounds()
    logger.info(f"Computed GeoTIFF bounds: {bounds}")

    # Save to GeoTIFF
    rotated_elevation.rio.to_raster(geotiff_file)
    logger.info(f"Saved rotated GeoTIFF to: {geotiff_file}")

    # Load in OceanMesh and plot
    EPSG = 4326
    dem = om.DEM(geotiff_file, crs=EPSG)

    # Log DEM info for debugging
    logger.debug(f"DEM bbox: {dem.bbox}")
    logger.debug(f"DEM dims: {dem.dims}")

    dem.plot(
        xlabel="longitude (WGS84 degrees)",
        ylabel="latitude (WGS84 degrees)",
        title="GEBCO_2022 15arc sec from GeoTIFF",
        cbarlabel="elevation (meters)",
        vmin=-100,
        vmax=10,
    )

except Exception as e:
    logger.error(f"Error occurred: {e}", exc_info=True)

