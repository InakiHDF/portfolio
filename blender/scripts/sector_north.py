"""
SECTOR NORTE  (sector "NORTH")
==============================

Todo lo que se apoya contra el nuevo limite norte (y = 2.70), mas el panel
calado bajo la escalera:

  - Panel calado sobre la cara de la escalera, con cuadros de pixel art
  - Mueble de audio/video con bandeja giradiscos y tres consolas retro
  - Pantalla de proyeccion enrollable y proyector colgado del techo
  - Estanteria de discos con parlantes, amplificador, lampara de lava y auriculares
  - Reja metalica con cuadros, reloj y fotos chicas
  - Dos plantas de piso
  - CAM_NORTH_WIDE: camara de validacion, porque CAM_LEFT/BACK quedaron
    demasiado cerca de la pared nueva para encuadrarla entera

Posiciones en X tomadas de tu cenital como fraccion del ancho de la
habitacion, asi no dependen de la escala de esa imagen.

Uso:
  Blender --background ARCHIVO.blend --python sector_north.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import box, root, col, tag, obj, clear_sector, out_path, save

SECTOR = "NORTH"
Y_WALL = 2.70          # cara sur de la pared nueva y de la escalera
Z_CEIL = 2.90

FURN = None
PROPS = None
ARCH = None


# ---------------------------------------------------------------------------
# PANEL CALADO BAJO LA ESCALERA
# ---------------------------------------------------------------------------

def build_stair_panel():
    """Un panel por escalon, asi el borde superior sigue la pendiente."""
    stair = obj("STAIRCASE_01_ROOT")
    steps = sorted((o for o in bpy.data.objects
                    if o.name.startswith("STAIR_STEP_")),
                   key=lambda o: o.location.x)
    if not steps:
        return
    width = steps[0].dimensions.y

    r = root("STAIR_PANEL_ROOT", (0, 0, 0), PROPS, SECTOR,
             {"asset_id": "stair_panel", "asset_type": "panel",
              "reference_group": "escalera"})
    r.parent = stair
    r.location = (0, 0, 0)

    for step in steps[2:]:                       # los dos primeros quedan lisos
        h = step.dimensions.z - 0.04
        if h <= 0.10:
            continue
        box("STAIR_PANEL_%s" % step.name[-2:],
            (step.dimensions.x, 0.03, h),
            (step.location.x, -width / 2 - 0.015, h / 2),
            PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
            props={"asset_id": "stair_panel_%s" % step.name[-2:],
                   "asset_type": "panel",
                   "notes": "textura calada / celosia"})

    # Cuadros de pixel art sobre el panel. (x mundo, z, ancho, alto)
    frames = [(-3.10, 0.80, 0.30, 0.38), (-2.78, 1.22, 0.26, 0.26),
              (-2.42, 0.92, 0.34, 0.30), (-2.28, 1.52, 0.24, 0.32),
              (-1.96, 1.24, 0.30, 0.36), (-1.62, 1.72, 0.28, 0.28),
              (-1.34, 1.10, 0.32, 0.34)]
    for i, (x, z, w, h) in enumerate(frames):
        box("FRAME_STAIR_%02d" % (i + 1), (w, 0.03, h),
            (x, Y_WALL - 0.045, z), PROPS, "MAT_BLOCKOUT_PAPER",
            sector=SECTOR,
            props={"asset_id": "frame_stair_%02d" % (i + 1),
                   "asset_type": "poster",
                   "texture_id": "TEX_FRAME_STAIR_%02d" % (i + 1)})


# ---------------------------------------------------------------------------
# MUEBLE DE AUDIO / VIDEO
# ---------------------------------------------------------------------------

def build_media_console():
    x0, x1 = -1.74, 0.56
    w, d, h = x1 - x0, 0.55, 0.60
    cx = (x0 + x1) / 2
    r = root("MEDIA_CONSOLE_01_ROOT", (cx, Y_WALL - d / 2, 0.0), FURN, SECTOR,
             {"asset_id": "media_console_01", "asset_type": "console",
              "reference_group": "norte"})

    box("MEDIA_TOP", (w, d, 0.06), (0, 0, h - 0.03), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "media_top", "asset_type": "console"})
    box("MEDIA_SHELF_LOW", (w - 0.10, d, 0.05), (0, 0, 0.20), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "media_shelf_low", "asset_type": "console"})
    for i, x in enumerate((-w / 2 + 0.025, -0.383, 0.383, w / 2 - 0.025)):
        box("MEDIA_DIV_%02d" % (i + 1), (0.05, d, h - 0.06), (x, 0, (h - 0.06) / 2),
            FURN, "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
            props={"asset_id": "media_div_%02d" % (i + 1),
                   "asset_type": "console"})

    # Arriba: bandeja giradiscos, una caja blanca y aparatos chatos
    box("TURNTABLE_BODY", (0.52, 0.42, 0.10), (-0.30, 0.0, h + 0.05), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "turntable_01", "asset_type": "audio"})
    box("TURNTABLE_PLATTER", (0.30, 0.30, 0.03), (-0.33, 0.0, h + 0.115), PROPS,
        "MAT_BLOCKOUT_METAL", parent=r, sector=SECTOR,
        props={"asset_id": "turntable_platter", "asset_type": "audio"})
    box("MEDIA_BOX_WHITE", (0.34, 0.34, 0.26), (-0.94, 0.0, h + 0.13), PROPS,
        "MAT_BLOCKOUT_FABRIC_LIGHT", parent=r, sector=SECTOR,
        props={"asset_id": "media_box_white", "asset_type": "equipment"})
    for i, (x, w2, d2, h2) in enumerate(((0.38, 0.40, 0.28, 0.06),
                                         (0.82, 0.26, 0.20, 0.05),
                                         (0.30, 0.16, 0.10, 0.04))):
        box("MEDIA_GEAR_%02d" % (i + 1), (w2, d2, h2),
            (x, -0.10 if i == 2 else 0.0, h + h2 / 2), PROPS,
            "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
            props={"asset_id": "media_gear_%02d" % (i + 1),
                   "asset_type": "equipment"})

    # Abajo: tres consolas retro
    retro = [(-0.75, "MAT_BLOCKOUT_FABRIC_LIGHT"),
             (0.0, "MAT_BLOCKOUT_ACCENT_BLUE"),
             (0.75, "MAT_BLOCKOUT_PLASTIC_BLACK")]
    for i, (x, m) in enumerate(retro):
        box("RETRO_CONSOLE_%02d" % (i + 1), (0.44, 0.34, 0.11),
            (x, 0.0, 0.28), PROPS, m, parent=r, sector=SECTOR,
            props={"asset_id": "retro_console_%02d" % (i + 1),
                   "asset_type": "equipment"})


# ---------------------------------------------------------------------------
# PANTALLA Y PROYECTOR
# ---------------------------------------------------------------------------

def build_screen():
    x0, x1 = -1.11, 1.05
    w = x1 - x0
    cx = (x0 + x1) / 2
    r = root("SCREEN_PROJ_01_ROOT", (cx, Y_WALL, 0.0), PROPS, SECTOR,
             {"asset_id": "screen_proj_01", "asset_type": "screen",
              "reference_group": "norte"})

    box("SCREEN_SURFACE", (w, 0.03, 1.20), (0, -0.035, 1.75), PROPS,
        "MAT_BLOCKOUT_FABRIC_LIGHT", parent=r, sector=SECTOR,
        props={"asset_id": "screen_surface", "asset_type": "screen",
               "texture_id": "TEX_SCREEN_PROJ",
               "notes": "candidata a emision + video/imagen del usuario"})
    box("SCREEN_FRAME_BOTTOM", (w + 0.04, 0.05, 0.06), (0, -0.04, 1.12),
        PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "screen_frame_bottom", "asset_type": "screen"})
    box("SCREEN_CASE", (w + 0.16, 0.14, 0.14), (0, -0.07, 2.44), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "screen_case", "asset_type": "screen",
               "notes": "cajon de la pantalla enrollable"})


def build_projector():
    r = root("PROJECTOR_01_ROOT", (-0.46, 2.05, Z_CEIL), PROPS, SECTOR,
             {"asset_id": "projector_01", "asset_type": "projector",
              "reference_group": "norte"})
    box("PROJECTOR_MOUNT", (0.06, 0.06, 0.12), (0, 0, -0.06), PROPS,
        "MAT_BLOCKOUT_METAL", parent=r, sector=SECTOR,
        props={"asset_id": "projector_mount", "asset_type": "projector"})
    box("PROJECTOR_BODY", (0.38, 0.34, 0.17), (0, 0, -0.205), PROPS,
        "MAT_BLOCKOUT_FABRIC_LIGHT", parent=r, sector=SECTOR,
        props={"asset_id": "projector_body", "asset_type": "projector"})
    box("PROJECTOR_LENS", (0.10, 0.05, 0.10), (0.10, -0.19, -0.205), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "projector_lens", "asset_type": "projector"})


# ---------------------------------------------------------------------------
# ESTANTERIA DE DISCOS Y EQUIPO DE AUDIO
# ---------------------------------------------------------------------------

def build_record_shelf():
    x0, x1 = 1.16, 3.22
    w, d, h = x1 - x0, 0.52, 0.95
    cx = (x0 + x1) / 2
    r = root("SHELF_RECORDS_01_ROOT", (cx, Y_WALL - d / 2, 0.0), FURN, SECTOR,
             {"asset_id": "shelf_records_01", "asset_type": "shelf",
              "reference_group": "norte"})

    box("RECORDS_TOP", (w, d, 0.05), (0, 0, h - 0.025), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "records_top", "asset_type": "shelf"})
    box("RECORDS_BOTTOM", (w, d, 0.05), (0, 0, 0.025), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "records_bottom", "asset_type": "shelf"})
    box("RECORDS_BACK", (w, 0.03, h), (0, d / 2 - 0.015, h / 2), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "records_back", "asset_type": "shelf"})
    for i, x in enumerate((-w / 2 + 0.02, -0.505, 0.0, 0.505, w / 2 - 0.02)):
        box("RECORDS_DIV_%02d" % (i + 1), (0.04, d, h - 0.10), (x, 0, h / 2),
            FURN, "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
            props={"asset_id": "records_div_%02d" % (i + 1),
                   "asset_type": "shelf"})

    # Contenido de las cuatro cajas
    cubes = (-0.7575, -0.2525, 0.2525, 0.7575)
    for i, x in enumerate(cubes):
        if i == 1:
            box("RECORDS_BASKET", (0.42, 0.40, 0.34), (x, -0.02, 0.24), PROPS,
                "MAT_BLOCKOUT_WOOD_LIGHT", parent=r, sector=SECTOR,
                props={"asset_id": "records_basket", "asset_type": "decoration"})
            continue
        for j, (dx, tw) in enumerate(((-0.14, 0.11), (0.0, 0.13), (0.15, 0.09))):
            box("RECORDS_STACK_%02d_%02d" % (i + 1, j + 1), (tw, 0.36, 0.36),
                (x + dx, -0.02, 0.25), PROPS,
                "MAT_BLOCKOUT_FABRIC" if (i + j) % 2 else "MAT_BLOCKOUT_PAPER",
                parent=r, sector=SECTOR,
                props={"asset_id": "records_stack_%02d_%02d" % (i + 1, j + 1),
                       "asset_type": "records"})

    # Arriba: parlantes, amplificador, lampara de lava, auriculares
    for side, x in (("L", -0.86), ("R", 0.86)):
        box("SPEAKER_%s_BODY" % side, (0.32, 0.36, 0.55), (x, 0.0, h + 0.275),
            PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
            props={"asset_id": "speaker_%s" % side.lower(),
                   "asset_type": "audio"})
        for j, (dz, dia) in enumerate(((0.16, 0.22), (-0.10, 0.13))):
            box("SPEAKER_%s_CONE_%02d" % (side, j + 1), (dia, 0.03, dia),
                (x, -0.185, h + 0.275 + dz), PROPS, "MAT_BLOCKOUT_METAL",
                parent=r, sector=SECTOR,
                props={"asset_id": "speaker_%s_cone_%02d" % (side.lower(), j + 1),
                       "asset_type": "audio"})

    box("AMPLIFIER", (0.52, 0.36, 0.16), (-0.10, 0.0, h + 0.08), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "amplifier_01", "asset_type": "audio"})
    box("AMPLIFIER_DISPLAY", (0.20, 0.02, 0.06), (-0.16, -0.19, h + 0.09),
        PROPS, "MAT_BLOCKOUT_ACCENT_BLUE", parent=r, sector=SECTOR,
        props={"asset_id": "amplifier_display", "asset_type": "screen"})
    box("LAVA_LAMP_BASE", (0.13, 0.13, 0.08), (0.34, 0.0, h + 0.04), PROPS,
        "MAT_BLOCKOUT_METAL", parent=r, sector=SECTOR,
        props={"asset_id": "lava_lamp_base", "asset_type": "lamp"})
    box("LAVA_LAMP_GLASS", (0.11, 0.11, 0.30), (0.34, 0.0, h + 0.23), PROPS,
        "MAT_BLOCKOUT_EMISSIVE", parent=r, sector=SECTOR,
        props={"asset_id": "lava_lamp_glass", "asset_type": "lamp",
               "notes": "practica: lleva luz propia en la fase 7"})
    box("HEADPHONES_STAND", (0.05, 0.05, 0.24), (0.58, 0.0, h + 0.12), PROPS,
        "MAT_BLOCKOUT_METAL", parent=r, sector=SECTOR,
        props={"asset_id": "headphones_stand", "asset_type": "audio"})
    box("HEADPHONES", (0.22, 0.14, 0.18), (0.58, 0.0, h + 0.31), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "headphones_01", "asset_type": "audio"})


# ---------------------------------------------------------------------------
# PARED: REJA, RELOJ, FOTOS
# ---------------------------------------------------------------------------

def build_wall_decor():
    r = root("DECOR_NORTH_ROOT", (0.0, Y_WALL, 0.0), PROPS, SECTOR,
             {"asset_id": "decor_north", "asset_type": "poster_group",
              "reference_group": "norte"})

    # Reja metalica sobre la estanteria de discos
    gx0, gx1, gz0, gz1 = 1.41, 3.22, 1.86, 2.80
    box("GRID_PANEL", (gx1 - gx0, 0.03, gz1 - gz0),
        ((gx0 + gx1) / 2, -0.03, (gz0 + gz1) / 2), PROPS,
        "MAT_BLOCKOUT_METAL", parent=r, sector=SECTOR,
        props={"asset_id": "grid_panel_01", "asset_type": "panel",
               "notes": "reja: textura con alpha en la fase 6"})
    grid_frames = [(1.66, 2.44, 0.34, 0.42), (2.06, 2.52, 0.28, 0.28),
                   (2.40, 2.30, 0.36, 0.36), (2.86, 2.48, 0.30, 0.38),
                   (2.62, 2.02, 0.26, 0.26), (1.82, 2.02, 0.30, 0.24)]
    for i, (x, z, w, h) in enumerate(grid_frames):
        box("FRAME_GRID_%02d" % (i + 1), (w, 0.03, h), (x, -0.06, z), PROPS,
            "MAT_BLOCKOUT_PAPER", parent=r, sector=SECTOR,
            props={"asset_id": "frame_grid_%02d" % (i + 1),
                   "asset_type": "poster",
                   "texture_id": "TEX_FRAME_GRID_%02d" % (i + 1)})

    # Reloj y fotos van entre la pantalla y la reja, nunca detras de la
    # pantalla (que ocupa de x=-1.11 a x=1.05).
    box("CLOCK_WALL", (0.38, 0.04, 0.38), (1.80, -0.02, 1.66), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "clock_wall_01", "asset_type": "decoration",
               "texture_id": "TEX_CLOCK"})
    for i, (x, z) in enumerate(((1.16, 1.78), (1.30, 1.68), (1.44, 1.76),
                                (1.28, 1.52))):
        box("PHOTO_NORTH_%02d" % (i + 1), (0.11, 0.03, 0.15), (x, -0.02, z),
            PROPS, "MAT_BLOCKOUT_PAPER", parent=r, sector=SECTOR,
            props={"asset_id": "photo_north_%02d" % (i + 1),
                   "asset_type": "poster",
                   "texture_id": "TEX_PHOTO_NORTH_%02d" % (i + 1)})


def build_plants():
    # (x, ancho de maceta, ancho de follaje, alto de follaje)
    # La chica entra entre el mueble de audio (termina en 0.56) y la
    # estanteria de discos (arranca en 1.16); la alta va al este de la
    # estanteria, sin taparla.
    for i, (x, pot, fol, fh) in enumerate(((0.86, 0.32, 0.50, 0.62),
                                           (3.74, 0.44, 0.72, 1.40))):
        r = root("PLANT_NORTH_%02d_ROOT" % (i + 1),
                 (x, Y_WALL - pot / 2 - 0.05, 0.0), PROPS, SECTOR,
                 {"asset_id": "plant_north_%02d" % (i + 1),
                  "asset_type": "plant", "reference_group": "norte"})
        box("PLANT_NORTH_%02d_POT" % (i + 1), (pot, pot, pot * 1.15),
            (0, 0, pot * 0.575), PROPS, "MAT_BLOCKOUT_CERAMIC",
            parent=r, sector=SECTOR,
            props={"asset_id": "plant_north_%02d_pot" % (i + 1),
                   "asset_type": "plant"})
        box("PLANT_NORTH_%02d_FOLIAGE" % (i + 1), (fol, fol, fh),
            (0, 0, pot * 1.15 + fh / 2 - 0.05), PROPS, "MAT_BLOCKOUT_PLANT",
            parent=r, sector=SECTOR,
            props={"asset_id": "plant_north_%02d_foliage" % (i + 1),
                   "asset_type": "plant"})


def add_wide_camera():
    """CAM_BACK quedo a 2.70 m de la pared nueva y no la encuadra entera."""
    if bpy.data.objects.get("CAM_NORTH_WIDE"):
        return
    data = bpy.data.cameras.new("CAM_NORTH_WIDE_DATA")
    data.lens = 20.0
    data.sensor_width = 36.0
    data.clip_start = 0.05
    data.clip_end = 200.0
    cam = bpy.data.objects.new("CAM_NORTH_WIDE", data)
    cam.location = (0.0, -2.20, 1.60)
    cam.rotation_euler = (math.radians(90), 0.0, 0.0)
    col("50_CAMERAS").objects.link(cam)
    tag(cam, SECTOR, {"asset_id": "cam_north_wide", "asset_type": "camera",
                      "notes": "solo validacion; no reemplaza a CAM_BACK"})


def main():
    global FURN, PROPS, ARCH
    FURN = col("20_FURNITURE")
    PROPS = col("30_PROPS")
    ARCH = col("10_ARCHITECTURE_LOCKED")

    print("Objetos NORTH reemplazados:", clear_sector(SECTOR))
    build_stair_panel()
    build_media_console()
    build_screen()
    build_projector()
    build_record_shelf()
    build_wall_decor()
    build_plants()
    add_wide_camera()
    save(out_path(sys.argv, bpy.data.filepath))


main()
