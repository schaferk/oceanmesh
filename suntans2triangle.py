#!/usr/bin/env python3

import argparse
import time
import os
import numpy as np

from mesh_io import write_node_file, write_ele_file

def read_points(filename):
    pts = []
    with open(filename) as f:
        for line in f:
            if not line.strip():
                continue
            x, y, *_ = line.split()
            pts.append((float(x), float(y)))
    return pts

def read_cells(filename):
    cells = []
    with open(filename) as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            cx, cy = map(float, parts[0:2])
            nodes = list(map(int, parts[2:5]))
            cells.append((cx, cy, nodes))
    return cells

def main():
    parser = argparse.ArgumentParser(description="write suntans points.dat, cells.dat to triangle PREFIX.node, PREFIX.ele.")
    parser.add_argument("--points", default="points.dat", help="Input points.dat file (default: points.dat)")
    parser.add_argument("--cells", default="cells.dat", help="Input cells.dat file (default: cells.dat)")
    parser.add_argument("--output_prefix", required=True, help="Output prefix for files (required)")
    args = parser.parse_args()

    start_time = time.perf_counter()  # Start timing

    points = np.array(read_points(args.points))
    write_node_file(points,args.output_prefix)

    cells = read_cells(args.cells)
    # Extract only the node indices part for the .ele file
    triangle_nodes = np.array([cell[2] for cell in cells])  # shape (num_triangles, 3)

    write_ele_file(triangle_nodes, args.output_prefix)

    end_time = time.perf_counter()  # End timing

    print(f"Script execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
