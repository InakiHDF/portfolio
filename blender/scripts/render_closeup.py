"""
PRIMER PLANO CON LUZ NEUTRA
===========================

Renderiza uno o varios objetos aislados, con luz de estudio, para juzgar la
FORMA sin que la iluminacion dramatica de la escena tape lo que se esta
mirando. No guarda nada: la camara y las luces se crean y se descartan.

Uso:
  Blender --background ARCHIVO.blend --python render_closeup.py -- NOMBRE OBJ [OBJ...]

Ejemplo:
  ... render_closeup.py -- planta_oeste PLANT_WEST_POT PLANT_WEST_FOLIAGE
"""

import os
import sys
import math

import bpy
from mathutils import Vector

OUT = "/Users/gongorainaki/Repos/Web/Portfolio/blender/renders"
RES = (900, 900)


def world_bounds(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for corner in o.bound_box:
            p = o.matrix_world @ Vector(corner)
            lo = Vector((min(lo[i], p[i]) for i in range(3)))
            hi = Vector((max(hi[i], p[i]) for i in range(3)))
    return lo, hi


def main():
    extra = sys.argv[sys.argv.index("--") + 1:]
    name, targets = extra[0], extra[1:]
    objs = [bpy.data.objects[n] for n in targets if n in bpy.data.objects]
    if not objs:
        raise SystemExit("No encontre ninguno de: " + ", ".join(targets))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 128
    if hasattr(scene.eevee, "use_shadows"):
        scene.eevee.use_shadows = True

    # Todo lo demas fuera: se juzga la pieza sola.
    visibles = set(o.name for o in objs)
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o.name not in visibles

    # Fondo gris parejo en vez de las luces de la escena.
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.16, 0.16, 0.17, 1.0)
    bg.inputs[1].default_value = 1.0

    lo, hi = world_bounds(objs)
    center = (lo + hi) / 2.0
    size = max((hi - lo).length, 0.15)

    for key, offset, energy in (("KEY", (1.0, -1.3, 1.1), 900),
                                ("FILL", (-1.4, -0.7, 0.4), 260),
                                ("RIM", (-0.5, 1.5, 1.2), 600)):
        d = bpy.data.lights.new("TMP_" + key, type="AREA")
        d.energy = energy * size * size
        d.size = size * 1.4
        o = bpy.data.objects.new("TMP_" + key, d)
        pos = center + Vector(offset) * size
        o.location = pos
        o.rotation_euler = (center - pos).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(o)

    data = bpy.data.cameras.new("TMP_CAM")
    data.lens = 60.0
    cam = bpy.data.objects.new("TMP_CAM", data)
    pos = center + Vector((0.85, -1.5, 0.65)).normalized() * size * 1.75
    cam.location = pos
    cam.rotation_euler = (center - pos).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.render.filepath = os.path.join(OUT, "MODELO_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    caras = sum(len(o.data.polygons) for o in objs)
    print("MODELO_%s.png  %d objeto(s)  %d caras  tamano %.2f m"
          % (name, len(objs), caras, size))


main()
