#!/usr/bin/env python3
"""
triangle2suntans.py - Convert Triangle (.node,.ele,.neigh) to SUNTANS files.

Outputs (no header lines):

  points.dat   : x y 0                (Delaunay points; 0 is unused placeholder)
  cells.dat    : xv yv p1 p2 p3 n1 n2 n3  (Voronoi point = triangle circumcenter, p's and n's are 0-based)
  edges.dat    : p1 p2 marker vor1 vor2   (Delaunay edge endpoints (0-based), marker: 0 computational, 1 boundary)

Assumptions:
  - .node, .ele, .neigh use Triangle's standard ASCII format.
  - Coordinates in .node are already projected (Cartesian).
  - Uses C-style (0-based) indexing in all outputs to match SUNTANS expectations.

Author: generated for user
"""

from __future__ import annotations
import argparse
import math
import sys
import os
import numpy as np

import logging
# Configure logger
logging.basicConfig(
    level=logging.INFO,        # minimum level to capture
    format="%(asctime)s [%(levelname)s] %(message)s",  # optional format
    handlers=[logging.StreamHandler()]  # ensures logs go to stdout
)

logger = logging.getLogger(__name__)

import sys

# colored output
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

def read_node(filename, base=1):
    """Read .node file, return coords list (aligned to requested base)."""
    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)
    coords = None
    with open(filename, 'r') as f:
        while True:
            hdr = f.readline()
            if not hdr:
                raise RuntimeError("Unexpected end of .node file")
            hdrs = hdr.strip().split()
            if len(hdrs) == 0:
                continue
            npts = int(float(hdrs[0]))
            coords = [None] * (npts + 1)  # internally always 1-based
            break
        for _ in range(npts):
            parts = f.readline().strip().split()
            if len(parts) < 3:
                continue
            nid = int(float(parts[0])) + (1 - base)  # shift if base==0
            x = float(parts[1]); y = float(parts[2])
            coords[nid] = (x, y)
    if coords is None or any(c is None for c in coords[1:]):
        raise RuntimeError("Missing or bad node entries in .node file")
    return coords

def read_ele(filename, base=1):
    """Read .ele file, return tris[tid] = (n1,n2,n3)."""
    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)
    tris = None
    with open(filename, 'r') as f:
        while True:
            hdr = f.readline()
            if not hdr:
                raise RuntimeError("Unexpected end of .ele file")
            hdrs = hdr.strip().split()
            if len(hdrs) == 0:
                continue
            nele = int(float(hdrs[0]))
            nvert = int(float(hdrs[1])) if len(hdrs) > 1 else 3
            if nvert != 3:
                raise RuntimeError("Only triangles supported")
            tris = [None] * (nele + 1)  # internally always 1-based
            break
        for _ in range(nele):
            parts = f.readline().strip().split()
            if len(parts) < 4:
                continue
            tid = int(float(parts[0])) + (1 - base)   # shift if base==0
            n1 = int(float(parts[1])) + (1 - base)
            n2 = int(float(parts[2])) + (1 - base)
            n3 = int(float(parts[3])) + (1 - base)
            tris[tid] = (n1, n2, n3)
    try:
        if tris is None or any(t is None for t in tris[1:]):
            raise RuntimeError("Failed to read .ele or missing triangles")
    except RuntimeError as e:
        logger.exception("Runtime error occurred")

    return tris

def read_neigh(filename, expected_nele, base=1):
    """Read .neigh file and return neighbors list indexed 1..nele."""
    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)
    neigh = None
    with open(filename, 'r') as f:
        while True:
            hdr = f.readline()
            if not hdr:
                raise RuntimeError("Unexpected end of .neigh file")
            hdrs = hdr.strip().split()
            if len(hdrs) == 0:
                continue
            nele = int(float(hdrs[0]))
            if nele != expected_nele:
                print(f"{YELLOW}Warning:{RESET} .neigh header says {nele} triangles but .ele had {expected_nele}. Proceeding with {expected_nele}.")
            neigh = [None] * (expected_nele + 1)
            break
        for _ in range(expected_nele):
            line = f.readline()
            if not line:
                break
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            tid = int(float(parts[0])) + (1 - base)
            nb1 = int(float(parts[1])) + (1 - base)
            nb2 = int(float(parts[2])) + (1 - base)
            nb3 = int(float(parts[3])) + (1 - base)
            nb1 = nb1 if nb1 >= 0 else -1
            nb2 = nb2 if nb2 >= 0 else -1
            nb3 = nb3 if nb3 >= 0 else -1
            neigh[tid] = (nb1, nb2, nb3)
    try:
        if neigh is None or any(n is None for n in neigh[1:]):
            raise RuntimeError("Failed to read .neigh or missing neighbor rows")
    except RuntimeError as e:
        logger.exception("Runtime error occurred")

    return neigh

