"""
TAPADO DEL HUECO OESTE + CONTINUACION DE LA ESCALERA   (sector "ARCH2")
======================================================================

1. Tapa el vacio que quedo detras de WALL_WEST_INFILL despues de moverlo
   0.4645 m hacia +X. Se agrega un bloque nuevo; el infill no se toca.
2. Corrige el zocalo de la jamba, que quedo flotando en ese hueco.
3. Continua la escalera desde STAIR_STEP_09 con el mismo paso: 5 escalones
   nuevos (10 a 14), misma huella 0.28 y misma contrahuella 0.19.
4. El escalon 15 ya no es escalon: es la pared que sigue hasta la pared este,
   de piso a techo, con el fondo que da la propia escalera (1.30 m).

No modifica nada de lo que ya ajustaste a mano.

Uso:
  Blender --background ARCHIVO.blend --python fix_west_gap_and_stairs.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import box, col, obj, resize_box, clear_sector, out_path, save

SECTOR = "ARCH2"
ARCH = None

# --- lo que dejo el usuario, medido del archivo ----------------------------
X_RECESS_FACE = -4.85     # cara interior de WALL_WEST (el plano de fondo)
GOING, RISE = 0.28, 0.19  # huella y contrahuella de la escalera existente
LAST_STEP = 9             # ultimo escalon que existe hoy
NEW_STEPS = 5             # escalones nuevos: 10 a 14
STAIR_DEPTH = 1.30        # fondo de la escalera = fondo de la pared nueva
H = 2.90                  # altura libre
X_EAST_OUT = 4.65         # cara exterior de la pared este


def fill_west_gap():
    """El infill se movio +0.4645 en X y dejo aire atras. Se rellena."""
    infill = obj("WALL_WEST_INFILL")
    back_face = infill.location.x - infill.dimensions.x / 2
    width = back_face - X_RECESS_FACE
    if width <= 0.001:
        print("No hay hueco atras del infill; nada que tapar.")
        return
    box("WALL_WEST_GAP_FILL", (width, infill.dimensions.y, H),
        ((X_RECESS_FACE + back_face) / 2, infill.location.y, H / 2),
        ARCH, "MAT_BLOCKOUT_ARCH", sector=SECTOR,
        props={"asset_id": "wall_west_gap_fill", "asset_type": "architecture",
               "notes": "rellena el vacio detras del infill desplazado"})
    print("Hueco oeste tapado: %.4f m de profundidad" % width)

    # El zocalo de la jamba tiene que llegar hasta la cara nueva del infill.
    jamb = obj("SKIRTING_WEST_JAMB", required=False)
    if jamb:
        front_face = infill.location.x + infill.dimensions.x / 2
        resize_box(jamb, (front_face - X_RECESS_FACE, 0.03, 0.12),
                   ((X_RECESS_FACE + front_face) / 2, jamb.location.y, 0.06))


def extend_stairs():
    """Sigue la serie de escalones y cierra con la pared hasta el este."""
    stair = obj("STAIRCASE_01_ROOT")
    last = obj("STAIR_STEP_%02d" % LAST_STEP)
    x0, h0 = last.location.x, last.dimensions.z
    width = last.dimensions.y

    for i in range(1, NEW_STEPS + 1):
        n = LAST_STEP + i
        h = h0 + RISE * i
        box("STAIR_STEP_%02d" % n, (GOING, width, h),
            (x0 + GOING * i, last.location.y, h / 2),
            ARCH, "MAT_BLOCKOUT_STAIR", parent=stair, sector=SECTOR,
            props={"asset_id": "stair_step_%02d" % n,
                   "asset_type": "architecture"})

    # Donde caeria el escalon 15 arranca la pared, de piso a techo.
    wall_x0 = stair.location.x + x0 + GOING * (NEW_STEPS + 0.5)
    y_face = stair.location.y + last.location.y - width / 2
    box("STAIR_WALL_NORTH", (X_EAST_OUT - wall_x0, STAIR_DEPTH, H),
        ((wall_x0 + X_EAST_OUT) / 2, y_face + STAIR_DEPTH / 2, H / 2),
        ARCH, "MAT_BLOCKOUT_ARCH", sector=SECTOR,
        props={"asset_id": "stair_wall_north", "asset_type": "architecture",
               "notes": "continua la escalera como pared hasta la pared este; "
                        "adelanta el limite norte a y=%.2f" % y_face})
    box("SKIRTING_STAIRWALL", (X_EAST_OUT - 0.15 - wall_x0, 0.03, 0.12),
        ((wall_x0 + X_EAST_OUT - 0.15) / 2, y_face - 0.015, 0.06),
        ARCH, "MAT_BLOCKOUT_SKIRTING", sector=SECTOR,
        props={"asset_id": "skirting_stairwall", "asset_type": "architecture"})

    print("Escalones nuevos: %d (hasta STAIR_STEP_%02d)"
          % (NEW_STEPS, LAST_STEP + NEW_STEPS))
    print("Pared nueva desde x=%.3f hasta x=%.2f, cara sur en y=%.2f"
          % (wall_x0, X_EAST_OUT, y_face))


def main():
    global ARCH
    ARCH = col("10_ARCHITECTURE_LOCKED")
    print("Objetos ARCH2 reemplazados:", clear_sector(SECTOR))
    fill_west_gap()
    extend_stairs()
    save(out_path(sys.argv, bpy.data.filepath))


main()
