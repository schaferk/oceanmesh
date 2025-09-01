#!/usr/bin/env python3

import time
import meshio
import oceanmesh as om

start_time = time.perf_counter()  # Start timing

print(om.__version__)

fname = "gshhg-shp-2.3.7/GSHHS_shp/f/GSHHS_f_L1.shp"

EPSG = 4326  # EPSG:4326 otherwise known as WGS84
region_name='new_york'
output_filename = f"{region_name}_epsg{EPSG}.vtk"

extent = om.Region(extent=(-75.00, -70.001, 40.0001, 41.9000), crs=EPSG)
min_edge_length = 0.01  # minimum mesh size in domain in projection

shore = om.Shoreline(fname, extent.bbox, min_edge_length)

edge_length = om.distance_sizing_function(shore, max_edge_length=0.05)

domain = om.signed_distance_function(shore)

points, cells = om.generate_mesh(domain, edge_length)

# remove degenerate mesh faces and other common problems in the mesh
points, cells = om.make_mesh_boundaries_traversable(points, cells)

points, cells = om.delete_faces_connected_to_one_face(points, cells)

# remove low quality boundary elements less than 15%
points, cells = om.delete_boundary_faces(points, cells, min_qual=0.15)

# apply a Laplacian smoother
points, cells = om.laplacian2(points, cells)

# write the mesh with meshio
meshio.write_points_cells(
    output_filename,
    points,
    [("triangle", cells)],
    file_format="vtk",
)

end_time = time.perf_counter()  # End timing

print(f"Script execution time: {end_time - start_time:.2f} seconds")