def circumcenter(pa, pb, pc):
    """Circumcenter of triangle pa,pb,pc (pa=(x,y)). Robust fallback to centroid."""
    (x1,y1),(x2,y2),(x3,y3) = (pa, pb, pc)
    dx1 = x2 - x1; dy1 = y2 - y1
    dx2 = x3 - x1; dy2 = y3 - y1
    det = dx1 * dy2 - dy1 * dx2
    if abs(det) < 1e-12:
        return ((x1+x2+x3)/3.0, (y1+y2+y3)/3.0)
    a = dx1; b = dy1; c = (dx1*dx1 + dy1*dy1) / 2.0
    d = dx2; e = dy2; f = (dx2*dx2 + dy2*dy2) / 2.0
    det2 = a*e - b*d
    ux = ( c*e - b*f ) / det2
    uy = ( a*f - c*d ) / det2
    return (ux + x1, uy + y1)

def build_edge_map(tris):
    edge_map = {}
    for tid in range(1, len(tris)):
        n1,n2,n3 = tris[tid]
        edges = [(n1,n2), (n2,n3), (n3,n1)]
        for a,b in edges:
            key = (a,b) if a < b else (b,a)
            edge_map.setdefault(key, []).append(tid)
    return edge_map

def write_points_file(nodes, out="points.dat"):
    with open(out, 'w') as f:
        for nid in range(1, len(nodes)):
            x,y = nodes[nid]
            f.write(f"{x:.9g} {y:.9g} 0\n")

def write_cells_file(tris, nodes, neigh, out="cells.dat"):
    with open(out, 'w') as f:
        for tid in range(1, len(tris)):
            n1,n2,n3 = tris[tid]
            pa = nodes[n1]; pb = nodes[n2]; pc = nodes[n3]
            xv, yv = circumcenter(pa,pb,pc)
            p1 = n1 - 1; p2 = n2 - 1; p3 = n3 - 1
            nb1, nb2, nb3 = neigh[tid]
            nb1s = nb1-1 if nb1 > 0 else -1
            nb2s = nb2-1 if nb2 > 0 else -1
            nb3s = nb3-1 if nb3 > 0 else -1
            f.write(f"{xv:.9g} {yv:.9g} {p1:d} {p2:d} {p3:d} {nb1s:d} {nb2s:d} {nb3s:d}\n")

def write_cells_file_hybrid(nodes, tris, neigh, edge_map, out='cells.dat'):
    with open(out, 'w') as f:
        for edge, adj_tris in edge_map.items():
            nfaces = len(adj_tris) if len(adj_tris) > 0 else 1
            xv = (nodes[edge[0]][0] + nodes[edge[1]][0]) / 2
            yv = (nodes[edge[0]][1] + nodes[edge[1]][1]) / 2
            cells = [(tri_id if tri_id else 0) for tri_id in adj_tris]
            if len(cells) < nfaces:
                cells += [0] * (nfaces - len(cells))
            cells = [c if c != 0 else 0 for c in cells]
            neighbors = []
            for c in cells[:nfaces]:
                if c > 0 and neigh[c - 1] is not None and len(neigh[c - 1]) > 0:
                    nbors = neigh[c - 1]
                    neighbors.append(nbors[0] - 1 if nbors[0] > 0 else -1)
                else:
                    neighbors.append(-1)
            if len(neighbors) < nfaces:
                neighbors += [-1] * (nfaces - len(neighbors))
            line_vals = [str(nfaces), f"{xv:.6f}", f"{yv:.6f}"] + \
                        [str(c) for c in cells[:nfaces]] + \
                        [str(n) for n in neighbors[:nfaces]]
            f.write(" ".join(line_vals) + "\n")

