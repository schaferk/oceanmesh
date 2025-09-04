#!/usr/bin/env python3
"""
chk_mesh.py - Mesh quality checker for SUNTANS-style points.dat and cells.dat

Detects:
  - Sliver triangles (smallest angle < threshold)
  - Nearly-colinear points that can cause coincident Voronoi points

Usage:
  ./chk_mesh.py --points points.dat --cells cells.dat --min-angle 30.0

Inputs:
  points.dat: x y z
  cells.dat:  cx cy n1 n2 n3 [neighbors...]
              where (cx,cy) is cell centroid and n1,n2,n3 are point indices

Outputs:
  Reports cells with bad geometry.
"""

import argparse
import math
import sys

def read_points(filename):
    pts = []
    with open(filename) as f:
        for line in f:
            if not line.strip():
                continue
            x, y, *_ = map(float, line.split())
            pts.append((x, y))
    return pts

def read_cells(filename):
    cells = []
    with open(filename) as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            # first two are centroid coords
            cx, cy = map(float, parts[0:2])
            # next three are node indices
            node_ids = list(map(int, parts[2:5]))
            cells.append(node_ids)
    return cells

def angle(a, b, c):
    """Return angle at point b given triangle vertices a, b, c."""
    bax = a[0] - b[0]; bay = a[1] - b[1]
    bcx = c[0] - b[0]; bcy = c[1] - b[1]
    dot = bax * bcx + bay * bcy
    mag_ba = math.hypot(bax, bay)
    mag_bc = math.hypot(bcx, bcy)
    if mag_ba * mag_bc == 0:
        return 0.0
    cosang = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cosang))

def check_mesh(points, cells, min_angle):
    bad_cells = []
    for ci, nodes in enumerate(cells):
        try:
            a, b, c = [points[idx] for idx in nodes]
        except IndexError:
            print(f"Warning: cell {ci} has invalid node index {nodes}")
            continue
        angles = [angle(b, a, c), angle(a, b, c), angle(a, c, b)]
        minang = min(angles)
        if minang < min_angle:
            bad_cells.append((ci, minang, nodes))
    return bad_cells

def main():
    ap = argparse.ArgumentParser(description="Mesh quality checker for SUNTANS points/cells.")
    ap.add_argument("--points", required=True, help="points.dat file (x y z)")
    ap.add_argument("--cells", required=True, help="cells.dat file (cx cy n1 n2 n3 ...)")
    ap.add_argument("--min-angle", type=float, default=20.0,
                    help="Minimum allowed triangle angle in degrees (default=20)")
    args = ap.parse_args()

    points = read_points(args.points)
    cells = read_cells(args.cells)

    bad = check_mesh(points, cells, args.min_angle)

    total_cells = len(cells)
    num_bad = len(bad)

    if num_bad == 0:
        print("✅ Mesh check passed: no sliver triangles found. ({total_cells} cells checked)")
    else:
        frac_bad = 100.0 * num_bad / total_cells
        print(f"⚠️ Found {num_bad} bad cells out of {total_cells} "
              f"({frac_bad:.2f}% below {args.min_angle}°)")
        for ci, minang, nodes in bad[:20]:  # only show first 20
            print(f"  Cell {ci}: min angle={minang:.2f}°, nodes={nodes}")

if __name__ == "__main__":
    main()
