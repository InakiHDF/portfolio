"""
EXPORTAR LA HABITACION A GLB
============================

Reglas del export, y por que cada una:

  - Solo lo VISIBLE. Lo que ocultas con el ojo en el Outliner (techo, pared
    sur, su zocalo) tampoco sale del render, asi que tampoco tiene que estar
    en la web. Es el mismo criterio que ya usan los scripts de render.
  - Modificadores aplicados: los biseles tienen que viajar.
  - Propiedades personalizadas incluidas. Es la parte clave: `asset_type`,
    `sector`, `zona` y demas llegan al GLB como `userData` de cada objeto, y
    de ahi los lee la pagina. Sin esto habria que mantener una lista de
    nombres a mano en el javascript, que se desincroniza el primer dia.
  - Camaras incluidas: CAM_ISO_SW es el encuadre aprobado y la pagina lo
    tiene que reproducir exacto, no aproximar.
  - Filtrado: en Blender las texturas estan en "Closest". El exportador lo
    traduce a NEAREST en el sampler del glTF, asi el texel se ve como bloque
    tambien en el navegador.

Uso:
  Blender --background ARCHIVO.blend --python export_glb.py -- SALIDA.glb
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT = os.path.join(REPO, "web", "modelos", "habitacion.glb")


def main():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    destino = extra[0] if extra else DEFAULT
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    # Lo oculto en el visor se saca tambien del export.
    ocultos = []
    for o in bpy.data.objects:
        if o.hide_get():
            o.hide_viewport = True
            ocultos.append(o.name)
    print("Fuera del GLB:", ", ".join(ocultos) or "nada")

    visibles = [o for o in bpy.data.objects if not o.hide_viewport]
    mallas = [o for o in visibles if o.type == "MESH"]
    print("Objetos: %d   mallas: %d   caras: %d"
          % (len(visibles), len(mallas),
             sum(len(o.data.polygons) for o in mallas)))

    opciones = dict(
        filepath=destino,
        export_format="GLB",
        use_visible=True,
        export_apply=True,            # aplica los biseles
        export_extras=True,           # propiedades -> userData
        export_cameras=True,
        export_lights=True,
        export_yup=True,
        export_texture_dir="",
        export_image_format="AUTO",
        export_materials="EXPORT",
        export_normals=True,
        export_tangents=False,
        export_animations=False,
challenge_placeholder=None,
    )
    opciones.pop("challenge_placeholder")

    # El operador cambia de firma entre versiones: se prueban las claves y se
    # descartan las que esta version no conoce, en vez de fallar entero.
    validas = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    descartadas = [k for k in opciones if k not in validas]
    for k in descartadas:
        opciones.pop(k)
    if descartadas:
        print("Opciones que esta version no acepta:", ", ".join(descartadas))

    bpy.ops.export_scene.gltf(**opciones)
    mb = os.path.getsize(destino) / 1024 / 1024
    print("\nGLB: %s\nPeso: %.2f MB" % (destino, mb))


main()
