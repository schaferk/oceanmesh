#!/usr/bin/env python3
import sys
import pyvista as pv

HELP_TEXT = """
PyVista Mesh Viewer Interactive Controls:

Mouse / Trackpad:
- Left Click + Drag: Rotate the mesh in 3D
- Right Click + Drag / Two-finger drag on trackpad: Pan the scene
- Scroll Wheel or Pinch Gesture: Zoom in/out

Keyboard Shortcuts:
- z: Toggle zoom box mode
- r: Reset camera to original view
- w: Toggle wireframe display
- e: Toggle edges display
- a: Toggle axes display
- q or ESC: Quit the viewer
"""

def show_help():
    print(HELP_TEXT)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_help()
        sys.exit(0)

    mesh_file = "new_york.vtk"  # Change as needed
    mesh = pv.read(mesh_file)

    plotter = pv.Plotter()
    plotter.add_mesh(mesh, show_edges=True, color="lightblue")
    plotter.show_grid()
    plotter.add_axes()
    plotter.set_background("white")
    # Enable interactive rubber band zoom
    plotter.enable_zoom_style()

    # Show the interactive plot window
    plotter.show()

if __name__ == "__main__":
    main()

