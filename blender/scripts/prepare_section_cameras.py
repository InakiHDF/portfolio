"""Prepara una copia editable con cámaras fijas para las cinco secciones.

También corrige dos solapamientos visibles ya aprobados para esta versión:
las hojas 01/02 de la mesa este y las cuatro polaroids de la pared norte.

Uso:
  Blender --background ENTRADA.blend --python prepare_section_cameras.py -- SALIDA.blend
"""

import math
import os
import sys

import bpy
from mathutils import Vector


COLLECTION = "50_CAMERAS_SECTION"
CAMERAS = {
    # nombre: (zona, objeto de referencia, ocupación, radio mínimo)
    "CAM_SECTION_WEB": ("web", "MONITOR_MAIN_PANEL", 0.46, 0.72),
    "CAM_SECTION_VIDEO": ("video", "SCREEN_SURFACE", 0.56, 0.90),
    "CAM_SECTION_TEXTO": ("texto", "TABLE_EAST_TOP", 0.58, 1.00),
    "CAM_SECTION_MUSICA": ("musica", "RECORDS_TOP", 0.50, 0.82),
    "CAM_SECTION_MI": ("mi", "BLANKET_PROXY", 0.54, 0.90),
}


def output_path():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not extra:
        raise SystemExit("falta SALIDA.blend")
    return os.path.abspath(extra[0])


def collection(name):
    found = bpy.data.collections.get(name)
    if found is None:
        found = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(found)
    return found


def world_sphere(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center = sum(points, Vector()) / len(points)
    radius = max((point - center).length for point in points)
    return center, radius


def exported_vertical_fov(data):
    """Replica el FOV vertical que glTF obtiene con el aspecto del render."""
    scene = bpy.context.scene
    aspect = (scene.render.resolution_x * scene.render.pixel_aspect_x) / (
        scene.render.resolution_y * scene.render.pixel_aspect_y
    )
    if data.sensor_fit == "VERTICAL":
        sensor_height = data.sensor_height
    else:
        sensor_height = data.sensor_width / aspect
    return 2.0 * math.atan(sensor_height / (2.0 * data.lens))


def create_camera(name, zone, target_name, occupancy, minimum_radius, home, target_collection):
    target = bpy.data.objects.get(target_name)
    if target is None:
        raise RuntimeError("falta el objeto de referencia " + target_name)

    camera = bpy.data.objects.get(name)
    if camera is None or camera.type != "CAMERA":
        data = bpy.data.cameras.new(name + "_DATA")
        camera = bpy.data.objects.new(name, data)
    for owner in list(camera.users_collection):
        owner.objects.unlink(camera)
    target_collection.objects.link(camera)

    source = home.data
    data = camera.data
    data.lens = source.lens
    data.sensor_width = source.sensor_width
    data.sensor_height = source.sensor_height
    data.sensor_fit = source.sensor_fit
    data.shift_x = source.shift_x
    data.shift_y = source.shift_y
    data.clip_start = 0.05
    data.clip_end = 200.0
    data.display_size = 0.18
    data.show_passepartout = True
    data.passepartout_alpha = 0.82
    camera.show_name = True
    camera.show_in_front = True

    center, radius = world_sphere(target)
    radius = max(radius, minimum_radius)
    direction = (home.matrix_world.translation - center).normalized()
    distance = radius / (math.tan(exported_vertical_fov(data) * 0.5) * occupancy)
    camera.location = center + direction * distance
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = (center - camera.location).to_track_quat("-Z", "Y")

    camera["section"] = zone
    camera["camera_role"] = "section_reference"
    camera["target_object"] = target_name
    camera["instructions"] = "Ajustar a mano: la web respeta posición, rotación y FOV exactos."
    return camera


def fix_overlaps():
    # La hoja queda en la posición nueva aprobada. El bake se rehace después,
    # de modo que no quede la sombra oscura de su posición anterior.
    sheet = bpy.data.objects.get("SHEET_EAST_01")
    if sheet:
        sheet.location.x = -0.10
        sheet.location.y = 0.48

    # Se conserva la composición original y se elimina únicamente la foto
    # central, que era la que invadía a las demás.
    positions = {
        "PHOTO_NORTH_01": (1.5509344339370728, 1.6272934675216675),
        "PHOTO_NORTH_03": (1.8309345245361328, 1.6072934865951538),
        "PHOTO_NORTH_04": (1.6709344387054443, 1.3672934770584106),
    }
    for name, (x, z) in positions.items():
        photo = bpy.data.objects.get(name)
        if photo:
            photo.location.x = x
            photo.location.z = z
    middle = bpy.data.objects.get("PHOTO_NORTH_02")
    if middle:
        bpy.data.objects.remove(middle, do_unlink=True)


def main():
    home = bpy.data.objects.get("CAM_ISO_SW")
    if home is None or home.type != "CAMERA":
        raise SystemExit("falta CAM_ISO_SW")

    fix_overlaps()
    target_collection = collection(COLLECTION)
    made = []
    for name, values in CAMERAS.items():
        made.append(create_camera(name, *values, home, target_collection))

    bpy.context.scene.camera = home
    bpy.context.scene["section_cameras"] = ",".join(CAMERAS)
    path = output_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("SECTION_CAMERAS:", ", ".join(camera.name for camera in made))
    print("SAVED:", path)


main()
