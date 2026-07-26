"""
DARLE VIDA A LA MESA ESTE  (sector "EAST2")
===========================================

Que hace:

1. Mueve NOTEBOOK_EAST enfrente de la silla y lo deja cerrado, con el lomo
   al norte. Reserva libre la franja al norte del cuaderno para que la tapa
   pueda abrirse hacia ese lado sin chocar con nada.
2. Reacomoda las hojas: tamanos distintos, alturas escalonadas y un giro
   propio para cada una. Una mesa donde se escribe no tiene nada paralelo.
3. Agrega lapicera suelta, taza de cafe, regla, dos rollos de planos, una
   pila de hojas, un bollo de papel, goma y tacho de basura abajo con otro
   bollo al lado.

Que NO hace: tocar nada que hayas movido vos. Antes de mover un objeto
compara su posicion contra la que dejo sector_east.py; si no coincide,
lo saltea y lo informa.

Uso:
  Blender --background ARCHIVO.blend --python enrich_table_east.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import box, col, obj, resize_box, clear_sector, out_path, save

SECTOR = "EAST2"
TOL = 0.006        # tolerancia para considerar que un objeto no se movio
Z_TOP = 0.88       # cara superior de la mesa, en coordenadas de la mesa

PROPS = None
TABLE = None

# Posiciones locales que dejo sector_east.py. Si no coinciden, el objeto se
# movio a mano y no se toca.
BASELINE = {
    "NOTEBOOK_EAST": (0.24, -1.06),
    "SHEET_EAST_01": (-0.16, 0.24),
    "SHEET_EAST_02": (0.20, 0.16),
    "SHEET_EAST_03": (-0.22, -0.16),
    "SHEET_EAST_04": (0.18, -0.30),
    "SHEET_EAST_05": (-0.10, -0.62),
    "SHEET_EAST_06": (0.22, -0.72),
    "SHEET_EAST_07": (-0.26, -1.00),
}

# Donde va cada hoja ahora: (x, y, ancho, largo, espesor, giro en grados).
# Ninguna comparte angulo ni tamano con otra.
SHEETS = {
    "SHEET_EAST_01": (0.08, 0.44, 0.30, 0.42, 0.006, 14),
    "SHEET_EAST_02": (0.30, 0.16, 0.26, 0.36, 0.004, -9),
    "SHEET_EAST_03": (-0.30, -0.52, 0.34, 0.46, 0.008, 7),
    "SHEET_EAST_04": (0.00, -0.34, 0.22, 0.30, 0.005, -21),
    "SHEET_EAST_05": (-0.16, -0.86, 0.30, 0.40, 0.010, 16),
    "SHEET_EAST_06": (0.28, -0.70, 0.19, 0.26, 0.004, 31),
    "SHEET_EAST_07": (0.06, -1.10, 0.26, 0.36, 0.006, -12),
}

# Enfrente de la silla. El cuaderno abre hacia el norte (+Y local).
NOTEBOOK = (-0.28, 0.058)
NOTEBOOK_SIZE = (0.30, 0.22, 0.028)
OPEN_CLEARANCE = 0.24


def untouched(name):
    """Devuelve el objeto solo si sigue donde lo dejo un script.

    Acepta dos posiciones validas: la que dejo sector_east.py y la que deja
    este mismo script. Asi se puede volver a correr sin que la segunda
    corrida confunda su propio resultado con una edicion manual tuya."""
    o = bpy.data.objects.get(name)
    if o is None:
        print("  FALTA", name)
        return None
    valid = [BASELINE[name]]
    if name in SHEETS:
        valid.append(SHEETS[name][:2])
    if name == "NOTEBOOK_EAST":
        valid.append(NOTEBOOK)
    for bx, by in valid:
        if abs(o.location.x - bx) <= TOL and abs(o.location.y - by) <= TOL:
            return o
    print("  SALTEADO (lo moviste vos): %-16s local=(%.3f, %.3f)"
          % (name, o.location.x, o.location.y))
    return None


def rad(d):
    return (0.0, 0.0, math.radians(d))


def place_notebook():
    nb = bpy.data.objects.get("NOTEBOOK_EAST")
    if nb is None:
        print("  FALTA NOTEBOOK_EAST")
        return
    if untouched("NOTEBOOK_EAST"):
        w, d, t = NOTEBOOK_SIZE
        resize_box(nb, (w, d, t), (NOTEBOOK[0], NOTEBOOK[1], Z_TOP + t / 2))
        nb["notes"] = ("cerrado, lomo al norte; libre %.2f m al norte para "
                       "abrir la tapa" % OPEN_CLEARANCE)

    # El elastico y el senalador se colocan contra la posicion REAL del
    # cuaderno, lo hayas movido vos o no.
    x, y = nb.location.x, nb.location.y
    w, d, t = nb.dimensions

    box("NOTEBOOK_EAST_BAND", (w - 0.02, 0.016, t + 0.006),
        (x, y - d / 2 + 0.045, Z_TOP + t / 2), PROPS,
        "MAT_BLOCKOUT_ACCENT_ORANGE", parent=TABLE, sector=SECTOR,
        props={"asset_id": "notebook_east_band", "asset_type": "books"})
    box("NOTEBOOK_EAST_RIBBON", (0.035, 0.07, 0.003),
        (x + 0.09, y - d / 2 - 0.02, Z_TOP + 0.0015),
        PROPS, "MAT_BLOCKOUT_ACCENT_ORANGE", parent=TABLE, sector=SECTOR,
        props={"asset_id": "notebook_east_ribbon", "asset_type": "books"})


def place_sheets():
    for i, (name, (x, y, w, d, t, ang)) in enumerate(sorted(SHEETS.items())):
        sheet = untouched(name)
        if not sheet:
            continue
        # Altura escalonada: dos hojas nunca quedan coplanares.
        z = Z_TOP + 0.002 * i + t / 2
        resize_box(sheet, (w, d, t), (x, y, z))
        sheet.rotation_euler = rad(ang)


def add_pen():
    box("PEN_EAST_BODY", (0.15, 0.013, 0.013), (-0.30, -0.16, Z_TOP + 0.0065),
        PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", rotation=rad(24), parent=TABLE,
        sector=SECTOR,
        props={"asset_id": "pen_east", "asset_type": "decoration",
               "notes": "suelta al costado del cuaderno"})
    box("PEN_EAST_CAP", (0.04, 0.015, 0.015), (-0.235, -0.132, Z_TOP + 0.0075),
        PROPS, "MAT_BLOCKOUT_ACCENT_ORANGE", rotation=rad(24), parent=TABLE,
        sector=SECTOR,
        props={"asset_id": "pen_east_cap", "asset_type": "decoration"})


def add_mug():
    mx, my = 0.14, -0.10
    box("MUG_EAST_BODY", (0.085, 0.085, 0.105), (mx, my, Z_TOP + 0.0525),
        PROPS, "MAT_BLOCKOUT_FABRIC_LIGHT", parent=TABLE, sector=SECTOR,
        props={"asset_id": "mug_east", "asset_type": "decoration"})
    # Manija en C hacia el sur: apuntando al este quedaba escondida detras
    # del cuerpo y la taza leia como un cubo.
    handle = (("TOP", (0.018, 0.048, 0.014), (mx, my - 0.055, Z_TOP + 0.088)),
              ("BOTTOM", (0.018, 0.048, 0.014), (mx, my - 0.055, Z_TOP + 0.028)),
              ("OUTER", (0.018, 0.014, 0.074), (mx, my - 0.075, Z_TOP + 0.058)))
    for name, size, loc in handle:
        box("MUG_EAST_HANDLE_%s" % name, size, loc, PROPS,
            "MAT_BLOCKOUT_FABRIC_LIGHT", parent=TABLE, sector=SECTOR,
            props={"asset_id": "mug_east_handle", "asset_type": "decoration"})
    box("MUG_EAST_COFFEE", (0.07, 0.07, 0.004), (mx, my, Z_TOP + 0.093),
        PROPS, "MAT_BLOCKOUT_WOOD", parent=TABLE, sector=SECTOR,
        props={"asset_id": "mug_east_coffee", "asset_type": "decoration"})


def add_ruler_and_eraser():
    box("RULER_EAST", (0.035, 0.34, 0.005), (-0.02, -0.44, Z_TOP + 0.020),
        PROPS, "MAT_BLOCKOUT_WOOD_LIGHT", rotation=rad(-38), parent=TABLE,
        sector=SECTOR,
        props={"asset_id": "ruler_east", "asset_type": "decoration"})
    box("ERASER_EAST", (0.045, 0.026, 0.018), (-0.12, -0.24, Z_TOP + 0.009),
        PROPS, "MAT_BLOCKOUT_FABRIC", rotation=rad(-11), parent=TABLE,
        sector=SECTOR,
        props={"asset_id": "eraser_east", "asset_type": "decoration"})


def add_rolls():
    """Dos rollos de planos en el fondo, contra el canto norte."""
    for i, (x, y, dia, length, ang) in enumerate(((0.34, 1.02, 0.09, 0.55, 4),
                                                  (0.43, 0.96, 0.07, 0.42, -6))):
        box("ROLL_PLAN_%02d" % (i + 1), (dia, length, dia),
            (x, y, Z_TOP + dia / 2), PROPS, "MAT_BLOCKOUT_PAPER",
            rotation=rad(ang), parent=TABLE, sector=SECTOR,
            props={"asset_id": "roll_plan_%02d" % (i + 1),
                   "asset_type": "paper", "notes": "plano enrollado"})


def add_paper_stack():
    """Pila de hojas: cada una corrida y girada un poco respecto de la de abajo."""
    layers = ((0.22, -0.94, 0.28, 0.38, 0.012, 5),
              (0.235, -0.925, 0.26, 0.36, 0.010, -8),
              (0.215, -0.95, 0.24, 0.34, 0.008, 13))
    z = Z_TOP
    for i, (x, y, w, d, t, ang) in enumerate(layers):
        box("PAPER_STACK_EAST_%02d" % (i + 1), (w, d, t), (x, y, z + t / 2),
            PROPS, "MAT_BLOCKOUT_PAPER", rotation=rad(ang), parent=TABLE,
            sector=SECTOR,
            props={"asset_id": "paper_stack_east_%02d" % (i + 1),
                   "asset_type": "paper"})
        z += t


def crumpled(name, center, scale, parent, sector):
    """Un bollo de papel = dos cajas cruzadas. Una sola lee como cubo."""
    parts = (((0.075, 0.062, 0.058), 22), ((0.058, 0.072, 0.052), -37))
    for i, (size, ang) in enumerate(parts):
        box("%s_%02d" % (name, i + 1),
            tuple(s * scale for s in size),
            (center[0] + (0.006 if i else 0), center[1] - (0.005 if i else 0),
             center[2]), PROPS, "MAT_BLOCKOUT_PAPER", rotation=rad(ang),
            parent=parent, sector=sector,
            props={"asset_id": name.lower(), "asset_type": "paper"})


def add_trash_bin():
    """Tacho debajo de la mesa, entre las patas del lado sur."""
    bx, by, h = 3.95, -1.30, 0.44
    props_col = PROPS
    box("TRASH_BIN_BODY", (0.29, 0.29, h), (bx, by, h / 2), props_col,
        "MAT_BLOCKOUT_METAL", sector=SECTOR,
        props={"asset_id": "trash_bin_east", "asset_type": "bin",
               "reference_group": "este"})
    box("TRASH_BIN_RIM", (0.32, 0.32, 0.03), (bx, by, h - 0.005), props_col,
        "MAT_BLOCKOUT_PLASTIC_BLACK", sector=SECTOR,
        props={"asset_id": "trash_bin_rim", "asset_type": "bin"})
    # Un bollo asomando del tacho y otro que no entro
    crumpled("TRASH_BALL_IN", (bx - 0.04, by + 0.03, h + 0.01), 1.0,
             None, SECTOR)
    crumpled("TRASH_BALL_OUT", (bx - 0.30, by - 0.16, 0.035), 0.9,
             None, SECTOR)


def main():
    global PROPS, TABLE
    PROPS = col("30_PROPS")
    TABLE = obj("TABLE_EAST_01_ROOT")

    print("Objetos EAST2 reemplazados:", clear_sector(SECTOR))
    place_notebook()
    place_sheets()
    add_pen()
    add_mug()
    add_ruler_and_eraser()
    add_rolls()
    add_paper_stack()
    crumpled("PAPER_BALL_TABLE", (0.36, -0.44, Z_TOP + 0.03), 0.85, TABLE,
             SECTOR)
    add_trash_bin()
    save(out_path(sys.argv, bpy.data.filepath))


main()
