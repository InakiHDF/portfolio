"""
GENERADOR DEL ARCHIVO BASE — HABITACION_v001.blend
==================================================

Crea desde cero un archivo de Blender con:
  - Unidades metricas y escala 1.0
  - La estructura de colecciones definida en el brief
  - Las 4 camaras (CAM_FRONT / CAM_RIGHT / CAM_BACK / CAM_LEFT) con las
    imagenes de referencia cargadas como fondo de cada camara
  - El blockout de arquitectura (suelo, techo, 4 paredes, zocalos,
    plataforma, escalones, puerta, escalera)
  - UN solo mueble de ejemplo (BED_01) para documentar el patron
    ROOT / PROXY / propiedades personalizadas

TODAS las medidas estan en el diccionario ROOM y en las constantes de abajo.
Cambiar un numero y volver a ejecutar el script regenera el archivo entero.

Uso:
  /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
      --python blender/scripts/generate_blockout.py

ATENCION: este script SOBREESCRIBE el .blend de salida. Una vez que empieces a
trabajar a mano en el archivo, no lo vuelvas a ejecutar sobre la misma version:
subi el numero de OUT_NAME primero.
"""

import os
import math
import bpy
from mathutils import Matrix

# ---------------------------------------------------------------------------
# PARAMETROS EDITABLES
# ---------------------------------------------------------------------------

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(REPO, "blender")
OUT_NAME = "HABITACION_v001.blend"

# Dimensiones INTERIORES de la habitacion, en metros.
ROOM = {
    "width": 9.0,    # eje X  (de pared OESTE a pared ESTE)
    "depth": 8.0,    # eje Y  (de pared SUR a pared NORTE)
    "height": 2.9,   # eje Z  (del suelo al techo)
}

WALL_T = 0.15        # espesor de pared
SLAB_T = 0.20        # espesor de losa de suelo y techo
SKIRT_H = 0.12       # alto del zocalo
SKIRT_T = 0.03       # saliente del zocalo

# Camaras
CAM_HEIGHT = 1.60
CAM_LENS = 20.0      # mm. Las referencias son muy angulares; ajustable.
RES_X, RES_Y = 1920, 1080

# Mapeo de las imagenes de referencia a cada camara.
# Convencion usada: CAM_FRONT mira hacia -Y, CAM_BACK hacia +Y,
# CAM_RIGHT hacia +X, CAM_LEFT hacia -X (nombres segun plano, no segun
# la mano del observador). Si alguna referencia queda en la pared
# equivocada, intercambia los nombres de archivo en este diccionario.
CAM_REFS = {
    "CAM_FRONT": "Front.png",
    "CAM_RIGHT": "Right.png",
    "CAM_BACK": "Back.png",
    "CAM_LEFT": "Left.png",
}

# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

HALF_W = ROOM["width"] / 2.0
HALF_D = ROOM["depth"] / 2.0
H = ROOM["height"]


