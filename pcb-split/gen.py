"""
Generate the left/right split boards for the Kinesis Advantage 2 pillzmod split.

Each half carries:
  * the original Molex/thumb-header connectors at their exact upstream
    coordinates (see extract_upstream.py / lib/placements.json)
  * a nice!nano (pro-micro footprint), portrait, USB towards the top edge
  * reset button, power slide switch and JST-PH battery socket below it
  * one M3 hole between the function row and key well connectors

The matrix is wired directly to the controller (9 rows + 7 cols = 16 GPIO per
half), so the 74HC595 of the single-board design is gone.

Usage (KiCad python):  python3 gen.py
"""

import json
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib", "pillz_split.pretty")
KLIB = "/app/extensions/Library/footprints"
# 3D models: approximations from models.py, plus stock KiCad ones
MODELS = "${KIPRJMOD}/../lib/pillz_split.3dshapes"
STOCK3D = "${KICAD10_3DMODEL_DIR}"
CONNECTOR_MODELS = {
    "Molex_0039532135": f"{MODELS}/Molex_0039532135.wrl",
    "Molex_039532134": f"{MODELS}/Molex_039532134.wrl",
    "PinHeader_1x10_PillzThumb":
        f"{STOCK3D}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x10_P2.54mm_Vertical.step",
}

mm = pcbnew.FromMM

with open(os.path.join(HERE, "lib", "placements.json")) as f:
    PLACEMENTS = json.load(f)

# Outer edges of the original board, the halves keep them so they sit where the
# original board sat.
TOP, BOTTOM = 50.0, 136.0

# top of the nice!nano body: level with the middle of the function row
# connector (J1/J2 run y=53.4..71.6)
NANO_TOP = 62.5

# nice!nano / pro-micro: pin number -> function. Pins 1-12 run down one side,
# 13-24 back up the other. "Dn" is the &pro_micro gpio number used by ZMK.
NANO_PINS = {
    1: "D1", 2: "D0", 3: "GND", 4: "GND", 5: "D2", 6: "D3", 7: "D4", 8: "D5",
    9: "D6", 10: "D7", 11: "D8", 12: "D9", 13: "D10", 14: "D16", 15: "D14",
    16: "D15", 17: "D18", 18: "D19", 19: "D20", 20: "D21", 21: "VCC",
    22: "RST", 23: "GND", 24: "B+",
}

HALVES = {
    "left": {
        "connectors": ["J2", "J4", "J6"],
        "outline": (100.0, 132.5),
        "nano_x": 121.12,
        # nano pin -> matrix net. Left column (13-24) faces the Molex
        # connectors, right column (1-12) faces the inner edge.
        "nano_nets": {
            20: "COL_0", 19: "ROW_12", 18: "ROW_13", 17: "ROW_14",
            16: "COL_2", 15: "COL_1",
            1: "ROW_0", 2: "ROW_1", 5: "COL_3", 6: "COL_4", 7: "ROW_2",
            8: "ROW_3", 9: "ROW_4", 10: "ROW_5", 11: "COL_5", 12: "COL_6",
        },
        # button row starts level with the key well connector (y=101.4),
        # battery socket ~3 mm below it
        "reset": (116.4, 104.3),
        # actuator points down into the free area, inner edge stays clear
        "switch": (125.9, 104.3, 180),
        "jst": (117.0, 113.8),
        # between the function row and key well connectors
        "holes": [(104.5, 86.5)],
        "label": (121.12, 120.0),
    },
    "right": {
        "connectors": ["J1", "J3", "J5"],
        "outline": (167.5, 200.0),
        "nano_x": 178.88,
        # right column (1-12) faces the Molex connectors here
        "nano_nets": {
            1: "ROW_13", 2: "ROW_14", 5: "ROW_12", 6: "COL_5", 7: "COL_3",
            8: "COL_4", 9: "ROW_10", 10: "ROW_9", 11: "ROW_11", 12: "COL_0",
            20: "COL_1", 19: "COL_2", 18: "ROW_6", 17: "ROW_7", 16: "ROW_8",
            15: "COL_6",
        },
        "reset": (183.6, 104.3),
        "switch": (174.1, 104.3, 180),
        "jst": (181.0, 113.8),
        "holes": [(195.5, 86.5)],
        "label": (178.88, 120.0),
        # J1 pin 1 (ROW_13) sits in the top corner and Freerouting fails to
        # reach it; run it down the free outer side of J1 to pin 11 (ROW_13)
        "preroutes": [
            ("ROW_13", "F.Cu", [(192.9, 55.0), (194.4, 56.5), (194.4, 66.0), (192.9, 67.5)]),
        ],
    },
}


def load(lib, name):
    fp = pcbnew.FootprintLoad(lib, name)
    if fp is None:
        raise RuntimeError(f"footprint {name} not found in {lib}")
    return fp


def set_model(fp, path):
    fp.Models().clear()
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    fp.Add3DModel(m)


