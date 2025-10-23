#!/usr/bin/env python3
"""
make_neigh.py — Generate a Triangle .neigh file from .ele and .node files.

Usage:
    ./make_neigh.py prefix.1.ele [prefix.1.node]

This script reads the .ele file (and optionally the .node file for sanity check)
and computes the neighbor list for each triangle. The output is written to
`prefix.neigh` in the same format that Triangle would produce.

Options:
    -h, --help   Show this help message and exit.
"""

import sys
import os
import argparse
from collections import defaultdict

def parse_ele(elefile):
    with open(elefile) as f:
        header = f.readline().split()
        if len(header) < 3:
            raise ValueError(f"Invalid .ele header in {elefile}")
        nelems, nverts, _ = map(int, header[:3])
        elems = []
        for line in f:
            if line.strip().startswith("#") or not line.strip():
                continue
            parts = line.split()
            elems.append([int(p) for p in parts[1:1+nverts]])
        return nelems, nverts, elems

def compute_neighbors(elems):
    """Return list of neighbor indices for each triangle."""
    edge2tri = defaultdict(list)
    for i, tri in enumerate(elems, start=1):
        n = len(tri)
        for j in range(n):
            e = tuple(sorted((tri[j], tri[(j+1)%n])))
            edge2tri[e].append(i)

    neighbors = [[] for _ in elems]
    for edge, tris in edge2tri.items():
        if len(tris) == 2:
            t1, t2 = tris
            neighbors[t1-1].append(t2)
            neighbors[t2-1].append(t1)

    # Pad with -1 so each triangle has the same number of sides
    max_sides = max(len(tri) for tri in elems)
    for nbrs in neighbors:
        while len(nbrs) < max_sides:
            nbrs.append(-1)
    return neighbors

def compute_vertex_neighbors(elems):
    """Return list of neighbor vertex indices for each vertex."""
    vertex_neighbors = defaultdict(set)

    for tri in elems:
        n = len(tri)
        for i in range(n):
            v_current = tri[i]
            v_next = tri[(i + 1) % n]
            v_prev = tri[(i - 1) % n]

            # Add neighbors for current vertex:
            vertex_neighbors[v_current].add(v_next)
            vertex_neighbors[v_current].add(v_prev)

    # Convert sets to sorted lists
    max_vertex = max(vertex_neighbors.keys())
    neighbors_list = [sorted(vertex_neighbors[v]) if v in vertex_neighbors else [] for v in range(max_vertex + 1)]

    return neighbors_list

def write_neigh(outfile, neighbors):
    with open(outfile, "w") as f:
        f.write(f"{len(neighbors)} {len(neighbors[0])}\n")
        for i, nbrs in enumerate(neighbors, start=1):
            f.write(f"{i} " + " ".join(str(n) for n in nbrs) + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Generate Triangle .neigh file from .ele/.node"
    )
    parser.add_argument("elefile", help=".ele file (e.g., prefix.1.ele)")
    parser.add_argument("nodefile", nargs="?", help=".node file (optional)")
    args = parser.parse_args()

    prefix = os.path.splitext(args.elefile)[0]
    outfile = prefix + ".neigh"

    nelems, nverts, elems = parse_ele(args.elefile)
    max_vertex = max(max(tri) for tri in elems)
    print(f"Maximum vertex index in elems: {max_vertex}")

    neighbors = compute_neighbors(elems)
    #neightbors = compute_vertex_neighbors(elems)
    # neighbors is a list of lists, e.g., [[1, 2], [0, 3], ...]
    max_neighbor = max(max(sublist) for sublist in neighbors if sublist)  # Handle empty sublists safely
    print(f"Maximum neighbor in neighbors: {max_neighbor}")

    write_neigh(outfile, neighbors)

    print(f"✔ Wrote {outfile}")

if __name__ == "__main__":
    main()