def wipe_scene():
    """Vacia el archivo por completo (objetos, mallas, materiales, imagenes)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights, bpy.data.images, bpy.data.collections):
        for item in list(block):
            try:
                block.remove(item, do_unlink=True)
            except (RuntimeError, TypeError):
                pass


def setup_scene():
    scene = bpy.context.scene
    scene.name = "HABITACION"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    for transform in ("AgX", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = transform
            break
        except TypeError:
            continue

    # Mundo oscuro: la escena se ilumina con luces en la Fase 7, no con el mundo.
    world = bpy.data.worlds.new("WORLD_HABITACION")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    scene.world = world


COLLECTIONS = [
    "00_REFERENCES",
    "10_ARCHITECTURE_LOCKED",
    "20_FURNITURE",
    "30_PROPS",
    "40_LIGHTS",
    "50_CAMERAS",
    "60_MATERIALS_GUIDES",
    "80_WIP",
    "90_APPROVED",
    "99_EXPORT",
]


def build_collections():
    root = bpy.data.collections.new("SCENE_ROOT")
    bpy.context.scene.collection.children.link(root)
    out = {"SCENE_ROOT": root}
    for name in COLLECTIONS:
        col = bpy.data.collections.new(name)
        root.children.link(col)
        out[name] = col
    return out


def make_material(name, rgb, roughness=0.9):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*rgb, 1.0)  # color en modo Solid del viewport
    return mat


def make_box(name, size, location, collection, material=None, props=None,
             parent=None):
    """Crea una caja con normales hacia afuera. size y location en metros."""
    sx, sy, sz = (s / 2.0 for s in size)
    verts = [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
    ]
    faces = [
        (0, 3, 2, 1),  # abajo
        (4, 5, 6, 7),  # arriba
        (0, 1, 5, 4),  # -Y
        (1, 2, 6, 5),  # +X
        (2, 3, 7, 6),  # +Y
        (3, 0, 4, 7),  # -X
    ]
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    if material:
        obj.data.materials.append(material)
    collection.objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
    apply_props(obj, props)
    return obj


def make_root(name, location, collection, props=None):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.35
    obj.location = location
    collection.objects.link(obj)
    apply_props(obj, props)
    return obj


def apply_props(obj, props):
    base = {"status": "blockout", "style": "low_poly_pixelated"}
    base.update(props or {})
    for key, value in base.items():
        obj[key] = value


# ---------------------------------------------------------------------------
# ARQUITECTURA
# ---------------------------------------------------------------------------

def build_architecture(col, mats):
    arch = col["10_ARCHITECTURE_LOCKED"]
    outer_w = ROOM["width"] + 2 * WALL_T
    outer_d = ROOM["depth"] + 2 * WALL_T

    make_box("FLOOR", (outer_w, outer_d, SLAB_T), (0, 0, -SLAB_T / 2),
             arch, mats["floor"],
             {"asset_id": "floor_01", "asset_type": "architecture",
              "material_id": "MAT_BLOCKOUT_FLOOR", "preserve_root_transform": True})

    make_box("CEILING", (outer_w, outer_d, SLAB_T), (0, 0, H + SLAB_T / 2),
             arch, mats["arch"],
             {"asset_id": "ceiling_01", "asset_type": "architecture"})

    walls = {
        # nombre        size                       location
        "WALL_SOUTH": ((outer_w, WALL_T, H), (0, -HALF_D - WALL_T / 2, H / 2)),
        "WALL_NORTH": ((outer_w, WALL_T, H), (0, HALF_D + WALL_T / 2, H / 2)),
        "WALL_EAST":  ((WALL_T, ROOM["depth"], H), (HALF_W + WALL_T / 2, 0, H / 2)),
        "WALL_WEST":  ((WALL_T, ROOM["depth"], H), (-HALF_W - WALL_T / 2, 0, H / 2)),
    }
    for name, (size, loc) in walls.items():
        make_box(name, size, loc, arch, mats["arch"],
                 {"asset_id": name.lower(), "asset_type": "architecture",
                  "material_id": "MAT_BLOCKOUT_ARCH"})

    skirts = {
        "SKIRTING_SOUTH": ((ROOM["width"], SKIRT_T, SKIRT_H),
                           (0, -HALF_D + SKIRT_T / 2, SKIRT_H / 2)),
        "SKIRTING_NORTH": ((ROOM["width"], SKIRT_T, SKIRT_H),
                           (0, HALF_D - SKIRT_T / 2, SKIRT_H / 2)),
        "SKIRTING_EAST":  ((SKIRT_T, ROOM["depth"], SKIRT_H),
                           (HALF_W - SKIRT_T / 2, 0, SKIRT_H / 2)),
        "SKIRTING_WEST":  ((SKIRT_T, ROOM["depth"], SKIRT_H),
                           (-HALF_W + SKIRT_T / 2, 0, SKIRT_H / 2)),
    }
    for name, (size, loc) in skirts.items():
        make_box(name, size, loc, arch, mats["skirt"],
                 {"asset_id": name.lower(), "asset_type": "architecture"})

    build_entrance(arch, mats)
    build_staircase(arch, mats)


def build_entrance(arch, mats):
    """Plataforma elevada + 3 escalones + puerta, en la esquina -X / +Y."""
    plat_h = 0.60
    plat_x0, plat_x1 = -HALF_W, -HALF_W + 1.40
    plat_y0, plat_y1 = 1.20, 3.20
    plat_cx = (plat_x0 + plat_x1) / 2
    plat_cy = (plat_y0 + plat_y1) / 2
    plat_d = plat_y1 - plat_y0

    root = make_root("ENTRANCE_01_ROOT", (plat_x1, plat_cy, 0.0), arch,
                     {"asset_id": "entrance_01", "asset_type": "entrance",
                      "notes": "plataforma, escalones y puerta de entrada"})

    make_box("PLATFORM_ENTRANCE", (plat_x1 - plat_x0, plat_d, plat_h),
             (plat_cx - plat_x1, 0, plat_h / 2), arch, mats["stair"],
             {"asset_id": "platform_entrance", "asset_type": "architecture"},
             parent=root)

    going, rises = 0.35, [0.45, 0.30, 0.15]
    for i, rise in enumerate(rises):
        x0 = i * going
        make_box(f"STEP_ENTRANCE_{i + 1:02d}", (going, plat_d, rise),
                 (x0 + going / 2, 0, rise / 2), arch, mats["stair"],
                 {"asset_id": f"step_entrance_{i + 1:02d}",
                  "asset_type": "architecture"},
                 parent=root)

    make_box("DOOR_PROXY", (0.06, 0.90, 2.05),
             (plat_x0 - plat_x1 + 0.03, 0, plat_h + 2.05 / 2), arch, mats["door"],
             {"asset_id": "door_01", "asset_type": "door",
              "material_id": "MAT_BLOCKOUT_DOOR"},
             parent=root)


def build_staircase(arch, mats):
    """Tramo recto que sube pegado a la pared NORTE, hacia -X."""
    steps, rise, going, width = 10, 0.19, 0.28, 1.30
    root = make_root("STAIRCASE_01_ROOT", (-1.00, HALF_D - width / 2, 0.0), arch,
                     {"asset_id": "staircase_01", "asset_type": "staircase",
                      "notes": "sube hacia -X pegada a la pared norte"})
    root.rotation_euler = (0, 0, math.pi)  # el tramo sube hacia -X en el mundo

    for i in range(steps):
        h = rise * (i + 1)
        make_box(f"STAIR_STEP_{i + 1:02d}", (going, width, h),
                 (i * going + going / 2, 0, h / 2), arch, mats["stair"],
                 {"asset_id": f"stair_step_{i + 1:02d}",
                  "asset_type": "architecture"},
                 parent=root)

    run = steps * going
    slope = math.atan2(rise, going)
    railing = make_box("STAIR_RAILING_PROXY", (run / math.cos(slope), 0.06, 0.06),
                       (run / 2, -width / 2 + 0.03,
                        steps * rise / 2 + 0.95),
                       arch, mats["metal"],
                       {"asset_id": "stair_railing_01", "asset_type": "railing"},
                       parent=root)
    railing.rotation_euler = (0, -slope, 0)


# ---------------------------------------------------------------------------
# MUEBLE DE EJEMPLO
# ---------------------------------------------------------------------------

def build_bed_example(col, mats):
    """Unico mueble incluido. Sirve como plantilla del patron ROOT/PROXY."""
    furn = col["20_FURNITURE"]
    root = make_root("BED_01_ROOT", (0.0, -HALF_D + 1.15, 0.0), furn,
                     {"asset_id": "bed_01", "asset_type": "bed",
                      "reference_group": "bed", "preserve_root_transform": True,
                      "notes": "EJEMPLO. Mover, reescalar o borrar libremente."})

    w, d = 1.60, 2.10  # ancho (X) x largo (Y) de la cama

    make_box("BED_FRAME_PROXY", (w, d, 0.30), (0, 0, 0.15), furn, mats["wood"],
             {"asset_id": "bed_frame_01", "asset_type": "bed_frame",
              "material_id": "MAT_BLOCKOUT_WOOD", "target_polygons": 400},
             parent=root)

    make_box("MATTRESS_PROXY", (w - 0.06, d - 0.10, 0.24), (0, 0, 0.42),
             furn, mats["fabric_light"],
             {"asset_id": "mattress_01", "asset_type": "mattress",
              "target_polygons": 200},
             parent=root)

    make_box("BLANKET_PROXY", (w + 0.06, d - 0.55, 0.10), (0, 0.22, 0.58),
             furn, mats["fabric"],
             {"asset_id": "blanket_01", "asset_type": "blanket",
              "target_polygons": 600},
             parent=root)

    # La cabecera queda contra la pared (-Y local): ahi van las almohadas.
    for side, x in (("L", -0.38), ("R", 0.38)):
        make_box(f"PILLOW_{side}_PROXY", (0.62, 0.36, 0.14),
                 (x, -d / 2 + 0.28, 0.61), furn, mats["fabric_light"],
                 {"asset_id": f"pillow_{side.lower()}_01", "asset_type": "pillow",
                  "material_id": "MAT_BLOCKOUT_FABRIC_LIGHT",
                  "preserve_bounding_box": True, "bbox_tolerance": 0.03,
                  "target_polygons": 300, "reference_group": "bed"},
                 parent=root)


# ---------------------------------------------------------------------------
# CAMARAS
# ---------------------------------------------------------------------------

CAM_YAW = {          # rotacion Z en grados; X siempre 90 (camara horizontal)
    "CAM_FRONT": 180,   # mira hacia -Y
    "CAM_RIGHT": 270,   # mira hacia +X
    "CAM_BACK": 0,      # mira hacia +Y
    "CAM_LEFT": 90,     # mira hacia -X
}


def build_cameras(col):
    cams = col["50_CAMERAS"]
    refs = col["00_REFERENCES"]
    loaded = []

    for name, yaw in CAM_YAW.items():
        data = bpy.data.cameras.new(name + "_DATA")
        data.lens = CAM_LENS
        data.sensor_width = 36.0
        data.clip_start = 0.05
        data.clip_end = 200.0

        img_path = os.path.join(REPO, CAM_REFS[name])
        if os.path.exists(img_path):
            img = bpy.data.images.load(img_path)
            img.name = "REF_" + name
            bg = data.background_images.new()
            bg.image = img
            bg.alpha = 0.40
            bg.display_depth = "FRONT"
            bg.frame_method = "FIT"
            data.show_background_images = True
            loaded.append(name)

        obj = bpy.data.objects.new(name, data)
        obj.location = (0.0, 0.0, CAM_HEIGHT)
        obj.rotation_euler = (math.radians(90), 0.0, math.radians(yaw))
        cams.objects.link(obj)
        apply_props(obj, {"asset_id": name.lower(), "asset_type": "camera",
                          "status": "approved"})

    bpy.context.scene.camera = bpy.data.objects["CAM_FRONT"]

    # Marcador visible del punto comun de camara, por si hay que moverlo.
    pivot = make_root("CAM_PIVOT_REFERENCE", (0, 0, CAM_HEIGHT), refs,
                      {"asset_id": "cam_pivot", "asset_type": "guide",
                       "notes": "las 4 camaras comparten esta posicion"})
    pivot.empty_display_type = "SPHERE"
    pivot.empty_display_size = 0.12
    return loaded


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    wipe_scene()
    setup_scene()
    col = build_collections()

    mats = {
        "arch": make_material("MAT_BLOCKOUT_ARCH", (0.62, 0.60, 0.57)),
        "floor": make_material("MAT_BLOCKOUT_FLOOR", (0.45, 0.33, 0.21)),
        "skirt": make_material("MAT_BLOCKOUT_SKIRTING", (0.30, 0.32, 0.35)),
        "stair": make_material("MAT_BLOCKOUT_STAIR", (0.48, 0.47, 0.45)),
        "door": make_material("MAT_BLOCKOUT_DOOR", (0.12, 0.22, 0.13)),
        "metal": make_material("MAT_BLOCKOUT_METAL", (0.06, 0.06, 0.06), 0.4),
        "wood": make_material("MAT_BLOCKOUT_WOOD", (0.24, 0.14, 0.08)),
        "fabric": make_material("MAT_BLOCKOUT_FABRIC", (0.20, 0.23, 0.29)),
        "fabric_light": make_material("MAT_BLOCKOUT_FABRIC_LIGHT", (0.72, 0.72, 0.74)),
    }
    build_architecture(col, mats)
    build_bed_example(col, mats)
    refs_ok = build_cameras(col)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, OUT_NAME)
    bpy.ops.wm.save_as_mainfile(filepath=out_path)

    print("\n" + "=" * 60)
    print("ARCHIVO GENERADO:", out_path)
    print("Objetos:", len(bpy.data.objects), "| Materiales:", len(bpy.data.materials))
    print("Referencias cargadas en camara:", ", ".join(refs_ok) or "ninguna")
    print("Habitacion interior: %.2f x %.2f x %.2f m"
          % (ROOM["width"], ROOM["depth"], ROOM["height"]))
    print("=" * 60)


main()
