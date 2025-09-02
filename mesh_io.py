def write_node_file(points, region_name='region'):
    node_filename = f"{region_name}.node"
    num_points = points.shape[0]
    num_dimensions = 2
    num_vertex_attributes = 1
    num_boundary_markers = 0

    header = f"{num_points} {num_dimensions} {num_vertex_attributes} {num_boundary_markers}\n"
    with open(node_filename, "w") as f:
        f.write(header)
        for idx, (x, y) in enumerate(points):
            f.write(f"{idx} {x:.8f} {y:.8f} 0\n")

def write_ele_file(cells, region_name='region'):
    ele_filename = f"{region_name}.ele"
    num_triangles = cells.shape[0]
    vertices_per_triangle = cells.shape[1]  # should be 3
    attributes_per_triangle = 1

    header = f"{num_triangles} {vertices_per_triangle} {attributes_per_triangle}\n"
    with open(ele_filename, "w") as f:
        f.write(header)
        for idx, tri_vertices in enumerate(cells):
            # Write triangle vertex indices and set attribute to 0
            f.write(f"{idx} {tri_vertices[0]} {tri_vertices[1]} {tri_vertices[2]}\n")

