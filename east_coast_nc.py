#!/usr/bin/env python3

import oceanmesh as om

fdem = "datasets/EastCoast.nc"

# Digital Elevation Models (DEM) can be read into oceanmesh in
# either the NetCDF format or GeoTiff format provided they are
# in geographic coordinates (WGS84)

# If no extents are passed (i.e., the kwarg bbox), then the entire extent of the
# DEM is read into memory.
# Note: the DEM will be projected to the desired CRS automatically.
EPSG = 4326
dem = om.DEM(fdem, crs=EPSG)
dem.plot(
    xlabel="longitude (WGS84 degrees)",
    ylabel="latitude (WGS84 degrees)",
    title="SRTM 30m",
    cbarlabel="elevation (meters)",
    vmin=-10,  # minimum elevation value in plot
    vmax=10,  # maximum elevation value in plot
)