def place(board, fp, ref, x, y, rot=0.0, back=True):
    fp.SetReference(ref)
    board.Add(fp)
    fp.SetOrientationDegrees(0)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    # board text labels these parts instead
    if ref[:2] in ("SW", "H") or ref in ("J1", "J2", "J7"):
        fp.Reference().SetVisible(False)
    return fp


def make_nano():
    """Pro-micro footprint, USB at -y, viewed from the controller's top side."""
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID("pillz_split", "nice_nano_v2"))
    fp.SetValue("nice!nano v2")
    for num in range(1, 25):
        if num <= 12:
            px, py = -7.62, -13.97 + (num - 1) * 2.54
        else:
            px, py = 7.62, -13.97 + (24 - num) * 2.54
        pad = pcbnew.PAD(fp)
        pad.SetNumber(str(num))
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pcbnew.PAD.PTHMask())
        pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_RECT if num == 1 else pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(mm(1.75), mm(1.75)))
        pad.SetDrillSize(pcbnew.VECTOR2I(mm(1.1), mm(1.1)))
        pad.SetPosition(pcbnew.VECTOR2I(mm(px), mm(py)))
        fp.Add(pad)

    def rect(layer, x0, y0, x1, y1, w=0.12):
        s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_RECT)
        s.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetLayer(layer)
        s.SetWidth(mm(w))
        fp.Add(s)

    rect(pcbnew.F_SilkS, -8.89, -16.5, 8.89, 16.5)
    rect(pcbnew.F_SilkS, -4.5, -16.2, 4.5, -14.8)  # USB-C
    rect(pcbnew.F_Fab, -8.89, -16.5, 8.89, 16.5, 0.1)
    rect(pcbnew.F_CrtYd, -9.15, -16.75, 9.15, 16.75, 0.05)
    for num, fn in NANO_PINS.items():
        px = -5.6 if num <= 12 else 5.6
        py = -13.97 + ((num - 1) if num <= 12 else (24 - num)) * 2.54
        t = pcbnew.PCB_TEXT(fp)
        t.SetText(fn)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        t.SetTextThickness(mm(0.12))
        t.SetPosition(pcbnew.VECTOR2I(mm(px), mm(py)))
        fp.Add(t)
    return fp


def text(board, s, x, y, size=1.0, rot=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetLayer(pcbnew.B_SilkS)
    t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextAngleDegrees(rot)
    board.Add(t)


def outline(board, x0, x1, r=1.5):
    y0, y1 = TOP, BOTTOM

    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)

    def arc(c, start, angle):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetCenter(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
        s.SetStart(pcbnew.VECTOR2I(mm(start[0]), mm(start[1])))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)

    seg((x0 + r, y0), (x1 - r, y0))
    seg((x1, y0 + r), (x1, y1 - r))
    seg((x1 - r, y1), (x0 + r, y1))
    seg((x0, y1 - r), (x0, y0 + r))
    arc((x1 - r, y0 + r), (x1 - r, y0), 90)
    arc((x1 - r, y1 - r), (x1, y1 - r), 90)
    arc((x0 + r, y1 - r), (x0 + r, y1), 90)
    arc((x0 + r, y0 + r), (x0, y0 + r), 90)


def edge_keepout(board, x0, x1, w=0.6):
    """Track/via keepout strip inside the outline. Freerouting doesn't get the
    copper-to-edge rule from the DSN, but it does honour keepouts."""
    y0, y1 = TOP, BOTTOM
    layers = pcbnew.LSET()
    layers.AddLayer(pcbnew.F_Cu)
    layers.AddLayer(pcbnew.B_Cu)
    for rx0, ry0, rx1, ry1 in ((x0, y0, x1, y0 + w), (x0, y1 - w, x1, y1),
                               (x0, y0, x0 + w, y1), (x1 - w, y0, x1, y1)):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetLayerSet(layers)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)):
            o.Append(mm(x), mm(y))
        board.Add(z)


def add_preroutes(board, cfg):
    """Locked tracks the autorouter keeps; route.py re-adds any it drops."""
    for netname, layer, pts in cfg.get("preroutes", []):
        net = board.FindNet(netname)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if has_track(board, netname, x0, y0, x1, y1):
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
            t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
            t.SetWidth(mm(0.25))
            t.SetLayer(board.GetLayerID(layer))
            t.SetNet(net)
            t.SetLocked(True)
            board.Add(t)


def has_track(board, netname, x0, y0, x1, y1):
    ends = {(mm(x0), mm(y0)), (mm(x1), mm(y1))}
    for t in board.GetTracks():
        if t.GetNetname() == netname and t.GetClass() == "PCB_TRACK":
            a, b = t.GetStart(), t.GetEnd()
            if {(a.x, a.y), (b.x, b.y)} == ends:
                return True
    return False


