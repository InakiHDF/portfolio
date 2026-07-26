"""
SECTOR OESTE  (sector "WEST")  — lo que ve CAM_LEFT
==================================================

Setup de computadora, estante con libros y planta colgante, cuadros, planta de
piso, riel de luces, y en el retranqueo: estante de vasijas y rack de botellas.

Reconstruible: borra y rehace solo los objetos con la propiedad sector="WEST".

Uso:
  Blender --background ARCHIVO.blend --python sector_west.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import box, root, col, clear_sector, out_path, save

SECTOR = "WEST"
X_WALL = -4.50        # cara interior de la pared oeste, tramo del setup
X_RECESS = -4.85      # cara interior del tramo retranqueado

FURN = None
PROPS = None


def build_desk():
    """Escritorio de 2.90 m contra la pared, de y=-3.40 a y=-0.50."""
    r = root("DESK_SETUP_01_ROOT", (X_WALL, -1.95, 0.0), FURN, SECTOR,
             {"asset_id": "desk_setup_01", "asset_type": "desk",
              "reference_group": "setup_oeste"})

    box("DESK_TOP", (0.72, 2.90, 0.05), (0.36, 0.0, 0.725), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "desk_top_01", "asset_type": "desk"})
    box("DESK_PANEL_SOUTH", (0.66, 0.05, 0.70), (0.35, -1.42, 0.35), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "desk_panel_south", "asset_type": "desk"})
    box("DESK_LEG_MID", (0.66, 0.05, 0.70), (0.35, 0.30, 0.35), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "desk_leg_mid", "asset_type": "desk"})

    # Cajonera en el extremo norte
    box("DESK_DRAWERS", (0.62, 0.50, 0.70), (0.34, 1.12, 0.35), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "desk_drawers_01", "asset_type": "drawer_unit"})
    for i, z in enumerate((0.15, 0.36, 0.57)):
        box("DESK_DRAWER_FRONT_%02d" % (i + 1), (0.02, 0.44, 0.17),
            (0.655, 1.12, z), FURN, "MAT_BLOCKOUT_WOOD_LIGHT",
            parent=r, sector=SECTOR,
            props={"asset_id": "desk_drawer_%02d" % (i + 1),
                   "asset_type": "drawer"})
        box("DESK_DRAWER_HANDLE_%02d" % (i + 1), (0.02, 0.22, 0.02),
            (0.672, 1.12, z), FURN, "MAT_BLOCKOUT_FABRIC_LIGHT",
            parent=r, sector=SECTOR,
            props={"asset_id": "desk_handle_%02d" % (i + 1),
                   "asset_type": "drawer"})


def build_computer():
    r = root("COMPUTER_01_ROOT", (X_WALL, -1.95, 0.0), PROPS, SECTOR,
             {"asset_id": "computer_01", "asset_type": "computer",
              "reference_group": "setup_oeste"})

    box("PC_TOWER", (0.24, 0.46, 0.52), (0.28, -1.05, 0.26), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "pc_tower_01", "asset_type": "computer"})
    box("PC_TOWER_LED_BAR", (0.02, 0.30, 0.03), (0.405, -1.05, 0.46), PROPS,
        "MAT_BLOCKOUT_ACCENT_BLUE", parent=r, sector=SECTOR,
        props={"asset_id": "pc_led_bar", "asset_type": "screen"})
    box("PC_TOWER_LED_LOGO", (0.02, 0.09, 0.09), (0.405, -1.05, 0.14), PROPS,
        "MAT_BLOCKOUT_ACCENT_BLUE", parent=r, sector=SECTOR,
        props={"asset_id": "pc_led_logo", "asset_type": "screen"})

    # Monitores: el grande al sur, el chico al norte
    for name, y, w, h, aid in (("MAIN", -0.35, 0.62, 0.38, "monitor_main"),
                               ("SIDE", 0.36, 0.50, 0.31, "monitor_side")):
        top = 0.87 + h / 2
        box("MONITOR_%s_PANEL" % name, (0.045, w, h), (0.22, y, top), PROPS,
            "MAT_BLOCKOUT_SCREEN", parent=r, sector=SECTOR,
            props={"asset_id": aid, "asset_type": "monitor",
                   "notes": "pantalla: candidata a textura/emision"})
        box("MONITOR_%s_NECK" % name, (0.06, 0.06, 0.14), (0.22, y, 0.815),
            PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
            props={"asset_id": aid + "_neck", "asset_type": "monitor"})
        box("MONITOR_%s_BASE" % name, (0.24, 0.26, 0.02), (0.22, y, 0.757),
            PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
            props={"asset_id": aid + "_base", "asset_type": "monitor"})

    box("KEYBOARD", (0.17, 0.46, 0.02), (0.48, -0.15, 0.76), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "keyboard_01", "asset_type": "peripheral"})
    box("MOUSE", (0.07, 0.11, 0.03), (0.48, 0.22, 0.765), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "mouse_01", "asset_type": "peripheral"})
    box("MUG_DESK", (0.09, 0.09, 0.10), (0.50, 0.64, 0.80), PROPS,
        "MAT_BLOCKOUT_FABRIC_LIGHT", parent=r, sector=SECTOR,
        props={"asset_id": "mug_01", "asset_type": "decoration"})
    box("PAPERS_DESK", (0.22, 0.30, 0.012), (0.50, -1.02, 0.756), PROPS,
        "MAT_BLOCKOUT_PAPER", parent=r, sector=SECTOR,
        props={"asset_id": "papers_desk", "asset_type": "paper"})

    # Lampara articulada en el extremo sur
    box("LAMP_DESK_BASE", (0.16, 0.16, 0.03), (0.20, -1.30, 0.765), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "lamp_desk_base", "asset_type": "lamp"})
    box("LAMP_DESK_ARM_A", (0.04, 0.04, 0.40), (0.20, -1.30, 0.98), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "lamp_desk_arm_a", "asset_type": "lamp"})
    box("LAMP_DESK_ARM_B", (0.34, 0.04, 0.04), (0.36, -1.30, 1.17), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "lamp_desk_arm_b", "asset_type": "lamp"})
    box("LAMP_DESK_HEAD", (0.13, 0.13, 0.12), (0.53, -1.30, 1.10), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "lamp_desk_head", "asset_type": "lamp"})
    box("LAMP_DESK_BULB", (0.09, 0.09, 0.01), (0.53, -1.30, 1.035), PROPS,
        "MAT_BLOCKOUT_EMISSIVE", parent=r, sector=SECTOR,
        props={"asset_id": "lamp_desk_bulb", "asset_type": "lamp",
               "notes": "aca va LIGHT_DESK_WEST en la fase 7"})


def build_chair():
    r = root("CHAIR_DESK_01_ROOT", (-3.62, -2.05, 0.0), FURN, SECTOR,
             {"asset_id": "chair_desk_01", "asset_type": "chair",
              "reference_group": "setup_oeste"})
    black = "MAT_BLOCKOUT_PLASTIC_BLACK"

    box("CHAIR_SEAT", (0.50, 0.52, 0.09), (0.0, 0.0, 0.46), FURN, black,
        parent=r, sector=SECTOR,
        props={"asset_id": "chair_seat", "asset_type": "chair"})
    box("CHAIR_BACK", (0.08, 0.48, 0.58), (0.23, 0.0, 0.80), FURN, black,
        parent=r, sector=SECTOR,
        props={"asset_id": "chair_back", "asset_type": "chair"})
    for side in (-1, 1):
        box("CHAIR_ARM_%s" % ("S" if side < 0 else "N"), (0.32, 0.05, 0.04),
            (0.02, side * 0.28, 0.63), FURN, black, parent=r, sector=SECTOR,
            props={"asset_id": "chair_arm", "asset_type": "chair"})
        box("CHAIR_ARM_POST_%s" % ("S" if side < 0 else "N"),
            (0.05, 0.05, 0.14), (0.14, side * 0.28, 0.54), FURN, black,
            parent=r, sector=SECTOR,
            props={"asset_id": "chair_arm_post", "asset_type": "chair"})
    box("CHAIR_COLUMN", (0.09, 0.09, 0.30), (0.0, 0.0, 0.27), FURN, black,
        parent=r, sector=SECTOR,
        props={"asset_id": "chair_column", "asset_type": "chair"})
    for i, ang in enumerate((math.radians(35), math.radians(-35))):
        box("CHAIR_BASE_%02d" % (i + 1), (0.62, 0.07, 0.04), (0.0, 0.0, 0.06),
            FURN, black, rotation=(0, 0, ang), parent=r, sector=SECTOR,
            props={"asset_id": "chair_base_%02d" % (i + 1),
                   "asset_type": "chair"})


def build_wall_shelf():
    """Estante sobre el escritorio, con libros, vela y planta colgante."""
    r = root("SHELF_DESK_01_ROOT", (X_WALL, -1.95, 1.78), FURN, SECTOR,
             {"asset_id": "shelf_desk_01", "asset_type": "shelf",
              "reference_group": "setup_oeste"})

    box("SHELF_DESK_BOARD", (0.26, 1.70, 0.05), (0.13, 0.0, 0.0), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "shelf_desk_board", "asset_type": "shelf"})
    for side in (-1, 1):
        box("SHELF_DESK_BRACKET_%s" % ("S" if side < 0 else "N"),
            (0.18, 0.04, 0.16), (0.10, side * 0.70, -0.10), FURN,
            "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
            props={"asset_id": "shelf_desk_bracket", "asset_type": "shelf"})

    box("SHELF_BOOKS_STACK", (0.20, 0.26, 0.09), (0.13, -0.62, 0.07), PROPS,
        "MAT_BLOCKOUT_PAPER", parent=r, sector=SECTOR,
        props={"asset_id": "books_stack_shelf", "asset_type": "books"})
    for i in range(6):
        h = 0.22 + (i % 3) * 0.03
        box("SHELF_BOOK_%02d" % (i + 1), (0.15, 0.042, h),
            (0.12, -0.40 + i * 0.05, 0.025 + h / 2), PROPS,
            "MAT_BLOCKOUT_WOOD_LIGHT" if i % 2 else "MAT_BLOCKOUT_FABRIC",
            parent=r, sector=SECTOR,
            props={"asset_id": "book_shelf_%02d" % (i + 1),
                   "asset_type": "books"})
    box("SHELF_CANDLE", (0.10, 0.10, 0.13), (0.13, 0.18, 0.09), PROPS,
        "MAT_BLOCKOUT_EMISSIVE", parent=r, sector=SECTOR,
        props={"asset_id": "candle_shelf", "asset_type": "lamp",
               "notes": "practica: lleva luz propia en la fase 7"})

    # Planta colgante en el extremo norte del estante
    box("PLANT_HANGING_POT", (0.20, 0.20, 0.17), (0.13, 0.62, 0.11), PROPS,
        "MAT_BLOCKOUT_CERAMIC", parent=r, sector=SECTOR,
        props={"asset_id": "plant_hanging_pot", "asset_type": "plant"})
    for i, (dx, dy, drop) in enumerate(((0.00, -0.07, 0.52), (0.06, 0.02, 0.34),
                                        (-0.05, 0.09, 0.66), (0.10, -0.02, 0.24))):
        box("PLANT_HANGING_VINE_%02d" % (i + 1), (0.06, 0.06, drop),
            (0.12 + dx, 0.62 + dy, 0.02 - drop / 2), PROPS,
            "MAT_BLOCKOUT_PLANT", parent=r, sector=SECTOR,
            props={"asset_id": "plant_hanging_vine_%02d" % (i + 1),
                   "asset_type": "plant"})


def build_posters():
    """Cuadros de la pared oeste. Cada uno es un plano con su propia textura."""
    r = root("POSTERS_WEST_ROOT", (X_WALL, 0.0, 0.0), PROPS, SECTOR,
             {"asset_id": "posters_west", "asset_type": "poster_group"})
    # (nombre, y, z, ancho, alto)
    layout = [
        ("POSTER_WEST_01", -3.35, 2.00, 0.55, 0.95),
        ("POSTER_WEST_02", -2.55, 2.12, 0.85, 0.60),
        ("POSTER_WEST_03", -3.45, 1.30, 0.36, 0.30),
        ("POSTER_WEST_04", -3.02, 1.27, 0.32, 0.28),
        ("POSTER_WEST_05", -0.95, 1.85, 0.45, 0.60),
    ]
    for name, y, z, w, h in layout:
        box(name, (0.025, w, h), (0.0125, y, z), PROPS,
            "MAT_BLOCKOUT_PAPER", parent=r, sector=SECTOR,
            props={"asset_id": name.lower(), "asset_type": "poster",
                   "texture_id": "TEX_" + name,
                   "notes": "imagen concreta a definir por el usuario"})


def build_plant_floor():
    r = root("PLANT_WEST_01_ROOT", (-4.18, -3.72, 0.0), PROPS, SECTOR,
             {"asset_id": "plant_west_01", "asset_type": "plant"})
    box("PLANT_WEST_POT", (0.34, 0.34, 0.38), (0.0, 0.0, 0.19), PROPS,
        "MAT_BLOCKOUT_CERAMIC", parent=r, sector=SECTOR,
        props={"asset_id": "plant_west_pot", "asset_type": "plant"})
    box("PLANT_WEST_FOLIAGE", (0.56, 0.56, 0.82), (0.02, 0.0, 0.79), PROPS,
        "MAT_BLOCKOUT_PLANT", parent=r, sector=SECTOR,
        props={"asset_id": "plant_west_foliage", "asset_type": "plant"})


def build_tracklight():
    r = root("TRACKLIGHT_WEST_ROOT", (-3.92, -2.10, 2.84), PROPS, SECTOR,
             {"asset_id": "tracklight_west", "asset_type": "light_fixture",
              "notes": "el fixture es prop; las luces van en 40_LIGHTS"})
    box("TRACKLIGHT_BAR", (0.06, 1.50, 0.06), (0.0, 0.0, 0.0), PROPS,
        "MAT_BLOCKOUT_PLASTIC_BLACK", parent=r, sector=SECTOR,
        props={"asset_id": "tracklight_bar", "asset_type": "light_fixture"})
    for i, y in enumerate((-0.60, 0.0, 0.60)):
        box("TRACKLIGHT_MOUNT_%02d" % (i + 1), (0.08, 0.08, 0.09),
            (0.0, y, -0.07), PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK",
            parent=r, sector=SECTOR,
            props={"asset_id": "tracklight_mount_%02d" % (i + 1),
                   "asset_type": "light_fixture"})
        box("TRACKLIGHT_HEAD_%02d" % (i + 1), (0.14, 0.14, 0.19),
            (-0.03, y, -0.21), PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK",
            rotation=(0, math.radians(18), 0), parent=r, sector=SECTOR,
            props={"asset_id": "tracklight_head_%02d" % (i + 1),
                   "asset_type": "light_fixture"})
        box("TRACKLIGHT_BULB_%02d" % (i + 1), (0.10, 0.10, 0.01),
            (-0.06, y, -0.30), PROPS, "MAT_BLOCKOUT_EMISSIVE",
            parent=r, sector=SECTOR,
            props={"asset_id": "tracklight_bulb_%02d" % (i + 1),
                   "asset_type": "light_fixture"})


def build_vase_shelf():
    """Estanteria de vasijas en el retranqueo, esquina noroeste."""
    r = root("SHELF_VASES_NW_ROOT", (X_RECESS, 3.25, 0.0), FURN, SECTOR,
             {"asset_id": "shelf_vases_nw", "asset_type": "shelf",
              "reference_group": "entrada"})
    for side in (-1, 1):
        box("SHELF_VASES_SIDE_%s" % ("S" if side < 0 else "N"),
            (0.30, 0.04, 1.28), (0.15, side * 0.63, 1.78), FURN,
            "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
            props={"asset_id": "shelf_vases_side", "asset_type": "shelf"})
    for i, z in enumerate((1.16, 1.75, 2.34)):
        box("SHELF_VASES_BOARD_%02d" % (i + 1), (0.30, 1.30, 0.04),
            (0.15, 0.0, z), FURN, "MAT_BLOCKOUT_WOOD",
            parent=r, sector=SECTOR,
            props={"asset_id": "shelf_vases_board_%02d" % (i + 1),
                   "asset_type": "shelf"})
    box("SHELF_VASES_DIVIDER", (0.30, 0.04, 1.28), (0.15, 0.0, 1.78), FURN,
        "MAT_BLOCKOUT_WOOD", parent=r, sector=SECTOR,
        props={"asset_id": "shelf_vases_divider", "asset_type": "shelf"})

    # Vasijas: cajas de distinto porte sobre cada balda
    vases = [(-0.42, 1.16, 0.16, 0.22, "MAT_BLOCKOUT_ACCENT_ORANGE"),
             (-0.18, 1.16, 0.13, 0.17, "MAT_BLOCKOUT_CERAMIC"),
             (0.22, 1.16, 0.15, 0.20, "MAT_BLOCKOUT_CERAMIC"),
             (0.48, 1.16, 0.12, 0.15, "MAT_BLOCKOUT_FABRIC"),
             (-0.35, 1.75, 0.14, 0.19, "MAT_BLOCKOUT_CERAMIC"),
             (-0.10, 1.75, 0.12, 0.24, "MAT_BLOCKOUT_ACCENT_ORANGE"),
             (0.30, 1.75, 0.16, 0.18, "MAT_BLOCKOUT_CERAMIC"),
             (-0.30, 2.34, 0.13, 0.16, "MAT_BLOCKOUT_CERAMIC"),
             (0.28, 2.34, 0.15, 0.21, "MAT_BLOCKOUT_CERAMIC")]
    for i, (y, zbase, w, h, m) in enumerate(vases):
        box("VASE_NW_%02d" % (i + 1), (w, w, h), (0.15, y, zbase + 0.02 + h / 2),
            PROPS, m, parent=r, sector=SECTOR,
            props={"asset_id": "vase_nw_%02d" % (i + 1),
                   "asset_type": "decoration"})
    box("PLANT_SHELF_NW", (0.30, 0.30, 0.34), (0.15, 0.05, 2.53), PROPS,
        "MAT_BLOCKOUT_PLANT", parent=r, sector=SECTOR,
        props={"asset_id": "plant_shelf_nw", "asset_type": "plant"})

    for i, y in enumerate((2.95, 3.28)):
        box("FRAME_NW_%02d" % (i + 1), (0.025, 0.18, 0.24),
            (X_RECESS + 0.0125, y, 0.98), PROPS, "MAT_BLOCKOUT_PAPER",
            sector=SECTOR,
            props={"asset_id": "frame_nw_%02d" % (i + 1),
                   "asset_type": "poster", "texture_id": "TEX_FRAME_NW_%02d" % (i + 1)})


def build_bottle_rack():
    """Rack negro de botellas al pie de la escalera."""
    r = root("BOTTLE_RACK_01_ROOT", (-2.00, 2.42, 0.0), FURN, SECTOR,
             {"asset_id": "bottle_rack_01", "asset_type": "rack",
              "reference_group": "entrada"})
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("RACK_POST_%d%d" % (sx > 0, sy > 0), (0.04, 0.04, 1.16),
                (sx * 0.19, sy * 0.16, 0.58), FURN, "MAT_BLOCKOUT_METAL",
                parent=r, sector=SECTOR,
                props={"asset_id": "rack_post", "asset_type": "rack"})
    colors = ["MAT_BLOCKOUT_ACCENT_ORANGE", "MAT_BLOCKOUT_ACCENT_BLUE",
              "MAT_BLOCKOUT_EMISSIVE", "MAT_BLOCKOUT_PLANT"]
    for i, z in enumerate((0.16, 0.48, 0.80, 1.12)):
        box("RACK_SHELF_%02d" % (i + 1), (0.42, 0.36, 0.03), (0.0, 0.0, z),
            FURN, "MAT_BLOCKOUT_METAL", parent=r, sector=SECTOR,
            props={"asset_id": "rack_shelf_%02d" % (i + 1),
                   "asset_type": "rack"})
        for j, x in enumerate((-0.12, 0.0, 0.12)):
            h = 0.16 + ((i + j) % 3) * 0.03
            box("RACK_BOTTLE_%02d_%02d" % (i + 1, j + 1), (0.08, 0.08, h),
                (x, 0.0, z + 0.015 + h / 2), PROPS, colors[(i + j) % 4],
                parent=r, sector=SECTOR,
                props={"asset_id": "rack_bottle_%02d_%02d" % (i + 1, j + 1),
                       "asset_type": "decoration"})


def main():
    global FURN, PROPS
    FURN = col("20_FURNITURE")
    PROPS = col("30_PROPS")

    removed = clear_sector(SECTOR)
    build_desk()
    build_computer()
    build_chair()
    build_wall_shelf()
    build_posters()
    build_plant_floor()
    build_tracklight()
    build_vase_shelf()
    build_bottle_rack()

    print("Objetos del sector WEST reemplazados:", removed)
    save(out_path(sys.argv, bpy.data.filepath))


main()
