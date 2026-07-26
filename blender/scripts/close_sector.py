"""
CERRAR UN SECTOR
================

Marca todos los objetos de un sector con status="approved". A partir de ahi
clear_sector() se niega a borrarlos, asi que volver a correr el script de ese
sector por error no puede destruir tus ajustes manuales.

Uso:
  Blender --background ARCHIVO.blend --python close_sector.py -- SALIDA.blend WEST ARCH
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import save

extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(extra) < 2:
    raise SystemExit("Faltan argumentos: SALIDA.blend SECTOR [SECTOR...]")

destination, sectors = extra[0], extra[1:]

for name in sectors:
    n = 0
    for obj in bpy.data.objects:
        if obj.get("sector") == name:
            obj["status"] = "approved"
            n += 1
    print("Sector %-8s cerrado: %d objeto(s) marcados como approved" % (name, n))

save(destination)