def design_rules(board):
    ds = board.GetDesignSettings()
    # JLCPCB standard 2-layer capabilities, with margin
    ds.m_MinClearance = mm(0.2)
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.2))
    nc.SetTrackWidth(mm(0.25))
    nc.SetViaDiameter(mm(0.6))
    nc.SetViaDrill(mm(0.3))


def build(side, cfg):
    board = pcbnew.BOARD()
    design_rules(board)
    nets = {}

    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    # connectors, verbatim from upstream
    for ref in cfg["connectors"]:
        p = PLACEMENTS[ref]
        fp = place(board, load(LIB, p["footprint"]), ref, p["x"], p["y"], p["rot"], p["back"])
        set_model(fp, CONNECTOR_MODELS[p["footprint"]])
        want = sorted((d["num"], round(d["x"], 3), round(d["y"], 3), d["net"]) for d in p["pads"])
        got = sorted(
            (pd.GetNumber(), round(pcbnew.ToMM(pd.GetPosition().x), 3),
             round(pcbnew.ToMM(pd.GetPosition().y), 3))
            for pd in fp.Pads()
        )
        if [w[:3] for w in want] != got:
            raise RuntimeError(f"{ref}: pad positions differ from upstream")
        by_pos = {w[:3]: w[3] for w in want}
        for pd in fp.Pads():
            key = (pd.GetNumber(), round(pcbnew.ToMM(pd.GetPosition().x), 3),
                   round(pcbnew.ToMM(pd.GetPosition().y), 3))
            name = by_pos[key].lstrip("/")
            if not name.startswith("unconnected"):
                pd.SetNet(net(name))

    # controller
    # the back-side flip mirrors top/bottom, 180 deg puts the USB back on top
    nano = place(board, make_nano(), "U1", cfg["nano_x"], NANO_TOP + 16.5, 180)
    set_model(nano, f"{MODELS}/nice_nano_v2.wrl")
    usb_top = min(pd.GetPosition().y for pd in nano.Pads() if pd.GetNumber() in ("1", "24"))
    if usb_top > mm(NANO_TOP + 5):
        raise RuntimeError("nice!nano USB end is not facing the top edge")
    for pd in nano.Pads():
        num = int(pd.GetNumber())
        fn = NANO_PINS[num]
        if fn == "GND":
            pd.SetNet(net("GND"))
        elif fn == "B+":
            pd.SetNet(net("B+"))
        elif fn == "RST":
            pd.SetNet(net("RST"))
        elif num in cfg["nano_nets"]:
            pd.SetNet(net(cfg["nano_nets"][num]))

    # reset button: RST <-> GND
    sw = place(board, load(f"{KLIB}/Button_Switch_SMD.pretty", "SW_SPST_SKQG_WithoutStem"),
               "SW1", *cfg["reset"])
    for pd in sw.Pads():
        pd.SetNet(net("RST" if pd.GetNumber() == "1" else "GND"))

    # power switch: common (2) -> B+, 1 -> battery +, 3 unused
    x, y, rot = cfg["switch"]
    # C&K PCM12SMTR: stocked by EU distributors (the MSK12C02 isn't)
    pw = place(board, load(f"{KLIB}/Button_Switch_SMD.pretty", "SW_SPDT_PCM12"),
               "SW2", x, y, rot)
    for pd in pw.Pads():
        if pd.GetNumber() == "2":
            pd.SetNet(net("B+"))
        elif pd.GetNumber() == "1":
            pd.SetNet(net("BAT+"))

    # battery: pin 1 = +, pin 2 = -
    bt = place(board, load(f"{KLIB}/Connector_JST.pretty", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"),
               "J7", *cfg["jst"])
    for pd in bt.Pads():
        pd.SetNet(net("BAT+" if pd.GetNumber() == "1" else "GND"))

    for i, (hx, hy) in enumerate(cfg["holes"], 1):
        place(board, load(f"{KLIB}/MountingHole.pretty", "MountingHole_3.2mm_M3"),
              f"H{i}", hx, hy, back=False)

    outline(board, *cfg["outline"])
    edge_keepout(board, *cfg["outline"])
    add_preroutes(board, cfg)

    lx, ly = cfg["label"]
    text(board, f"PILLZ SPLIT {side.upper()}", lx, ly, 1.2)
    rx, ry = cfg["reset"]
    text(board, "RST", rx, ry + 3.6, 0.9)
    for pd in bt.Pads():
        p = pd.GetPosition()
        text(board, "+" if pd.GetNumber() == "1" else "-",
             pcbnew.ToMM(p.x), pcbnew.ToMM(p.y) + 3.2, 1.2)
    sx, sy, _ = cfg["switch"]
    text(board, "PWR", sx, sy - 4.0, 0.9)

    out = os.path.join(HERE, side, f"pillz_split_{side}.kicad_pcb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    board.SetFileName(out)
    pcbnew.SaveBoard(out, board)
    print("wrote", out)


if __name__ == "__main__":
    for side, cfg in HALVES.items():
        build(side, cfg)
