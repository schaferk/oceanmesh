#!/usr/bin/env python3
import sys
import time
import numpy as np

def print_help():
    print("Usage: chk_cells.py [options] [cells_file]")
    print("Check format and consistency of SUNTANS-style cells.dat file.")
    print()
    print("Options:")
    print("  --no-header      Treat input file as not having a header row with cell count")
    print("  -h, --help       Show this help message and exit")
    print()
    print("Positional arguments:")
    print("  cells_file       Path to cells.dat file (default: 'cells.dat')")

def main():
    start_time = time.time()

    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return

    no_header = "--no-header" in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    input_file = args[0] if args else "cells.dat"

    print(f"Checking cells file: {input_file} "
          f"(header={'absent' if no_header else 'present'})")

    with open(input_file, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    if no_header:
        # Each row: xv yv p1 p2 p3 n1 n2 n3
        n_cells = len(lines)
        cells = np.array([[int(val) for val in line.split()[2:]] for line in lines])
    else:
        # First line is cell count
        n_cells = int(lines[0])
        cells = np.array([[int(val) for val in line.split()[2:]] for line in lines[1:]])

    # Check cell count
    if n_cells != len(cells):
        print(f"❌ Header mismatch: expected {n_cells}, got {len(cells)}")
    else:
        print("✅ Header/row count matches number of cell lines.")

    # Check triangles (3 unique nodes)
    non_triangle_cells = [i for i, c in enumerate(cells[:, :3]) if len(set(c)) != 3]
    if non_triangle_cells:
        print(f"❌ Non-triangular cells found: {len(non_triangle_cells)}")
    else:
        print("✅ All cells are triangles (3 unique nodes each).")

    # Check positive indices
    invalid_node_indices = np.argwhere(cells[:, :3] < 0)
    if invalid_node_indices.size > 0:
        print(f"❌ Found invalid (zero or negative) node indices:")
        for i, j in invalid_node_indices:
            print(f"   Cell {i + 1}, node {j + 1} = {cells[i, j]}")
    else:
        print("✅ All node indices are positive integers.")

    if (not non_triangle_cells and
        invalid_node_indices.size == 0 and
        n_cells == len(cells)):
        print("✅ cells.dat passed all checks successfully.")

    elapsed = time.time() - start_time
    print(f"⏱️  Completed in {elapsed:.3f} seconds.")

if __name__ == "__main__":
    main()

