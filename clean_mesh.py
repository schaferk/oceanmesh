#!/usr/bin/env python3
"""
Clean mesh data by removing bad cells and unused points.

Usage:
  python clean_mesh.py [--points points.dat] [--cells cells.dat] [--bad-cells BAD_CELLS]

Inputs:
  points.dat: Original points file (default: points.dat)
  cells.dat: Original cells file (default: cells.dat)
  BAD_CELLS: List of cell indices to remove (default: BAD_CELLS)

Outputs:
  Overwrites points.dat and cells.dat with cleaned data.
  Backups made as points.dat.bak and cells.dat.bak before overwriting.
"""

import argparse
import shutil
import os

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

def read_bad_cells(filename):
    bad = set()
    with open(filename) as f:
        for line in f:
            if line.strip().isdigit():
                bad.add(int(line.strip()))
    return bad

def write_cells(filename, cells, index_map):
    with open(filename, 'w') as f:
        for cx, cy, nodes in cells:
            mapped_nodes = [index_map[n] for n in nodes]
            line = f"{cx} {cy} {mapped_nodes[0]} {mapped_nodes[1]} {mapped_nodes[2]}\n"
            f.write(line)

def write_points(filename, points):
    with open(filename, 'w') as f:
        for x, y in points:
            f.write(f"{x} {y} 0\n")  # assuming z=0, original had z=0

def main():
    parser = argparse.ArgumentParser(description="Clean mesh by removing bad cells and unused points.")
    parser.add_argument("--points", default="points.dat", help="Input points.dat file (default: points.dat)")
    parser.add_argument("--cells", default="cells.dat", help="Input cells.dat file (default: cells.dat)")
    parser.add_argument("--bad-cells", default="BAD_CELLS", help="File listing cell indices to remove (default: BAD_CELLS)")
    args = parser.parse_args()

    points = read_points(args.points)
    cells = read_cells(args.cells)
    bad_cells = read_bad_cells(args.bad_cells)

    # Filter out bad cells
    cleaned_cells = [(cx, cy, nodes) for i, (cx, cy, nodes) in enumerate(cells) if i not in bad_cells]

    # Collect all used points after removing bad cells
    used_points = set()
    for _, _, nodes in cleaned_cells:
        used_points.update(nodes)

    # Create mapping from old point index to new index
    old_to_new = {}
    new_points = []
    for old_idx, pt in enumerate(points):
        if old_idx in used_points:
            new_idx = len(new_points)
            old_to_new[old_idx] = new_idx
            new_points.append(pt)

    # Backup original files before overwriting
    shutil.copy2(args.points, args.points + ".bak")
    shutil.copy2(args.cells, args.cells + ".bak")

    # Write cleaned data (overwrite original files)
    write_cells(args.cells, cleaned_cells, old_to_new)
    write_points(args.points, new_points)

    print(f"Removed {len(bad_cells)} bad cells.")
    print(f"Points reduced from {len(points)} to {len(new_points)}.")
    print(f"Backups created: {args.points}.bak, {args.cells}.bak")
    print(f"Cleaned files written: {args.points}, {args.cells}")

if __name__ == "__main__":
    main()

