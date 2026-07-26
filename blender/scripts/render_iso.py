"""
RENDER DE CALIDAD DESDE CAM_ISO_SW
==================================

A resolucion completa (1712x945), con EEVEE, que tarda segundos en vez de
minutos. Sin denoiser agresivo: el alisado del denoiser a pocas muestras es
lo que da ese aspecto ceroso de imagen generada.

El render espeja lo que este oculto con el ojo en el Outliner.

Uso:
  Blender --background ARCHIVO.blend --python render_iso.py -- NOMBRE [exposicion]
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy

OUT = "/Users/gongorainaki/Repos/Web/Portfolio/blender/renders"
RES = (1712, 945)


def main():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = extra[0] if extra else "ISO"
    exposure = float(extra[1]) if len(extra) > 1 else 0.20

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = exposure

    ev = scene.eevee
    for attr, value in (("taa_render_samples", 128),
                        ("use_raytracing", True),
                        ("use_shadows", True),
                        # la niebla la decide el archivo, no el render
                        ("shadow_ray_count", 4),
                        ("shadow_step_count", 8)):
        if hasattr(ev, attr):
            setattr(ev, attr, value)
    if hasattr(ev, "ray_tracing_options"):
        ev.ray_tracing_options.resolution_scale = "1"

    # El ambiente lo define el archivo (tune_lighting.py), no el render.

    ocultos = [o.name for o in bpy.data.objects if o.hide_get()]
    for o in bpy.data.objects:
        if o.hide_get():
            o.hide_render = True
    print("Fuera del render:", ", ".join(ocultos) or "nada")

    scene.camera = bpy.data.objects["CAM_ISO_SW"]
    scene.render.filepath = os.path.join(OUT, "ISO_%s.png" % name)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print("%s  %dx%d  exposicion %.2f  en %.1f s"
          % (scene.render.filepath, RES[0], RES[1], exposure, time.time() - t))


main()
