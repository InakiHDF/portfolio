"""
SECTOR ESTE  (sector "EAST")  — lo que ve CAM_RIGHT
===================================================

La mesa de trabajo de madera contra la pared este, la silla, y todo lo que hay
sobre la mesa. Incluye ademas el bolso arriba de la cama, que es lo unico que
faltaba del lado sur.

La pared este queda lisa a proposito: ni en Right.png ni en la cenital hay
nada colgado.

Sin rotaciones en Z: en la tanda anterior las sacaste, asi que todo va
alineado al eje.

Uso:
  Blender --background ARCHIVO.blend --python sector_east.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import box, root, col, obj, clear_sector, out_path, save

SECTOR = "EAST"

# Mesa: contra la pared este (cara interior en x=4.50), 0.15 de luz.
TABLE_C = (3.80, -1.15)     # centro en planta
TABLE_SIZE = (1.10, 2.75)   # profundidad (X) x largo (Y)
TABLE_H = 0.88              # cara superior
CHAIR_C = (3.05, -1.15)

FURN = None
PROPS = None


def build_table():
    w, d = TABLE_SIZE
    top_t, leg = 0.08, 0.10
    r = root("TABLE_EAST_01_ROOT", (TABLE_C[0], TABLE_C[1], 0.0), FURN, SECTOR,
             {"asset_id": "table_east_01", "asset_type": "table",
              "reference_group": "este"})

    box("TABLE_EAST_TOP", (w, d, top_t), (0, 0, TABLE_H - top_t / 2), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "table_east_top", "asset_type": "table"})
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("TABLE_EAST_LEG_%s%s" % ("W" if sx < 0 else "E",
                                         "S" if sy < 0 else "N"),
                (leg, leg, TABLE_H - top_t),
                (sx * (w / 2 - leg), sy * (d / 2 - leg * 1.5),
                 (TABLE_H - top_t) / 2), FURN, "MAT_BLOCKOUT_WOOD",
                parent=r, sector=SECTOR,
                props={"asset_id": "table_east_leg", "asset_type": "table"})
    for sy in (-1, 1):
        box("TABLE_EAST_RAIL_%s" % ("S" if sy < 0 else "N"),
            (w - leg * 2.4, 0.06, 0.09),
            (0, sy * (d / 2 - leg * 1.5), TABLE_H - top_t - 0.10), FURN,
            "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
            props={"asset_id": "table_east_rail", "asset_type": "table"})
    return r


def build_chair():
    r = root("CHAIR_EAST_01_ROOT", (CHAIR_C[0], CHAIR_C[1], 0.0), FURN, SECTOR,
             {"asset_id": "chair_east_01", "asset_type": "chair",
              "reference_group": "este",
              "notes": "mira al este, hacia la mesa"})
    seat_h, seat = 0.50, 0.52

    box("CHAIR_EAST_SEAT", (seat, seat, 0.08), (0, 0, seat_h - 0.04), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "chair_east_seat", "asset_type": "chair"})
    # El respaldo tiene que asomar bien por encima de la tapa (0.88).
    box("CHAIR_EAST_BACK", (0.07, seat - 0.04, 0.62), (-0.225, 0, 0.85), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "chair_east_back", "asset_type": "chair"})
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("CHAIR_EAST_LEG_%s%s" % ("W" if sx < 0 else "E",
                                         "S" if sy < 0 else "N"),
                (0.07, 0.07, seat_h - 0.08),
                (sx * 0.21, sy * 0.21, (seat_h - 0.08) / 2), FURN,
                "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
                props={"asset_id": "chair_east_leg", "asset_type": "chair"})


def build_table_props(table):
    """Sobre la tabla. Coordenadas locales de TABLE_EAST_01_ROOT."""
    z = TABLE_H

    # Lampara articulada en el extremo norte
    lamp = ((0.20, 0.20, 0.035, 0.0175, "MAT_BLOCKOUT_PLASTIC_BLACK", "BASE"),
            (0.05, 0.05, 0.46, 0.265, "MAT_BLOCKOUT_PLASTIC_BLACK", "ARM_A"))
    for w, d, h, dz, m, name in lamp:
        box("LAMP_EAST_%s" % name, (w, d, h), (0.30, 1.10, z + dz), PROPS, m,
            parent=table, sector=SECTOR,
            props={"asset_id": "lamp_east_%s" % name.lower(),
                   "asset_type": "lamp"})
    box("LAMP_EAST_ARM_B", (0.05, 0.38, 0.05), (0.30, 0.93, z + 0.51), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=table, sector=SECTOR,
        props={"asset_id": "lamp_east_arm_b", "asset_type": "lamp"})
    box("LAMP_EAST_HEAD", (0.15, 0.15, 0.14), (0.30, 0.76, z + 0.44), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=table, sector=SECTOR,
        props={"asset_id": "lamp_east_head", "asset_type": "lamp"})
    box("LAMP_EAST_BULB", (0.11, 0.11, 0.01), (0.30, 0.76, z + 0.375), PROPS,
        "MAT_BLOCKOUT_EMISSIVE", parent=table, sector=SECTOR,
        props={"asset_id": "lamp_east_bulb", "asset_type": "lamp",
               "notes": "aca va LIGHT_TABLE_EAST en la fase 7"})

    # Vaso con lapices
    box("PENCIL_CUP", (0.11, 0.11, 0.13), (0.10, 0.86, z + 0.065), PROPS,
        "MAT_BLOCKOUT_CERAMIC", parent=table, sector=SECTOR,
        props={"asset_id": "pencil_cup", "asset_type": "decoration"})
    for i, (dx, dy, h) in enumerate(((-0.02, 0.0, 0.21), (0.02, 0.02, 0.18),
                                     (0.0, -0.03, 0.23), (0.03, -0.01, 0.19))):
        box("PENCIL_%02d" % (i + 1), (0.014, 0.014, h),
            (0.10 + dx, 0.86 + dy, z + 0.05 + h / 2), PROPS,
            "MAT_BLOCKOUT_ACCENT_ORANGE" if i % 2 else "MAT_BLOCKOUT_WOOD_LIGHT",
            parent=table, sector=SECTOR,
            props={"asset_id": "pencil_%02d" % (i + 1),
                   "asset_type": "decoration"})

    # Estuche chico oscuro, hermano del bolso de la cama
    box("CASE_TABLE_EAST", (0.24, 0.17, 0.10), (-0.24, 0.62, z + 0.05), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=table, sector=SECTOR,
        props={"asset_id": "case_table_east", "asset_type": "decoration"})
    box("CASE_TABLE_EAST_TRIM", (0.25, 0.18, 0.015), (-0.24, 0.62, z + 0.062),
        PROPS, "MAT_BLOCKOUT_ACCENT_ORANGE", parent=table, sector=SECTOR,
        props={"asset_id": "case_table_east_trim", "asset_type": "decoration"})

    # Planos y hojas desparramados. (dx, dy, ancho, largo, espesor)
    sheets = [(-0.16, 0.24, 0.30, 0.42, 0.006),
              (0.20, 0.16, 0.28, 0.40, 0.004),
              (-0.22, -0.16, 0.32, 0.44, 0.008),
              (0.18, -0.30, 0.26, 0.36, 0.005),
              (-0.10, -0.62, 0.30, 0.42, 0.010),
              (0.22, -0.72, 0.22, 0.30, 0.004),
              (-0.26, -1.00, 0.28, 0.38, 0.006)]
    for i, (dx, dy, w, d, t) in enumerate(sheets):
        box("SHEET_EAST_%02d" % (i + 1), (w, d, t), (dx, dy, z + t / 2), PROPS,
            "MAT_BLOCKOUT_PAPER", parent=table, sector=SECTOR,
            props={"asset_id": "sheet_east_%02d" % (i + 1),
                   "asset_type": "paper",
                   "texture_id": "TEX_SHEET_EAST_%02d" % (i + 1),
                   "notes": "plano / dibujo tecnico"})

    # Cuaderno y cuenco chico en el extremo sur
    box("NOTEBOOK_EAST", (0.24, 0.32, 0.035), (0.24, -1.06, z + 0.018), PROPS,
        "MAT_BLOCKOUT_FABRIC", parent=table, sector=SECTOR,
        props={"asset_id": "notebook_east", "asset_type": "books",
               "texture_id": "TEX_NOTEBOOK_EAST"})
    box("BOWL_EAST", (0.17, 0.17, 0.09), (-0.28, -1.18, z + 0.045), PROPS,
        "MAT_BLOCKOUT_CERAMIC", parent=table, sector=SECTOR,
        props={"asset_id": "bowl_east", "asset_type": "decoration"})


def build_bed_bag():
    """Bolso rigido arriba de la cama, colgado de BED_01_ROOT para que lo siga."""
    bed = obj("BED_01_ROOT")
    blanket = obj("BLANKET_PROXY")
    top = blanket.matrix_world.translation.z + blanket.dimensions.z / 2

    cx, cy = 0.60, -2.85
    w, d, h = 0.48, 0.68, 0.24

    parts = [
        ("BAG_BED_BODY", (w, d, h), (cx, cy, top + h / 2),
         "MAT_BLOCKOUT_PLASTIC_BLACK", "bolso"),
        ("BAG_BED_SEAM", (w + 0.02, d + 0.02, 0.03), (cx, cy, top + h * 0.62),
         "MAT_BLOCKOUT_ACCENT_ORANGE", "cierre"),
        ("BAG_BED_HANDLE", (0.07, 0.22, 0.05), (cx - w / 2 - 0.02, cy, top + h * 0.55),
         "MAT_BLOCKOUT_PLASTIC_BLACK", "manija"),
        ("BAG_BED_LATCH_S", (0.05, 0.07, 0.06), (cx + w / 2 + 0.01, cy - 0.20, top + h * 0.62),
         "MAT_BLOCKOUT_ACCENT_ORANGE", "traba"),
        ("BAG_BED_LATCH_N", (0.05, 0.07, 0.06), (cx + w / 2 + 0.01, cy + 0.20, top + h * 0.62),
         "MAT_BLOCKOUT_ACCENT_ORANGE", "traba"),
    ]
    for name, size, loc, material, note in parts:
        part = box(name, size, loc, PROPS, material, sector=SECTOR,
                   props={"asset_id": name.lower(), "asset_type": "bag",
                          "reference_group": "cama", "notes": note})
        part.parent = bed
        part.matrix_parent_inverse = bed.matrix_world.inverted()


def main():
    global FURN, PROPS
    FURN = col("20_FURNITURE")
    PROPS = col("30_PROPS")

    print("Objetos EAST reemplazados:", clear_sector(SECTOR))
    table = build_table()
    build_chair()
    build_table_props(table)
    build_bed_bag()
    save(out_path(sys.argv, bpy.data.filepath))


main()
