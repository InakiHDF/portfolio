"""
BISELES EN TODO EL BLOCKOUT
===========================

Una arista matematicamente perfecta no existe en el mundo real: toda esquina
tiene un radio minimo que atrapa un reflejo. Sin eso, cualquier render lee
como sintetico por mas bien iluminado que este. Es la causa mas barata de
arreglar del aspecto "plastilina".

Agrega un modificador Bevel a cada malla. Es NO destructivo: no toca la
geometria ni las transformadas, y se puede borrar o ajustar cuando quieras.

El ancho se calcula por objeto: una hoja de papel de 4 mm de espesor no puede
llevar el mismo bisel que una pared. Se usa un cuarto de la dimension mas
chica, con tope de 12 mm.

Uso:
  Blender --background ARCHIVO.blend --python add_bevels.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import out_path, save

MOD = "BEVEL_BLOCKOUT"
MAX_WIDTH = 0.012
MIN_WIDTH = 0.0006
SEGMENTS = 2
ANGLE = 0.5236          # 30 grados: no biselar caras casi coplanares


def main():
    tocados, salteados = 0, 0
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.data.polygons:
            continue

        old = obj.modifiers.get(MOD)
        if old:
            obj.modifiers.remove(old)

        smallest = min(obj.dimensions)
        width = min(MAX_WIDTH, smallest * 0.22)
        if width < MIN_WIDTH:
            salteados += 1
            continue

        m = obj.modifiers.new(MOD, "BEVEL")
        m.width = width
        m.segments = SEGMENTS
        m.limit_method = "ANGLE"
        m.angle_limit = ANGLE
        m.use_clamp_overlap = True
        m.harden_normals = False
        tocados += 1

    print("Biseles puestos: %d   salteados por finos: %d" % (tocados, salteados))

    caras = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
    print("Caras antes de aplicar modificadores: %d" % caras)
    save(out_path(sys.argv, bpy.data.filepath))


main()
