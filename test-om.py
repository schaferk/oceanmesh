#!/usr/bin/env python3

import oceanmesh; 
print(oceanmesh.__version__)

import zipfile
import requests
import oceanmesh as om

EPSG = 32619  # A Python int, dict, or str containing the CRS information (in this case UTM19N)
bbox = (
    -70.29637,
    -43.56508,
    -69.65537,
    43.88338,
)  # the extent of the domain (can also be a multi-polygon delimited by rows of np.nan)
extent = om.Region(
    extent=bbox, crs=4326
)  # set the region (the bbox is given here in EPSG:4326 or WGS84)
extent = extent.transform_to(EPSG)  # Now I transform to the desired EPSG (UTM19N)
print(
    extent.bbox
)  # now the extents are in the desired CRS and can be passed to various functions later on


# Download and load the GSHHS shoreline
url = "http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.7.zip"
filename = url.split("/")[-1]
with open(filename, "wb") as f:
    r = requests.get(url)
    f.write(r.content)

with zipfile.ZipFile("gshhg-shp-2.3.7.zip", "r") as zip_ref:
    zip_ref.extractall("gshhg-shp-2.3.7")

fname = "gshhg-shp-2.3.7/GSHHS_shp/f/GSHHS_f_L1.shp"
EPSG = 4326  # EPSG code for WGS84 which is what you want to mesh in
# Specify and extent to read in and a minimum mesh size in the unit of the projection
extent = om.Region(extent=(-75.000, -70.001, 40.0001, 41.9000), crs=EPSG)
min_edge_length = 0.01  # In the units of the projection!
shoreline = om.Shoreline(
    fname, extent.bbox, min_edge_length, crs=EPSG
)  # NB: the Shoreline class assumes WGS84:4326 if not specified
shoreline.plot(
    xlabel="longitude (WGS84 degrees)",
    ylabel="latitude (WGS84 degrees)",
    title="shoreline boundaries",
)
# Using our shoreline, we create a signed distance function
# which will be used for meshing later on.
sdf = om.signed_distance_function(shoreline)

