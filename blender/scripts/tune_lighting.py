"""
AJUSTE DE NIVELES DE LUZ
========================

NO mueve ninguna luz ni la crea de nuevo: solo cambia potencias y el ambiente.
Es seguro correrlo despues de que hayas reubicado luces a mano.

  ambiente   color del mundo. Es una cupula pareja que llega a todos lados:
             es lo que evita que las zonas sin practica queden en negro.
  practicas  factor sobre la potencia de todas las luces del sector LIGHTS.
             Se guarda la potencia original en cada luz, asi el factor
             siempre se aplica sobre el valor de fabrica y no se acumula.

Uso:
  Blender --background ARCHIVO.blend --python tune_lighting.py -- SALIDA.blend [ambiente] [practicas]
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import out_path, save

AMBIENT_COLOR = (0.36, 0.35, 0.34)   # gris apenas calido
DEFAULT_AMBIENT = 0.30
DEFAULT_PRACTICALS = 0.80


def main():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ambient = float(extra[1]) if len(extra) > 1 else DEFAULT_AMBIENT
    practicals = float(extra[2]) if len(extra) > 2 else DEFAULT_PRACTICALS

    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*AMBIENT_COLOR, 1.0)
    bg.inputs[1].default_value = ambient

    n = 0
    for o in bpy.data.objects:
        if o.type != "LIGHT" or o.get("sector") != "LIGHTS":
            continue
        if "_energia_base" not in o:
            o["_energia_base"] = o.data.energy
        o.data.energy = o["_energia_base"] * practicals
        n += 1

    print("Ambiente: %.2f   Practicas: x%.2f sobre %d luces" % (ambient, practicals, n))
    save(out_path(sys.argv, bpy.data.filepath))


main()
