#!/usr/bin/env python3

import sys
import time
import meshio
import oceanmesh as om

from mesh_io import write_node_file, write_ele_file

import logging
import sys

from oceanmesh import Region
from pyproj import Transformer

# Set up transformer
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3338", always_xy=True)

#logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
#logging.basicConfig(stream=sys.stdout, level=logging.INFO)
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

start_time = time.perf_counter()  # Start timing

verbose = True

# ANSI escape codes for colors
RED = "\033[91m"
GREEN = "\033[92m"
ENDC = "\033[0m"

print(om.__version__)

fname = "gshhg-shp-2.3.7/GSHHS_shp/f/GSHHS_f_L1.shp"

# EPSG codes
EPSG = 3338  # Alaska Albers projection
EPSG_WGS84 = 4326
EPSG_ALASKA_ALBERS = 3338

region_name = 'alaska_albers2'
output_filename = f"{region_name}_epsg{EPSG}.vtk"

# Step 1: Define WGS84 bbox
#bbox_wgs84 = (-134.0, 54.0, -130.0, 56.0)    #alaska_albers2
#bbox_wgs84 = (-138.0, 53.5, -129.0, 57.0)
bbox_wgs84 = (-140.0, 51.0, -127.0, 58.0)  # (lon_min, lat_min, lon_max, lat_max) #bbox2
region_wgs84 = om.Region(extent=bbox_wgs84, crs=4326)

# Step 2: Transform corners manually with pyproj
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3338", always_xy=True)

# Step 3: Transform all 4 corners of the WGS84 bbox
lon_min, lat_min, lon_max, lat_max = bbox_wgs84
corners_lonlat = [
    (lon_min, lat_min),  #SW
    (lon_min, lat_max),  #NW
    (lon_max, lat_min),  #SE
    (lon_max, lat_max),  #NE
]
# Transform all 4 corners
xs, ys = zip(*[transformer.transform(lon, lat) for lon, lat in corners_lonlat])

# Step 4: Compute safe projected bbox
xmin, xmax = min(xs), max(xs)
ymin, ymax = min(ys), max(ys)
bbox_proj_region = (xmin, xmax, ymin, ymax)

print("Computed projected bbox:")
print(f"  x: {xmin:.2f} to {xmax:.2f}")
print(f"  y: {ymin:.2f} to {ymax:.2f}")

# Step 5: Now create projected Region
region_proj = Region(extent=bbox_proj_region, crs=EPSG_ALASKA_ALBERS)

min_edge_length = 1000  # minimum mesh size ~1 km in meters for Albers projection

# Load shoreline in projected coords
shore = om.Shoreline(fname, region_proj.bbox, min_edge_length, crs=EPSG)

# Distance sizing function to control mesh resolution
edge_length = om.distance_sizing_function(shore, max_edge_length=5000)  # max edge length larger for coarser mesh away from shore

# Signed distance function defines mesh domain and boundary
domain = om.signed_distance_function(shore)

# Generate mesh points and cells
points, cells = om.generate_mesh(domain, edge_length)

print("Shape of points:", points.shape)
print("Shape of cells:", cells.shape)

# Clean and smooth mesh
points, cells, jx = om.fix_mesh(points, cells)
if verbose:
    print("# 1. vertices of each triangle are arranged in counterclockwise order;")
    print("Length of jx:", len(jx))
    print("Shape of points:", points.shape)
    print("Total number of points:", len(points))
    if len(jx) != len(points):
        diff = len(jx) - len(points)
        print(f"{RED}Warning: Length of jx ({len(jx)}) differs from length of points ({len(points)}).")
        print(f"Number of points removed: {diff}{ENDC}")
    else:
        print(f"{GREEN}Length of jx matches length of points, no points removed.{ENDC}")

# 2. conformity (a triangle is not allowed to have a vertex of another triangle in its interior);
# 3. traversability (the number of boundary segments is equal to the number of boundary vertices,
#      which guarantees a unique path along the mesh boundary).
points, cells = om.make_mesh_boundaries_traversable(points, cells)
if verbose:
    print("# Remove degenerate mesh faces and other common problems in the mesh.")
    print("Shape of points:", points.shape)
    print("Shape of  cells:", cells.shape)

# Remove elements (i.e., "faces") connected to only one channel
# These typically occur in channels at or near the grid scale.
points, cells = om.delete_faces_connected_to_one_face(points, cells)
if verbose:
    print("# Remove elements (i.e., 'faces') connected to only one channel")
    print("Shape of points:", points.shape)
    print("Shape of  cells:", cells.shape)

points, cells = om.delete_boundary_faces(points, cells, min_qual=0.15)

if verbose:
    print("# Remove low quality boundary elements less than min_qual")
    print("Shape of points:", points.shape)
    print("Shape of  cells:", cells.shape)

points, cells = om.laplacian2(points, cells)
if verbose:
    print("# Apply a Laplacian smoother that preserves the element density")
    print("Shape of points:", points.shape)
    print("Shape of  cells:", cells.shape)

# Write mesh to VTK file
meshio.write_points_cells(
    output_filename,
    points,
    [("triangle", cells)],
    file_format="vtk",
)

write_node_file(points,region_name)
write_ele_file(cells,region_name)

end_time = time.perf_counter()  # End timing

print(f"Script execution time: {end_time - start_time:.2f} seconds")

