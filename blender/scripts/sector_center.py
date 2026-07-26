"""
SECTOR CENTRO  (sector "CENTER")
================================

La isla del medio de la habitacion:
  - Alfombra
  - Mesa ratona baja de madera
  - Libros y revistas sobre la mesa, joystick y un aparatito chico
  - Libros y revistas tirados en el piso, sobre la alfombra

Referencias de posicion: la cenital, mapeada como fraccion del ancho de la
habitacion y de la franja util norte-sur, mas el corrimiento al este que le
diste al mueble de audio.

Casi todo va con una rotacion chica en Z. Un objeto suelto alineado al eje
lee como error de modelado; torcido lee como algo que alguien dejo ahi.

Uso:
  Blender --background ARCHIVO.blend --python sector_center.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import box, root, col, clear_sector, out_path, save

SECTOR = "CENTER"

RUG_C = (0.25, 0.45)        # centro de la alfombra
RUG_SIZE = (3.40, 2.80)
TABLE_C = (0.10, 0.30)      # centro de la mesa ratona
TABLE_SIZE = (1.75, 0.75)
TABLE_H = 0.40              # altura de la cara superior

FURN = None
PROPS = None


def rad(d):
    return (0.0, 0.0, math.radians(d))


def build_rug():
    box("RUG_CENTER_01", (RUG_SIZE[0], RUG_SIZE[1], 0.015),
        (RUG_C[0], RUG_C[1], 0.0075), PROPS, "MAT_BLOCKOUT_RUG",
        rotation=rad(0.8), sector=SECTOR,
        props={"asset_id": "rug_center_01", "asset_type": "rug",
               "texture_id": "TEX_RUG_CENTER",
               "reference_group": "centro",
               "notes": "textura pixelada; el borde va en la misma imagen"})


def build_table():
    w, d = TABLE_SIZE
    top_t, leg_t = 0.09, 0.09
    r = root("TABLE_CENTER_01_ROOT", (TABLE_C[0], TABLE_C[1], 0.0), FURN,
             SECTOR, {"asset_id": "table_center_01", "asset_type": "table",
                      "reference_group": "centro"})
    r.rotation_euler = rad(-2.5)

    box("TABLE_CENTER_TOP", (w, d, top_t), (0, 0, TABLE_H - top_t / 2), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "table_center_top", "asset_type": "table"})
    for side in (-1, 1):
        box("TABLE_CENTER_LEG_%s" % ("W" if side < 0 else "E"),
            (leg_t, d - 0.08, TABLE_H - top_t),
            (side * (w / 2 - 0.13), 0, (TABLE_H - top_t) / 2), FURN,
            "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
            props={"asset_id": "table_center_leg", "asset_type": "table"})
    box("TABLE_CENTER_STRETCHER", (w - 0.42, 0.08, 0.07), (0, 0, 0.11), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "table_center_stretcher", "asset_type": "table"})
    return r


def build_table_props(table):
    """Todo lo que esta apoyado sobre la mesa, en coordenadas de la mesa."""
    z = TABLE_H

    # Pila de dos libros en el extremo oeste
    for i, (dx, dy, w, d, h, ang, m) in enumerate((
            (-0.55, 0.02, 0.36, 0.27, 0.035, 4, "MAT_BLOCKOUT_PAPER"),
            (-0.53, -0.01, 0.32, 0.24, 0.030, -6, "MAT_BLOCKOUT_ACCENT_ORANGE"))):
        box("BOOK_TABLE_%02d" % (i + 1), (w, d, h), (dx, dy, z + 0.018 + i * 0.033),
            PROPS, m, rotation=rad(ang), parent=table, sector=SECTOR,
            props={"asset_id": "book_table_%02d" % (i + 1),
                   "asset_type": "books",
                   "texture_id": "TEX_BOOK_TABLE_%02d" % (i + 1)})

    # Revista abierta en el extremo este
    box("MAGAZINE_TABLE_01", (0.34, 0.25, 0.014), (0.52, 0.05, z + 0.007),
        PROPS, "MAT_BLOCKOUT_PAPER", rotation=rad(-9), parent=table,
        sector=SECTOR,
        props={"asset_id": "magazine_table_01", "asset_type": "paper",
               "texture_id": "TEX_MAGAZINE_TABLE_01"})

    # Joystick: cuerpo mas dos mangos abiertos
    jx, jy = 0.02, -0.06
    box("GAMEPAD_TABLE_BODY", (0.17, 0.10, 0.045), (jx, jy, z + 0.023), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", rotation=rad(12), parent=table,
        sector=SECTOR,
        props={"asset_id": "gamepad_table", "asset_type": "peripheral"})
    for side, ang in ((-1, 32), (1, -8)):
        box("GAMEPAD_TABLE_GRIP_%s" % ("L" if side < 0 else "R"),
            (0.07, 0.13, 0.042), (jx + side * 0.10, jy - 0.04, z + 0.021),
            PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", rotation=rad(ang),
            parent=table, sector=SECTOR,
            props={"asset_id": "gamepad_grip", "asset_type": "peripheral"})

    # Aparatito chico: control remoto o cartucho
    box("CARTRIDGE_TABLE", (0.14, 0.08, 0.022), (0.28, -0.20, z + 0.011),
        PROPS, "MAT_BLOCKOUT_FABRIC", rotation=rad(21), parent=table,
        sector=SECTOR,
        props={"asset_id": "cartridge_table", "asset_type": "decoration"})


def build_floor_props():
    """Tirado en el piso, sobre la alfombra. Z apoyado sobre la alfombra."""
    z0 = 0.015

    # Revista abierta: dos paginas con una separacion minima
    for i, (dx, ang) in enumerate(((-0.115, 3), (0.115, -3))):
        box("MAGAZINE_FLOOR_OPEN_%02d" % (i + 1), (0.23, 0.30, 0.008),
            (-1.06 + dx, 0.62, z0 + 0.004), PROPS, "MAT_BLOCKOUT_PAPER",
            rotation=rad(-14 + ang), sector=SECTOR,
            props={"asset_id": "magazine_floor_open_%02d" % (i + 1),
                   "asset_type": "paper",
                   "texture_id": "TEX_MAGAZINE_FLOOR_%02d" % (i + 1),
                   "reference_group": "centro"})

    # Pila de tres libros al este de la mesa
    stack = ((0.40, 0.30, 0.04, 6, "MAT_BLOCKOUT_FABRIC"),
             (0.36, 0.28, 0.035, -9, "MAT_BLOCKOUT_PAPER"),
             (0.30, 0.24, 0.030, 3, "MAT_BLOCKOUT_ACCENT_ORANGE"))
    zz = z0
    for i, (w, d, h, ang, m) in enumerate(stack):
        box("BOOK_FLOOR_STACK_%02d" % (i + 1), (w, d, h),
            (1.38, 0.88, zz + h / 2), PROPS, m, rotation=rad(ang),
            sector=SECTOR,
            props={"asset_id": "book_floor_stack_%02d" % (i + 1),
                   "asset_type": "books",
                   "texture_id": "TEX_BOOK_FLOOR_%02d" % (i + 1),
                   "reference_group": "centro"})
        zz += h

    # Revista suelta al sur de la mesa
    box("MAGAZINE_FLOOR_01", (0.32, 0.24, 0.012), (0.30, -0.52, z0 + 0.006),
        PROPS, "MAT_BLOCKOUT_PAPER", rotation=rad(26), sector=SECTOR,
        props={"asset_id": "magazine_floor_01", "asset_type": "paper",
               "texture_id": "TEX_MAGAZINE_FLOOR_03",
               "reference_group": "centro"})

    # Segundo joystick, tirado en la alfombra
    box("GAMEPAD_FLOOR_BODY", (0.17, 0.10, 0.045), (-0.50, -0.30, z0 + 0.023),
        PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", rotation=rad(-38), sector=SECTOR,
        props={"asset_id": "gamepad_floor", "asset_type": "peripheral",
               "reference_group": "centro"})
    for side, ang in ((-1, -18), (1, -58)):
        box("GAMEPAD_FLOOR_GRIP_%s" % ("L" if side < 0 else "R"),
            (0.07, 0.13, 0.042),
            (-0.50 + side * 0.09, -0.36 + side * 0.02, z0 + 0.021), PROPS,
            "MAT_BLOCKOUT_PLASTIC_BLACK", rotation=rad(ang), sector=SECTOR,
            props={"asset_id": "gamepad_floor_grip",
                   "asset_type": "peripheral", "reference_group": "centro"})


def main():
    global FURN, PROPS
    FURN = col("20_FURNITURE")
    PROPS = col("30_PROPS")

    print("Objetos CENTER reemplazados:", clear_sector(SECTOR))
    build_rug()
    table = build_table()
    build_table_props(table)
    build_floor_props()
    save(out_path(sys.argv, bpy.data.filepath))


main()
