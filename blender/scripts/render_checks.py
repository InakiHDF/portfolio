"""
RENDERS DE VALIDACION DESDE LAS 4 CAMARAS
=========================================

Renderiza CAM_FRONT / CAM_RIGHT / CAM_BACK / CAM_LEFT a baja resolucion y las
guarda en blender/renders/. Sirve para comprobar posicion y silueta despues de
cada cambio importante. No modifica ni guarda el archivo.

Uso:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
      blender/HABITACION_v001.blend --python blender/scripts/render_checks.py
"""

import os
import sys
import bpy

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "blender", "renders")
# nombre -> resolucion. CAM_TOP usa un encuadre casi cuadrado para que la
# planta entre entera y sea comparable con el plano de referencia.
CAMS = {
    "CAM_FRONT": (800, 450),
    "CAM_RIGHT": (800, 450),
    "CAM_BACK": (800, 450),
    "CAM_LEFT": (800, 450),
    "CAM_TOP": (900, 800),
    "CAM_NORTH_WIDE": (900, 506),
    "CAM_ISO_SW": (856, 472),
}

# WORKBENCH muestra el blockout con colores planos y sin necesidad de luces.
# Cambiar a "CYCLES" cuando ya haya iluminacion que valorar (Fase 7).
ENGINE = os.environ.get("CHECK_ENGINE", "BLENDER_WORKBENCH")

scene = bpy.context.scene
scene.render.engine = ENGINE
if ENGINE == "CYCLES":
    scene.cycles.samples = 24
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = True
else:
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"

os.makedirs(OUT, exist_ok=True)

# Argumentos despues de '--': lista de camaras a renderizar. Sin argumentos,
# renderiza todas.
only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

for name, (rx, ry) in CAMS.items():
    if only and name not in only:
        continue
    cam = bpy.data.objects.get(name)
    if not cam:
        print("FALTA la camara", name)
        continue
    scene.camera = cam
    scene.render.resolution_x = rx
    scene.render.resolution_y = ry
    # La cenital necesita el techo fuera del render.
    ceiling = bpy.data.objects.get("CEILING")
    if ceiling:
        ceiling.hide_render = (name == "CAM_TOP")
    # CAM_ISO_SW mira desde afuera del cuarto: la pared sur tapa la vista.
    for n in ("WALL_SOUTH", "SKIRTING_SOUTH"):
        o = bpy.data.objects.get(n)
        if o:
            o.hide_render = (name == "CAM_ISO_SW")
    scene.render.filepath = os.path.join(OUT, "CHECK_" + name + ".png")
    bpy.ops.render.render(write_still=True)
    print("Render listo:", scene.render.filepath)