def write_edges_file(edge_map, out="edges.dat"):
    keys = sorted(edge_map.keys())
    with open(out, 'w') as f:
        for key in keys:
            a,b = key
            adj = edge_map[key]
            p1 = a - 1; p2 = b - 1
            if len(adj) == 1:
                marker = 1
                vor1 = adj[0] - 1
                vor2 = -1
            elif len(adj) >= 2:
                marker = 0
                vor1 = adj[0] - 1
                vor2 = adj[1] - 1
            else:
                marker = 1
                vor1 = -1; vor2 = -1
            f.write(f"{p1:d} {p2:d} {marker:d} {vor1:d} {vor2:d}\n")

def main():
    ap = argparse.ArgumentParser(
        description="Convert Triangle (.node,.ele,.neigh) -> SUNTANS (points,cells,edges)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ap.add_argument("--prefix", required=True, help="Triangle file prefix (prefix.node, prefix.ele, prefix.neigh)")
    ap.add_argument("--node-base", type=int, choices=[0, 1], default=1, help="Index base for .node file (0 or 1, default=1)")
    ap.add_argument("--ele-base", type=int, choices=[0, 1], default=1, help="Index base for .ele file (0 or 1, default=1)")
    ap.add_argument("--neigh-base", type=int, choices=[0, 1], default=1, help="Index base for .neigh file (0 or 1, default=1)")
    args = ap.parse_args()

    prefix = args.prefix
    nodefile = prefix + ".node"
    elefile  = prefix + ".ele"
    neighfile= prefix + ".neigh"

    try:
        nodes = read_node(nodefile, base=args.node_base)
        tris  = read_ele(elefile, base=args.ele_base)
        neigh = read_neigh(neighfile, len(tris)-1, base=args.neigh_base)
    except Exception as e:
        print(f"{RED}ERROR:{RESET} {e}")
        sys.exit(1)

    print(f"Read {len(nodes)-1} points, {len(tris)-1} triangles.")

    try:
        max_index_cells = np.max(np.fromiter(
            (v for t in tris if t is not None for v in t),
            dtype=int
        ))
        min_index_cells = np.min(np.fromiter(
            (v for t in tris if t is not None for v in t),
            dtype=int
        ))
        max_index_xp = np.max(np.fromiter(
            (i for i, n in enumerate(nodes) if n is not None),
            dtype=int
        ))
    except ValueError as e:
        logger.error(f"ValueError in index calculation: {e}")
        sys.exit(1)

    # Log diagnostic info about cells indices and self.xp size
    logger.info(f"cells min index: {min_index_cells}, max index: {max_index_cells}")
    logger.info(f"nodes axis 0 size: {max_index_xp} (max valid index {max_index_xp})")

    # Warn if indices are out of bounds
    if min_index_cells < 0 or max_index_cells > max_index_xp:
        logger.warning(
            f"cells indices out of valid self.xp range: min index {min_index_cells}, "
            f"max index {max_index_cells}, valid max index {max_index_xp}"
        )

    edge_map = build_edge_map(tris)

    write_points_file(nodes, out="points.dat")
    write_cells_file(tris, nodes, neigh, out="cells.dat")
    #write_cells_file_hybrid(nodes, tris, neigh, edge_map, out='cells.dat')
    write_edges_file(edge_map, out="edges.dat")

    n_boundary = sum(1 for adj in edge_map.values() if len(adj) == 1)
    print(f"{GREEN}Info:{RESET} edges.dat written ({len(edge_map)} edges).")
    print(f"{YELLOW}Note:{RESET} {n_boundary} edges were marked as boundary edges (marker=1) automatically because they have only one adjacent triangle.")
    print(f"{GREEN}Done.{RESET} Generated: points.dat, cells.dat, edges.dat")

if __name__ == "__main__":
    main()

#    for handler in logger.handlers:
#        handler.flush()
#    sys.exit()
