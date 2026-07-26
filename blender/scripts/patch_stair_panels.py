"""
PANELES QUE FALTABAN EN LA ESCALERA  (sector "NORTH2")
======================================================

Cuando genere los paneles negros salte los dos escalones mas bajos. Este
script recorre TODOS los STAIR_STEP_* y crea el panel de los que no lo tengan,
con la misma regla que los existentes: 0.03 de espesor, 0.04 mas bajo que el
escalon, pegado a la cara sur y parentado a STAIR_PANEL_ROOT.

Es idempotente: si ya existen todos, no hace nada.

Uso:
  Blender --background ARCHIVO.blend --python patch_stair_panels.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix
from lib_blockout import box, col, obj, clear_sector, out_path, save

SECTOR = "NORTH2"
THICKNESS = 0.03
CLEARANCE = 0.04


def main():
    clear_sector(SECTOR)
    panel_root = obj("STAIR_PANEL_ROOT")
    props_col = col("30_PROPS")

    steps = [o for o in bpy.data.objects if o.name.startswith("STAIR_STEP_")]
    created = []

    for step in sorted(steps, key=lambda o: o.matrix_world.translation.x):
        suffix = step.name.rsplit("_", 1)[-1]
        if bpy.data.objects.get("STAIR_PANEL_" + suffix):
            continue
        h = step.dimensions.z - CLEARANCE
        if h <= 0.10:
            continue

        w = step.matrix_world.translation
        # Cara sur del escalon, mas medio espesor hacia afuera.
        panel = box("STAIR_PANEL_" + suffix,
                    (step.dimensions.x, THICKNESS, h),
                    (w.x, w.y - step.dimensions.y / 2 - THICKNESS / 2, h / 2),
                    props_col, "MAT_BLOCKOUT_PLASTIC_BLACK", sector=SECTOR,
                    props={"asset_id": "stair_panel_" + suffix,
                           "asset_type": "panel",
                           "notes": "textura calada / celosia"})
        # Se cuelga del mismo padre conservando la posicion en mundo.
        panel.parent = panel_root
        panel.matrix_parent_inverse = panel_root.matrix_world.inverted()
        created.append(panel.name)

    print("Paneles creados:", ", ".join(created) if created else "ninguno")
    save(out_path(sys.argv, bpy.data.filepath))


main()
