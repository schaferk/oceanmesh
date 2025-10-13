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

