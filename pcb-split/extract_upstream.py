"""
One-off: vendor the connector footprints (and their exact placement) from the
upstream pillzmod "pcb-pro" board into lib/pillz_split.pretty + placements.json.

The key-well flex cables and the thumb ribbon only reach the original connector
positions, so the split boards reuse these coordinates verbatim.

Usage (KiCad python):
    python3 extract_upstream.py [path/to/pcb-pro.kicad_pcb]   # default: ../pcb-pro
"""

import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib", "pillz_split.pretty")
SRC = os.path.join(HERE, "..", "pcb-pro", "pcb-pro.kicad_pcb")

# ref -> vendored footprint name
WANTED = {
    "J1": "Molex_0039532135",  # right function row
    "J2": "Molex_0039532135",  # left function row
    "J3": "Molex_039532134",  # right key well (2134/2135 dual footprint)
    "J4": "Molex_039532134",  # left key well
    "J5": "PinHeader_1x10_PillzThumb",  # right thumb ribbon
    "J6": "PinHeader_1x10_PillzThumb",  # left thumb ribbon
}


def main(src_path):
    src = pcbnew.LoadBoard(src_path)
    placements = {}
    saved = set()
    for ref, name in WANTED.items():
        fp = src.FindFootprintByReference(ref)
        pos = fp.GetPosition()
        placements[ref] = {
            "footprint": name,
            "x": pcbnew.ToMM(pos.x),
            "y": pcbnew.ToMM(pos.y),
            "rot": fp.GetOrientationDegrees(),
            "back": fp.IsFlipped(),
            # pad number -> upstream net name, used to verify the regenerated
            # boards and to name the nets on the split halves
            "pads": [
                {
                    "num": p.GetNumber(),
                    "x": pcbnew.ToMM(p.GetPosition().x),
                    "y": pcbnew.ToMM(p.GetPosition().y),
                    "net": p.GetNetname(),
                }
                for p in fp.Pads()
            ],
        }
        if name in saved:
            continue
        # normalise to front side, 0 deg, origin before saving to the library
        copy = pcbnew.FOOTPRINT(fp)
        if copy.IsFlipped():
            copy.Flip(copy.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        copy.SetOrientationDegrees(0)
        copy.SetPosition(pcbnew.VECTOR2I(0, 0))
        copy.SetFPID(pcbnew.LIB_ID("pillz_split", name))
        for p in copy.Pads():
            p.SetNetCode(0)
        pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(LIB, copy)
        saved.add(name)

    with open(os.path.join(HERE, "lib", "placements.json"), "w") as f:
        json.dump(placements, f, indent=2)
    print("saved", sorted(saved))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else SRC)
