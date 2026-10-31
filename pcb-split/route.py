"""
Freerouting round-trip helpers for the split boards (KiCad python).

    python3 route.py dsn    <board.kicad_pcb> <out.dsn>
    python3 route.py finish <board.kicad_pcb> <in.ses>
    python3 route.py post   <board.kicad_pcb>   (run by finish)

"finish" imports the routed session, pours GND on both layers and saves.
"""

import os
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen  # noqa: E402

mm = pcbnew.FromMM


def export_dsn(pcb, dsn):
    board = pcbnew.LoadBoard(pcb)
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise RuntimeError("DSN export failed")


def gnd_pour(board):
    # drop a previous pour, keep the edge keepouts from gen.py
    for z in list(board.Zones()):
        if not z.GetIsRuleArea():
            board.Remove(z)
    box = board.GetBoardEdgesBoundingBox()
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(gnd)
        zone.SetLocalClearance(mm(0.3))
        zone.SetMinThickness(mm(0.25))
        # solid: thermal spokes on the small JST pad landed on islands
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        outline = zone.Outline()
        outline.NewOutline()
        for x, y in ((box.GetLeft(), box.GetTop()), (box.GetRight(), box.GetTop()),
                     (box.GetRight(), box.GetBottom()), (box.GetLeft(), box.GetBottom())):
            outline.Append(x, y)
        board.Add(zone)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def finish(pcb, ses):
    board = pcbnew.LoadBoard(pcb)
    for t in list(board.GetTracks()):
        board.Remove(t)
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise RuntimeError("SES import failed")
    pcbnew.SaveBoard(pcb, board)
    # pcbnew's python objects are unusable after the SES import, so the rest
    # runs in a fresh interpreter
    subprocess.run([sys.executable, os.path.abspath(__file__), "post", pcb], check=True)


def post(pcb):
    # the SES import replaces all tracks, put the fixed pre-routes back
    board = pcbnew.LoadBoard(pcb)
    side = "left" if "left" in os.path.basename(pcb) else "right"
    gen.add_preroutes(board, gen.HALVES[side])
    gnd_pour(board)
    pcbnew.SaveBoard(pcb, board)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"dsn": export_dsn, "finish": finish, "post": post}[cmd](*args)
