"""
RIG DE ILUMINACION  (sector "LIGHTS")
=====================================

Crea las luces en 40_LIGHTS. Ninguna posicion es inventada: cada una se
cuelga de un objeto que ya existe en el blockout (la lampara del escritorio,
la vela, la lampara de lava, los spots del riel, las pantallas). La luz
visual va separada del objeto emisivo, como pide el brief.

Las tiras de led debajo de las baldas son el recurso que mas se repite en
basement.studio y no existian en el blockout: se agregan como area chatas.

Cada luz queda con nombre propio para poder ajustarla de a una. Volver a
correr el script las reemplaza todas.

Uso:
  Blender --background ARCHIVO.blend --python setup_lights.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import col, tag, clear_sector, out_path, save

SECTOR = "LIGHTS"
LIGHTS = None

WARM  = (1.00, 0.66, 0.34)   # tungsteno, ~2700 K
AMBER = (1.00, 0.50, 0.16)   # vela y lava, mas caliente
COOL  = (0.66, 0.79, 1.00)   # pantallas y leds


def anchor(name, offset=(0, 0, 0)):
    """Posicion de un objeto del blockout, con corrimiento opcional."""
    o = bpy.data.objects.get(name)
    if not o:
        print("  sin ancla:", name)
        return None
    v = o.matrix_world.translation
    return (v.x + offset[0], v.y + offset[1], v.z + offset[2])


def add(name, kind, loc, energy, color, **kw):
    if loc is None:
        return None
    d = bpy.data.lights.new(name + "_DATA", type=kind)
    d.energy, d.color = energy, color
    if kind == "POINT":
        d.shadow_soft_size = kw.get("radius", 0.08)
    elif kind == "AREA":
        d.shape = "RECTANGLE"
        d.size, d.size_y = kw.get("size", (1.0, 0.2))
    elif kind == "SPOT":
        d.spot_size = kw.get("cone", math.radians(70))
        d.spot_blend = 0.5
        d.shadow_soft_size = kw.get("radius", 0.05)
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = kw.get("rot", (0, 0, 0))
    LIGHTS.objects.link(o)
    tag(o, SECTOR, {"asset_id": name.lower(), "asset_type": "light",
                    "notes": kw.get("notes", "")})
    return o


def main():
    global LIGHTS
    LIGHTS = col("40_LIGHTS")
    print("Luces reemplazadas:", clear_sector(SECTOR))

    DOWN = (0, 0, 0)                       # area mirando hacia abajo
    WALL_W = (0, math.radians(90), 0)      # area mirando al este
    NORTH = (math.radians(90), 0, math.radians(180))

    # --- practicas puntuales -------------------------------------------
    add("LIGHT_DESK_WEST", "POINT", anchor("LAMP_DESK_BULB", (0, 0, -0.04)),
        22, WARM, radius=0.05, notes="velador del setup oeste")
    add("LIGHT_TABLE_EAST", "POINT", anchor("LAMP_EAST_BULB", (0, 0, -0.04)),
        26, WARM, radius=0.05, notes="lampara de la mesa de trabajo")
    add("LIGHT_CANDLE", "POINT", anchor("SHELF_CANDLE"),
        6, AMBER, radius=0.04, notes="vela del estante oeste")
    add("LIGHT_LAVA", "POINT", anchor("LAVA_LAMP_GLASS"),
        14, AMBER, radius=0.06, notes="lampara de lava")

    # --- riel del techo -------------------------------------------------
    for i in (1, 2, 3):
        add("LIGHT_TRACK_%02d" % i, "SPOT",
            anchor("TRACKLIGHT_BULB_%02d" % i, (0, 0, -0.03)),
            30, WARM, cone=math.radians(64), radius=0.04,
            rot=(math.radians(14), 0, 0),
            notes="spot del riel, lava la pared oeste")

    # --- pantallas -------------------------------------------------------
    add("LIGHT_SCREEN", "AREA", anchor("SCREEN_SURFACE", (0, -0.30, 0)),
        26, (0.80, 0.86, 1.00), size=(2.1, 1.2), rot=NORTH,
        notes="pantalla de proyeccion")
    for n, tag_ in (("MONITOR_MAIN_PANEL", "MAIN"), ("MONITOR_SIDE_PANEL", "SIDE")):
        add("LIGHT_MONITOR_" + tag_, "AREA", anchor(n, (0.10, 0, 0)),
            7, COOL, size=(0.34, 0.55), rot=WALL_W,
            notes="monitor del setup oeste")
    add("LIGHT_AMP", "POINT", anchor("AMPLIFIER_DISPLAY"),
        1.5, COOL, radius=0.03, notes="display del amplificador")
    add("LIGHT_PC", "POINT", anchor("PC_TOWER_LED_BAR"),
        2.5, COOL, radius=0.04, notes="leds de la torre")

    # --- tiras de led bajo las baldas -----------------------------------
    add("LIGHT_LED_RECORDS", "AREA", anchor("RECORDS_TOP", (0, -0.10, -0.06)),
        9, WARM, size=(1.9, 0.30), rot=DOWN,
        notes="tira bajo la tapa de la discoteca")
    add("LIGHT_LED_SHELF_WEST", "AREA", anchor("SHELF_DESK_BOARD", (0.06, 0, -0.05)),
        6, WARM, size=(1.6, 0.22), rot=DOWN,
        notes="tira bajo el estante del escritorio")
    for i in (1, 2, 3):
        add("LIGHT_LED_VASE_%02d" % i, "AREA",
            anchor("SHELF_VASES_BOARD_%02d" % i, (0.02, 0, -0.03)),
            5, WARM, size=(0.26, 1.20), rot=WALL_W,
            notes="tira en la estanteria de vasijas")

    # --- luz que baja del piso de arriba --------------------------------
    add("LIGHT_STAIRWELL", "AREA", (-3.0, 3.35, 2.78),
        14, WARM, size=(1.2, 1.2), rot=DOWN,
        notes="cae por el hueco de la escalera")

    # --- relleno general -------------------------------------------------
    add("LIGHT_AMBIENT_FILL", "AREA", (0.0, -0.5, 2.84),
        12, (0.48, 0.55, 0.72), size=(8.0, 6.0), rot=DOWN,
        notes="relleno frio; es la unica luz que NO existe como objeto en "
              "la escena. Es la primera que hay que bajar si se quiere mas "
              "penumbra")

    print("Luces creadas:", len(LIGHTS.objects))
    save(out_path(sys.argv, bpy.data.filepath))


main()
