"""
PARTIR MATERIALES SOBRECARGADOS
===============================

MAT_BLOCKOUT_FABRIC_LIGHT estaba haciendo de tela, de ceramica, de plastico
blanco Y de pantalla de proyeccion al mismo tiempo. Ninguna textura puede
servir para las cuatro cosas: lo que queda bien en una almohada arruina una
pantalla.

Se reparte por objeto y se crean los materiales que faltaban.

Uso:
  Blender --background ARCHIVO.blend --python split_materials.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import mat, out_path, save

REPARTO = {
    "MAT_BLOCKOUT_CERAMIC": ["MUG_DESK", "MUG_EAST_BODY", "MUG_EAST_HANDLE_TOP",
                             "MUG_EAST_HANDLE_BOTTOM", "MUG_EAST_HANDLE_OUTER"],
    "MAT_BLOCKOUT_PLASTIC_LIGHT": ["MEDIA_BOX_WHITE", "PROJECTOR_BODY",
                                   "RETRO_CONSOLE_01", "DESK_DRAWER_HANDLE_01",
                                   "DESK_DRAWER_HANDLE_02", "DESK_DRAWER_HANDLE_03"],
    "MAT_SCREEN_PROJ": ["SCREEN_SURFACE"],
}

EXTRA = {
    "MAT_BLOCKOUT_PLASTIC_LIGHT": ((0.76, 0.75, 0.73), 0.50),
    "MAT_SCREEN_PROJ": ((0.74, 0.74, 0.73), 0.85),
}


def main():
    from lib_blockout import PALETTE
    PALETTE.update(EXTRA)

    for destino, objetos in REPARTO.items():
        m = mat(destino)
        n = 0
        for nombre in objetos:
            o = bpy.data.objects.get(nombre)
            if not o or o.type != "MESH":
                print("  falta:", nombre)
                continue
            o.data.materials.clear()
            o.data.materials.append(m)
            n += 1
        print("  %-28s <- %d objetos" % (destino, n))

    save(out_path(sys.argv, bpy.data.filepath))


main()
