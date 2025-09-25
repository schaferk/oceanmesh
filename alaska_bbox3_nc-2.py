#!/usr/bin/env python3

import logging
import xarray as xr
import rioxarray
import numpy as np
import oceanmesh as om

import matplotlib.pyplot as plt

import sys

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Adjust level to DEBUG for verbose output
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s',
    datefmt='%H:%M:%S'
)

# Suppress matplotlib font manager logging and other verbose debug logs
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# File paths
netcdf_file = "datasets/alaska_bbox3.nc"
geotiff_file = "datasets/alaska_bbox3.tif"

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
    lon_coords = np.linspace(-140.0, -129.0, lon_len)
    lat_coords = np.linspace(53.0, 58, lat_len)

    logger.debug(f"Longitude coords first 3: {np.array2string(lon_coords[:3], precision=10, floatmode='fixed')}")
    logger.debug(f"Longitude coords  last 3: {np.array2string(lon_coords[-3:], precision=10, floatmode='fixed')}")
    logger.debug(f"Latitude  coords first 3: {np.array2string(lat_coords[:3], precision=10, floatmode='fixed')}")
    logger.debug(f"Latitude  coords  last 3: {np.array2string(lat_coords[-4:], precision=10, floatmode='fixed')}")

    # Calculate longitude and latitude span from coordinate arrays
    lon_span = lon_coords[-1] - lon_coords[0]
    lat_span = lat_coords[-1] - lat_coords[0]

    logger.info(f"lon_coords[-1]: {lon_coords[-1]}")
    logger.info(f"lon_coords[ 0]: {lon_coords[0]}")
    logger.info(f"lat_coords[-1]: {lat_coords[-1]}")
    logger.info(f"lat_coords[ 0]: {lat_coords[0]}")

    mean_lat = (lat_coords[-1] + lat_coords[ 0]) / 2  # mean latitude of your bounding box

    # Convert degrees to radians for cosine
    mean_lat_rad = np.deg2rad(mean_lat)

    # Correction factor for longitude scaling by latitude
    correction = np.cos(mean_lat_rad)

    # Compute adjusted aspect ratio for plotting:
    aspect_ratio = (lon_span / lat_span) * correction

    # Log the values
    logger.info(f"Longitude span: {lon_span}")
    logger.info(f"Latitude span: {lat_span}")
    logger.info(f"Computed aspect ratio for plotting: {aspect_ratio}")

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

    logger.debug(f"###### dir(dem) ######")
    print(dir(dem))
    logger.debug(f"######################")

    # Log DEM info for debugging
    logger.debug(f"DEM bbox: {dem.bbox}")

    logger.debug(f"DEM values shape: {dem.values.shape}")
    logger.debug(f"Longitude coords shape: {lon_coords.shape}")
    logger.debug(f"Latitude coords shape: {lat_coords.shape}")

    #logger.debug(f"dem.bbox.top: {dem.bbox.top}")
    #logger.debug(f"dem.bbox.bottom: {dem.bbox.bottom}")
    logger.debug(f"dem.bbox.top: {dem.bbox[3]}")
    logger.debug(f"dem.bbox.bottom: {dem.bbox[1]}")

    logger.debug(f"dem.plot")
    fig, ax =dem.plot(
        xlabel="longitude (WGS84 degrees)",
        ylabel="latitude (WGS84 degrees)",
        title="GEBCO_2022 15arc sec from GeoTIFF",
        vmin=-50,
        vmax=10,
   #    xlim=(lon_coords[0], lon_coords[-1]),  # Set longitude range for x-axis
   #    ylim=(lat_coords[0], lat_coords[-1]),  # Set latitude range for y-axis     #BLANK DATA
   #    xlim=(dem.bbox.left, dem.bbox.right),
   #    ylim=(dem.bbox.top, dem.bbox.bottom),  # Use as is and check if reversed
   #    ylim=(dem.bbox.bottom, dem.bbox.top),  # Use as is and check if reversed
   #    ylim=(lat_coords[0], lat_coords[-1]),  # Set latitude range for y-axis     #BLANK DATA
   #    ylim=(min(dem.bbox.bottom, dem.bbox.top), max(dem.bbox.bottom, dem.bbox.top)),
   #    ylim=(min(dem.bbox[1], dem.bbox[3]), max(dem.bbox[1], dem.bbox[3])),
    )

except Exception as e:
    logger.error(f"Error occurred: {e}", exc_info=True)

