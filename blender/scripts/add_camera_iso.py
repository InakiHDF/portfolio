"""
CAMARA MAESTRA  CAM_ISO_SW   (sector "CAMS")
============================================

La camara fija desde la que se va a ver la habitacion: alta, en el rincon
suroeste, mirando al noreste. Es la que tiene que coincidir con la foto de
referencia, y contra la que se comparan todas las pruebas de iluminacion.

Los parametros estan arriba. Volver a correr el script la actualiza en el
lugar; no crea una segunda camara ni toca ninguna otra.

Uso:
  Blender --background ARCHIVO.blend --python add_camera_iso.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import math

import bpy
from lib_blockout import col, tag, out_path, save

NAME = "CAM_ISO_SW"
SECTOR = "CAMS"

# Valores finales, ajustados a mano por el usuario en el visor y leidos del
# archivo. No los toques sin que el lo pida: este encuadre esta aprobado.
LOCATION = (3.5397, -2.9407, 2.8946)
ROTATION = (57.507, 0.0, 45.912)  # grados, Euler XYZ
LENS = 16.0                       # mm; cuanto mas chico, mas abarca
SENSOR = 36.0
RESOLUTION = (1712, 945)          # mismo encuadre que la foto de referencia


def main():
    cam = bpy.data.objects.get(NAME)
    if cam is None:
        data = bpy.data.cameras.new(NAME + "_DATA")
        cam = bpy.data.objects.new(NAME, data)
        col("50_CAMERAS").objects.link(cam)
        tag(cam, SECTOR, {"asset_id": "cam_iso_sw", "asset_type": "camera",
                          "status": "approved",
                          "notes": "camara fija del sitio; esta AFUERA del cuarto, "
                                   "hay que ocultar WALL_SOUTH al renderizar"})
    cam.data.lens = LENS
    cam.data.sensor_width = SENSOR
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200.0
    cam.location = LOCATION
    cam.rotation_euler = tuple(math.radians(a) for a in ROTATION)

    scene = bpy.context.scene
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION

    print("%s  loc=%s  rot=%s  lente=%.1fmm"
          % (NAME, tuple(round(v, 2) for v in LOCATION),
             tuple(round(v, 1) for v in ROTATION), LENS))
    save(out_path(sys.argv, bpy.data.filepath))


main()
