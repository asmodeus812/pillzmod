"""
Write simple box VRML models for parts without a stock KiCad 3D model:
the Molex connectors and the nice!nano on its sockets.

They are approximations (outline and height only) for renders and clearance
checks, not mechanical CAD.

Usage:  python3 models.py   (plain python, no KiCad needed)
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "lib", "pillz_split.3dshapes")

WHITE = (0.92, 0.9, 0.85)
BLACK = (0.08, 0.08, 0.08)
BROWN = (0.45, 0.3, 0.15)
NAVY = (0.08, 0.1, 0.25)
METAL = (0.75, 0.75, 0.78)


def box(x0, x1, y0, y1, z0, z1, color):
    """Box in footprint coordinates (mm, y down, z up from the board)."""
    # VRML for KiCad: 1 unit = 0.1 inch, y points up
    u = 2.54
    xs, ys, zs = (x0 / u, x1 / u), (-y0 / u, -y1 / u), (z0 / u, z1 / u)
    pts = [(x, y, z) for z in zs for y in ys for x in xs]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return (
        "Shape {\n"
        f"  appearance Appearance {{ material Material {{ diffuseColor {color[0]} {color[1]} {color[2]} }} }}\n"
        "  geometry IndexedFaceSet {\n"
        "    solid FALSE\n"
        "    coord Coordinate { point [ "
        + ", ".join(f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in pts)
        + " ] }\n"
        "    coordIndex [ "
        + ", ".join(" ".join(map(str, f)) + " -1" for f in faces)
        + " ]\n  }\n}\n"
    )


def write(name, shapes):
    with open(os.path.join(OUT, name + ".wrl"), "w") as f:
        f.write("#VRML V2.0 utf8\n")
        f.writelines(shapes)


def main():
    os.makedirs(OUT, exist_ok=True)

    # 39-53-2135: vertical ZIF, 13 pos 1.25 mm, slider on top
    write("Molex_0039532135", [
        box(-9.0, 9.0, -2.4, 2.4, 0, 6.5, WHITE),
        box(-8.6, 8.6, -2.2, 2.2, 6.5, 8.5, BROWN),
        box(-8.0, 8.0, -0.3, 0.3, 8.0, 8.55, BLACK),
    ])
    # same connector seated in the 2134/2135 dual footprint
    write("Molex_039532134", [
        box(-9.0, 9.0, -4.1, 0.7, 0, 6.5, WHITE),
        box(-8.6, 8.6, -3.9, 0.5, 6.5, 8.5, BROWN),
        box(-8.0, 8.0, -2.0, -1.4, 8.0, 8.55, BLACK),
    ])
    # nice!nano v2 on two 8.5 mm 1x12 sockets, USB-C at -y
    write("nice_nano_v2", [
        box(-8.89, -6.35, -15.24, 15.24, 0, 8.5, BLACK),
        box(6.35, 8.89, -15.24, 15.24, 0, 8.5, BLACK),
        box(-8.89, 8.89, -16.5, 16.5, 8.5, 9.7, NAVY),
        box(-4.47, 4.47, -17.0, -9.7, 9.7, 12.9, METAL),
        box(-3.5, 3.5, -2.0, 5.0, 9.7, 10.6, BLACK),
    ])
    print("wrote models to", OUT)


if __name__ == "__main__":
    main()
