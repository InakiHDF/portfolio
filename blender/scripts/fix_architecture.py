"""
ARREGLOS DE ARQUITECTURA  (sector "ARCH")
=========================================

1. La pared oeste deja de ser plana: el tramo norte (puerta + escaleras) se
   retranquea 0.35 m. El tramo del setup se queda donde estaba.
2. Baranda de la escalera reconstruida sobre la pendiente, con parantes.
3. Marco de la puerta, y puerta movida a la nueva cara retranqueada.
4. Cama un poco mas grande (1.80 x 2.15 en vez de 1.60 x 2.10).
5. Camara cenital CAM_TOP ortografica, para comparar contra el plano.

Uso:
  Blender --background ENTRADA.blend --python fix_architecture.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import (box, root, col, mat, tag, obj, resize_box,
                          clear_sector, out_path, save)

SECTOR = "ARCH"

# --- geometria de la habitacion -------------------------------------------
X_IN = -4.50          # cara interior de la pared oeste, tramo del setup
X_RECESS = -4.85      # cara interior de la pared oeste, tramo retranqueado
X_OUT = -5.00         # cara exterior de la pared oeste
X_EAST_OUT = 4.65     # cara exterior de la pared este (sin cambios)
Y_SPLIT = 1.10        # donde arranca el retranqueo
Y_N, Y_S = 4.00, -4.00
H = 2.90
WALL_T = 0.15


def rebuild_west_wall():
    outer_w = X_EAST_OUT - X_OUT                    # 9.65
    outer_cx = (X_OUT + X_EAST_OUT) / 2             # -0.175
    outer_d = (Y_N - Y_S) + 2 * WALL_T              # 8.30

    # Losas y paredes norte/sur se estiran hasta la nueva cara exterior.
    resize_box(obj("FLOOR"), (outer_w, outer_d, 0.20), (outer_cx, 0, -0.10))
    resize_box(obj("CEILING"), (outer_w, outer_d, 0.20), (outer_cx, 0, H + 0.10))
    resize_box(obj("WALL_NORTH"), (outer_w, WALL_T, H),
               (outer_cx, Y_N + WALL_T / 2, H / 2))
    resize_box(obj("WALL_SOUTH"), (outer_w, WALL_T, H),
               (outer_cx, Y_S - WALL_T / 2, H / 2))

    # La pared oeste pasa a ser el plano de fondo (el retranqueo).
    resize_box(obj("WALL_WEST"), (WALL_T, outer_d, H),
               ((X_OUT + X_RECESS) / 2, 0, H / 2))
    obj("WALL_WEST")["notes"] = "plano retranqueado: puerta y escaleras"

    # Y el tramo sur se rellena hasta la cara original.
    box("WALL_WEST_INFILL",
        (X_IN - X_RECESS, (Y_SPLIT - Y_S) + WALL_T, H),
        ((X_RECESS + X_IN) / 2, (Y_SPLIT + Y_S - WALL_T) / 2, H / 2),
        col("10_ARCHITECTURE_LOCKED"), "MAT_BLOCKOUT_ARCH", sector=SECTOR,
        props={"asset_id": "wall_west_infill", "asset_type": "architecture",
               "notes": "tramo del setup, adelantado 0.35 m"})

    # Zocalos: el oeste se parte en dos tramos + el retorno de la jamba.
    resize_box(obj("SKIRTING_WEST"), (0.03, Y_SPLIT - Y_S, 0.12),
               (X_IN + 0.015, (Y_SPLIT + Y_S) / 2, 0.06))
    box("SKIRTING_WEST_RECESS", (0.03, Y_N - Y_SPLIT, 0.12),
        (X_RECESS + 0.015, (Y_N + Y_SPLIT) / 2, 0.06),
        col("10_ARCHITECTURE_LOCKED"), "MAT_BLOCKOUT_SKIRTING", sector=SECTOR,
        props={"asset_id": "skirting_west_recess", "asset_type": "architecture"})
    box("SKIRTING_WEST_JAMB", (X_IN - X_RECESS, 0.03, 0.12),
        ((X_RECESS + X_IN) / 2, Y_SPLIT + 0.015, 0.06),
        col("10_ARCHITECTURE_LOCKED"), "MAT_BLOCKOUT_SKIRTING", sector=SECTOR,
        props={"asset_id": "skirting_west_jamb", "asset_type": "architecture"})


def rebuild_railing():
    """La baranda vuelve a apoyar sobre la pendiente de STAIRCASE_01."""
    stair = obj("STAIRCASE_01_ROOT")
    going, rise, run = 0.28, 0.19, 2.80
    slope = math.atan2(rise, going)
    ratio = rise / going
    rail_h = 0.95
    y_local = -0.62

    rail = obj("STAIR_RAILING_PROXY", required=False)
    if rail:
        rail.scale = (1.0, 1.0, 1.0)
        resize_box(rail, (run / math.cos(slope), 0.06, 0.06),
                   (run / 2, y_local, ratio * (run / 2) + rail_h))
        rail.rotation_euler = (0, -slope, 0)

    # Parantes. Debajo del tramo bajo esta la plataforma (z = 0.60).
    plat_top, plat_x_local = 0.60, 0.84
    for i, x in enumerate((0.20, 1.40, 2.60)):
        bottom = plat_top if x < plat_x_local else ratio * x
        top = ratio * x + rail_h
        box("STAIR_POST_%02d" % (i + 1), (0.05, 0.05, top - bottom),
            (x, y_local, (top + bottom) / 2),
            col("10_ARCHITECTURE_LOCKED"), "MAT_BLOCKOUT_METAL",
            parent=stair, sector=SECTOR,
            props={"asset_id": "stair_post_%02d" % (i + 1),
                   "asset_type": "railing"})


def rebuild_door():
    """Puerta reubicada sobre la cara retranqueada, con marco y manija."""
    entrance = obj("ENTRANCE_01_ROOT")
    ex, ey = entrance.location.x, entrance.location.y
    door = obj("DOOR_PROXY")
    door.location.x = (X_RECESS + 0.03) - ex        # pegada a la cara nueva
    plat_top, dw, dh = 0.60, 0.90, 2.05
    door.location.z = plat_top + dh / 2

    frame_x = (X_RECESS + 0.05) - ex
    for i, side in enumerate((-1, 1)):
        box("DOOR_FRAME_%s" % ("SOUTH" if side < 0 else "NORTH"),
            (0.10, 0.06, dh + 0.10), (frame_x, side * (dw / 2 + 0.03), plat_top + (dh + 0.10) / 2),
            col("10_ARCHITECTURE_LOCKED"), "MAT_BLOCKOUT_WOOD",
            parent=entrance, sector=SECTOR,
            props={"asset_id": "door_frame_%d" % i, "asset_type": "door"})
    box("DOOR_FRAME_TOP", (0.10, dw + 0.12, 0.06),
        (frame_x, 0, plat_top + dh + 0.07),
        col("10_ARCHITECTURE_LOCKED"), "MAT_BLOCKOUT_WOOD",
        parent=entrance, sector=SECTOR,
        props={"asset_id": "door_frame_top", "asset_type": "door"})
    box("DOOR_HANDLE", (0.12, 0.04, 0.04),
        (door.location.x + 0.08, 0.34, plat_top + 1.05),
        col("10_ARCHITECTURE_LOCKED"), "MAT_BLOCKOUT_METAL",
        parent=entrance, sector=SECTOR,
        props={"asset_id": "door_handle", "asset_type": "door"})


def resize_bed():
    w, d = 1.80, 2.15
    resize_box(obj("BED_FRAME_PROXY"), (w, d, 0.30), (0, 0, 0.15))
    resize_box(obj("MATTRESS_PROXY"), (w - 0.06, d - 0.10, 0.24), (0, 0, 0.42))
    resize_box(obj("BLANKET_PROXY"), (w + 0.06, d - 0.55, 0.10), (0, 0.25, 0.58))
    for side, x in (("L", -0.42), ("R", 0.42)):
        resize_box(obj("PILLOW_%s_PROXY" % side), (0.68, 0.38, 0.15),
                   (x, -d / 2 + 0.30, 0.615))


def add_top_camera():
    if bpy.data.objects.get("CAM_TOP"):
        return
    data = bpy.data.cameras.new("CAM_TOP_DATA")
    data.type = "ORTHO"
    data.ortho_scale = 9.90
    data.clip_start = 0.10
    data.clip_end = 40.0
    cam = bpy.data.objects.new("CAM_TOP", data)
    cam.location = (-0.175, 0.0, 8.0)
    cam.rotation_euler = (0, 0, 0)     # mira hacia abajo; norte arriba
    col("50_CAMERAS").objects.link(cam)
    tag(cam, SECTOR, {"asset_id": "cam_top", "asset_type": "camera",
                      "status": "approved",
                      "notes": "ortografica, para comparar contra el plano"})


def main():
    removed = clear_sector(SECTOR)
    rebuild_west_wall()
    rebuild_railing()
    rebuild_door()
    resize_bed()
    add_top_camera()
    print("Objetos del sector ARCH reemplazados:", removed)
    save(out_path(sys.argv, bpy.data.filepath))


main()
