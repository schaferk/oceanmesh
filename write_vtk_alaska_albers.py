#!/usr/bin/env python3

import sys
import time
import meshio
import oceanmesh as om

from mesh_io import write_node_file, write_ele_file

start_time = time.perf_counter()  # Start timing

verbose = True

print(om.__version__)

fname = "gshhg-shp-2.3.7/GSHHS_shp/f/GSHHS_f_L1.shp"

EPSG = 3338  # Alaska Albers projection
region_name = 'alaska_albers'
output_filename = f"{region_name}_epsg{EPSG}.vtk"

# Define bbox in WGS84 coords as in draw_alaska.py (xmin, xmax, ymin, ymax)
bbox_wgs84 = (-138.0, -129.0, 53.5, 57.0)
region_wgs84 = om.Region(extent=bbox_wgs84, crs=4326)

# Transform region to Alaska Albers EPSG:3338
region_proj = region_wgs84.transform_to(EPSG)

# Ensure bbox order is correct after projection
xmin, ymin, xmax, ymax = region_proj.bbox
xmin, xmax = min(xmin, xmax), max(xmin, xmax)
ymin, ymax = min(ymin, ymax), max(ymin, ymax)
region_proj.bbox = (xmin, ymin, xmax, ymax)
print("Projected bbox (Alaska Albers):", region_proj.bbox)

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
# Print the first 5 entries
#print("First few points:\n", points[:5])

print("Shape of cells:", cells.shape)
#print("First few cells:\n", cells[:5])
#sys.exit()

# Clean and smooth mesh
# 1. vertices of each triangle are arranged in counterclockwise order;
#    Notes: fix_mesh is not defined
#points, cells = fix_mesh(points, cells)

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
    print("Remove elements (i.e., 'faces') connected to only one channel")
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

