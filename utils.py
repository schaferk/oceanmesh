# utils.py

def read_points(filename):
    """
    Reads a file of projected (x, y) coordinates.

    Parameters:
        filename (str): Path to the ASCII file.

    Returns:
        list of (x, y) tuples as floats
    """
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
