"""Fija la geometría aprobada antes de volver a hornear la iluminación.

Uso:
  Blender --background ENTRADA.blend --python fix_final_geometry.py -- SALIDA.blend
"""

import os
import sys

import bpy


PHOTO_POSITIONS = {
    "PHOTO_NORTH_01": (1.5509344339370728, -0.02, 1.6272934675216675),
    "PHOTO_NORTH_03": (1.8309345245361328, -0.02, 1.6072934865951538),
    "PHOTO_NORTH_04": (1.6709344387054443, -0.02, 1.3672934770584106),
}


def main():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not extra:
        raise SystemExit("falta SALIDA.blend")

    sheet = bpy.data.objects.get("SHEET_EAST_01")
    if sheet is None:
        raise SystemExit("falta SHEET_EAST_01")
    sheet.location.x = -0.10
    sheet.location.y = 0.48

    for name, location in PHOTO_POSITIONS.items():
        photo = bpy.data.objects.get(name)
        if photo is None:
            raise SystemExit("falta " + name)
        photo.location = location

    middle = bpy.data.objects.get("PHOTO_NORTH_02")
    if middle:
        bpy.data.objects.remove(middle, do_unlink=True)

    bpy.context.scene["geometry_fixed_before_lightmap"] = True
    output = os.path.abspath(extra[0])
    os.makedirs(os.path.dirname(output), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=output)
    print("GEOMETRY_FIXED:", output)


main()
