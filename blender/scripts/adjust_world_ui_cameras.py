"""Crea la copia para la UI integrada y encuadra sus tres superficies.

No modifica geometría, materiales, luces ni UVs. Parte de la copia HQ ya
horneada para conservar exactamente el aspecto aprobado.

Uso:
  Blender --background ENTRADA.blend --python adjust_world_ui_cameras.py -- SALIDA.blend
"""

import os
import sys

import bpy
from mathutils import Vector


def output_path():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not extra:
        raise SystemExit("falta SALIDA.blend")
    return os.path.abspath(extra[0])


def point(camera_name, target, lens, location=None, target_name=""):
    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != "CAMERA":
        raise SystemExit("falta " + camera_name)
    if location is not None:
        camera.location = location
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = (target - camera.location).to_track_quat("-Z", "Y")
    camera.data.lens = lens
    camera.data.clip_start = 0.025
    camera["target_object"] = target_name
    camera["world_ui_revision"] = "v020"
    print(camera_name, "LOCATION:", tuple(round(v, 6) for v in camera.location), "LENS:", lens)


def main():
    notebook = bpy.data.objects.get("NOTEBOOK_EAST")
    screen = bpy.data.objects.get("SCREEN_SURFACE")
    monitor_main = bpy.data.objects.get("MONITOR_MAIN_PANEL")
    monitor_side = bpy.data.objects.get("MONITOR_SIDE_PANEL")
    if not all((notebook, screen, monitor_main, monitor_side)):
        raise SystemExit("faltan superficies de referencia")

    # Films conserva el encuadre cercano. Web sube por encima del respaldo de
    # la silla y apunta al centro físico de ambos monitores.
    point("CAM_SECTION_VIDEO", screen.matrix_world.translation, 36.0,
          target_name="SCREEN_SURFACE")
    monitor_target = (monitor_main.matrix_world.translation + monitor_side.matrix_world.translation) * 0.5
    web_camera = bpy.data.objects.get("CAM_SECTION_WEB")
    web_location = web_camera.location + Vector((0.0, 0.0, 0.34))
    point("CAM_SECTION_WEB", monitor_target, 34.0, web_location,
          target_name="MONITOR_MAIN_PANEL+MONITOR_SIDE_PANEL")

    # La tapa conserva su bisagra original norte. Vista desde la silla (oeste),
    # tapa y cuerpo aparecen como páginas izquierda/derecha y el eje largo X
    # queda vertical en pantalla, que es la orientación natural de lectura.
    text_target = notebook.matrix_world.translation + Vector((0.0, 0.11, 0.012))
    text_location = text_target + Vector((-0.38, 0.0, 0.88))
    point("CAM_SECTION_TEXTO", text_target, 42.0, text_location,
          target_name="NOTEBOOK_EAST_SEATED_VIEW")

    path = output_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("SAVED:", path)


main()
