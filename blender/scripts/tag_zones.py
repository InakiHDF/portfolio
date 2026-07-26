"""
MARCAR LAS ZONAS CLICABLES  (no crea ni borra nada)
===================================================

Le pone a ciertos objetos una propiedad `zona` y otra `zona_titulo`.

Por que aca y no en el javascript: la propiedad viaja dentro del GLB como
userData del objeto. Si la lista viviera en el codigo de la pagina, habria
que mantener a mano una tabla de nombres que se desincroniza el primer dia
que se renombre o se mueva algo.

Uso:
  Blender --background ARCHIVO.blend --python tag_zones.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import out_path, save

ZONAS = {
    "web": ("desarrollos web",
            ["MONITOR_MAIN_PANEL", "MONITOR_SIDE_PANEL", "KEYBOARD",
             "DESK_TOP", "PC_TOWER"]),
    "video": ("videos",
              ["SCREEN_SURFACE", "PROJECTOR_BODY", "PROJECTOR_BEAM",
               "MEDIA_TOP", "TURNTABLE_BODY"]),
    "musica": ("musica",
               ["RECORDS_TOP", "VINYL_WALL_01", "VINYL_WALL_02", "VINYL_WALL_03",
                "VINYL_WALL_04", "VINYL_WALL_05", "VINYL_WALL_06",
                "SPEAKER_L_BODY", "SPEAKER_R_BODY", "AMPLIFIER"]),
    "texto": ("escritos",
              ["NOTEBOOK_EAST", "NOTEBOOK_EAST_COVER_TOP",
               "NOTEBOOK_EAST_COVER_BOTTOM", "TABLE_EAST_TOP",
               "SHEET_EAST_01", "SHEET_EAST_03", "SHEET_EAST_05"]),
    "mi": ("sobre mi",
           ["BED_FRAME_PROXY", "BLANKET_PROXY", "BACKPACK_BODY",
            "BACKPACK_FLAP"]),
}


def main():
    # Se limpia primero, asi sacar un objeto de la lista lo despinta de verdad.
    limpiados = 0
    for o in bpy.data.objects:
        if "zona" in o.keys():
            del o["zona"]
            if "zona_titulo" in o.keys():
                del o["zona_titulo"]
            limpiados += 1

    total, faltan = 0, []
    for clave, (titulo, nombres) in ZONAS.items():
        n = 0
        for nombre in nombres:
            o = bpy.data.objects.get(nombre)
            if o is None:
                faltan.append(nombre)
                continue
            o["zona"] = clave
            o["zona_titulo"] = titulo
            n += 1
        total += n
        print("  %-8s %-18s %d objetos" % (clave, titulo, n))

    if faltan:
        print("  no existen:", ", ".join(faltan))
    print("\nMarcados %d objetos en %d zonas (limpiados %d de antes)"
          % (total, len(ZONAS), limpiados))
    save(out_path(sys.argv, bpy.data.filepath))


main()
