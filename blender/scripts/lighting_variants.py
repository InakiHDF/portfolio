"""
VARIANTES DE ILUMINACION DESDE CAM_ISO_SW
=========================================

Renderiza la misma cámara con distintos niveles, para elegir. NO guarda el
.blend: todo lo que cambia (oscurecimiento de materiales, relleno, exposicion)
se aplica en memoria y se descarta.

Tres ejes por variante:
  mat_k   cuanto se oscurecen los materiales (1.0 = como estan)
  fill    multiplicador del relleno frio LIGHT_AMBIENT_FILL
  exp     exposicion del render

Uso:
  Blender --background ARCHIVO.blend --python lighting_variants.py -- [nombre...]
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy

OUT = "/Users/gongorainaki/Repos/Web/Portfolio/blender/renders"
RES = (856, 472)
SAMPLES = 44

# nombre -> (mat_k, fill, exposicion, descripcion)
VARIANTS = {
    "L1_CLARA":    (1.00, 1.00,  0.20, "materiales como estan, relleno entero"),
    "L2_MEDIA":    (0.65, 0.55,  0.45, "materiales al 65%, medio relleno"),
    "L3_OSCURA":   (0.40, 0.20,  0.80, "materiales al 40%, casi sin relleno"),
    "L4_BASEMENT": (0.20, 0.00,  1.05, "materiales al 20%, solo practicas"),
}

KEEP = ("EMISSIVE", "ACCENT")


def darken(k):
    """Guarda los colores originales la primera vez y aplica el factor."""
    for m in bpy.data.materials:
        if not m.use_nodes or any(t in m.name for t in KEEP):
            continue
        b = m.node_tree.nodes.get("Principled BSDF")
        if not b:
            continue
        if "_orig" not in m:
            c = b.inputs["Base Color"].default_value
            m["_orig"] = [c[0], c[1], c[2]]
        o = m["_orig"]
        # El papel y las telas claras bajan menos: si no, se pierden.
        f = k + (1.0 - k) * 0.45 if ("PAPER" in m.name or "LIGHT" in m.name) else k
        b.inputs["Base Color"].default_value = (o[0] * f, o[1] * f, o[2] * f, 1.0)
        b.inputs["Roughness"].default_value = 0.92


def main():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0

    # El render tiene que mostrar exactamente lo que se ve en el visor:
    # lo que este oculto con el ojo del Outliner tambien sale del render.
    ocultos = []
    for o in bpy.data.objects:
        if o.hide_get():
            o.hide_render = True
            ocultos.append(o.name)
    print("Fuera del render (ocultos en el visor):", ", ".join(ocultos) or "nada")
    scene.camera = bpy.data.objects["CAM_ISO_SW"]

    fill = bpy.data.objects.get("LIGHT_AMBIENT_FILL")
    fill_base = fill.data.energy if fill else 0.0

    only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name, (mat_k, f, exp, desc) in VARIANTS.items():
        if only and name not in only:
            continue
        darken(mat_k)
        if fill:
            fill.data.energy = fill_base * f
        scene.view_settings.exposure = exp
        scene.render.filepath = os.path.join(OUT, "LUZ_%s.png" % name)
        bpy.ops.render.render(write_still=True)
        print("listo %-12s  %s" % (name, desc))


main()
