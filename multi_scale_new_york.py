#!/usr/bin/env python3
#https://github.com/schaferk/oceanmesh?tab=readme-ov-file#mesh-generation

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np

import oceanmesh as om

fname = "gshhg-shp-2.3.7/GSHHS_shp/f/GSHHS_f_L1.shp"
EPSG = 4326  # EPSG:4326 or WGS84
extent1 = om.Region(extent=(-75.00, -70.001, 40.0001, 41.9000), crs=EPSG)
min_edge_length1 = 0.01  # minimum mesh size in domain in projection
bbox2 = np.array(
    [
        [-73.9481, 40.6028],
        [-74.0186, 40.5688],
        [-73.9366, 40.5362],
        [-73.7269, 40.5626],
        [-73.7231, 40.6459],
        [-73.8242, 40.6758],
        [-73.9481, 40.6028],
    ],
    dtype=float,
)
extent2 = om.Region(extent=bbox2, crs=EPSG)
min_edge_length2 = 4.6e-4  # minimum mesh size in domain in projection
s1 = om.Shoreline(fname, extent1.bbox, min_edge_length1)
sdf1 = om.signed_distance_function(s1)
el1 = om.distance_sizing_function(s1, max_edge_length=0.05)
s2 = om.Shoreline(fname, extent2.bbox, min_edge_length2)
sdf2 = om.signed_distance_function(s2)
el2 = om.distance_sizing_function(s2)
# Control the element size transition
# from coarse to fine with the kwargs prefixed with `blend`
points, cells = om.generate_multiscale_mesh(
    [sdf1, sdf2],
    [el1, el2],
)
# remove degenerate mesh faces and other common problems in the mesh
points, cells = om.make_mesh_boundaries_traversable(points, cells)
# remove singly connected elements (elements connected to only one other element)
points, cells = om.delete_faces_connected_to_one_face(points, cells)
# remove poor boundary elements with quality < 15%
points, cells = om.delete_boundary_faces(points, cells, min_qual=0.15)
# apply a Laplacian smoother that preservers the mesh size distribution
points, cells = om.laplacian2(points, cells)

# plot it showing the different levels of resolution
triang = tri.Triangulation(points[:, 0], points[:, 1], cells)
gs = gridspec.GridSpec(2, 2)
gs.update(wspace=0.5)
plt.figure()

bbox3 = np.array(
    [
        [-73.78, 40.60],
        [-73.75, 40.60],
        [-73.75, 40.64],
        [-73.78, 40.64],
        [-73.78, 40.60],
    ],
    dtype=float,
)

ax = plt.subplot(gs[0, 0])  #
ax.set_aspect("equal")
ax.triplot(triang, "-", lw=1)
ax.plot(bbox2[:, 0], bbox2[:, 1], "r--")
ax.plot(bbox3[:, 0], bbox3[:, 1], "m--")

ax = plt.subplot(gs[0, 1])
ax.set_aspect("equal")
ax.triplot(triang, "-", lw=1)
ax.plot(bbox2[:, 0], bbox2[:, 1], "r--")
ax.set_xlim(np.amin(bbox2[:, 0]), np.amax(bbox2[:, 0]))
ax.set_ylim(np.amin(bbox2[:, 1]), np.amax(bbox2[:, 1]))
ax.plot(bbox3[:, 0], bbox3[:, 1], "m--")

ax = plt.subplot(gs[1, :])
ax.set_aspect("equal")
ax.triplot(triang, "-", lw=1)
ax.set_xlim(-73.78, -73.75)
ax.set_ylim(40.60, 40.64)
plt.show()
