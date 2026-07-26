"""
PROFUNDIDAD Y BRILLOS  (sector "LIGHTS2")
=========================================

Tres cosas.

1. PROFUNDIDAD DEL RETRANQUEO. El problema es real y tiene una causa
   concreta: la luz de ambiente es una cupula perfectamente pareja, y una
   cupula pareja llega igual al fondo de un nicho que a la cara de enfrente.
   Sin oclusion, un retranqueo de 46 cm no se distingue de una pared plana.

   Se ataca por dos lados a la vez, porque ninguno de los dos alcanza solo:

     a) Se enciende el GI rapido de EEVEE, que es una oclusion por trazado.
        Oscurece TODO rincon de la escena por geometria, no solo este.
     b) Se agrega una luz rasante sobre la cara adelantada de la pared
        oeste. Rasante quiere decir casi paralela a la pared: ilumina lo
        que sobresale y no entra en el nicho.

2. La pantalla de proyeccion emite un poco. No proyecta nada: solo brilla
   lo suficiente para ser una fuente mas del cuarto.

3. La lampara de lava vuelve a tener su luz, ahora anclada a la campana
   nueva y con mas radio para que lave lo que tiene alrededor.

Uso:
  Blender --background ARCHIVO.blend --python tune_depth_and_glow.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import col, tag, clear_sector, out_path, save

SECTOR = "LIGHTS2"


def oclusion():
    """GI rapido: es lo que hace que un rincon se vea como rincon."""
    ev = bpy.context.scene.eevee
    ajustes = {
        "use_raytracing": True,
        "use_fast_gi": True,
        "fast_gi_method": "AMBIENT_OCCLUSION_ONLY",
        "fast_gi_resolution": "1",
        "fast_gi_ray_count": 4,
        "fast_gi_step_count": 12,
        "fast_gi_distance": 0.9,      # alcance: un nicho de 46 cm entra holgado
        "fast_gi_thickness_near": 0.05,
        "fast_gi_quality": 0.25,
    }
    puestos = []
    for k, v in ajustes.items():
        if hasattr(ev, k):
            try:
                setattr(ev, k, v)
                puestos.append(k)
            except (TypeError, ValueError) as e:
                print("   no acepta %s=%r (%s)" % (k, v, e))
    print("  oclusion: %d ajustes aplicados, alcance %.2f m"
          % (len(puestos), ajustes["fast_gi_distance"]))


def luz_rasante():
    """Area alargada casi pegada a la pared oeste, mirando al norte.

    Al ser rasante, la cara adelantada recibe luz y el fondo del nicho no.
    Esa diferencia es la que devuelve la profundidad."""
    d = bpy.data.lights.new("LIGHT_WEST_GRAZE_DATA", type="AREA")
    d.shape, d.size, d.size_y = "RECTANGLE", 3.6, 0.30
    d.energy, d.color = 26.0, (1.0, 0.82, 0.62)
    o = bpy.data.objects.new("LIGHT_WEST_GRAZE", d)
    # Pegada a la cara adelantada (x = -4.035), a media altura, mirando al norte
    o.location = (-3.90, -1.30, 1.85)
    o.rotation_euler = (math.radians(90), 0, math.radians(196))
    col("40_LIGHTS").objects.link(o)
    tag(o, SECTOR, {"asset_id": "light_west_graze", "asset_type": "light",
                    "notes": "rasante sobre la pared oeste; NO debe entrar al "
                             "retranqueo, de eso depende la profundidad"})
    print("  luz rasante en la pared oeste: area de 3.6 x 0.3 m")


def brillo_pantalla():
    m = bpy.data.materials.get("MAT_SCREEN_PROJ")
    if not m:
        print("  no esta MAT_SCREEN_PROJ")
        return
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not b:
        return
    b.inputs["Emission Color"].default_value = (0.82, 0.86, 0.95, 1.0)
    b.inputs["Emission Strength"].default_value = 0.28
    print("  pantalla: emision 0.28, sin proyectar nada")

    luz = bpy.data.objects.get("LIGHT_SCREEN")
    if luz:
        luz.data.energy = 12.0
        print("  LIGHT_SCREEN a %.0f W" % luz.data.energy)


def luz_lava():
    campana = bpy.data.objects.get("LAVA_CAMPANA")
    luz = bpy.data.objects.get("LIGHT_LAVA")
    if not campana or not luz:
        print("  falta la campana o la luz de la lava")
        return
    v = campana.matrix_world.translation
    luz.location = (v.x, v.y, v.z)
    luz.data.energy = 26.0
    luz.data.shadow_soft_size = 0.14
    luz.data.color = (1.0, 0.46, 0.14)
    if "_energia_base" in luz:
        luz["_energia_base"] = luz.data.energy
    print("  lava: luz reubicada en la campana, %.0f W, radio %.2f"
          % (luz.data.energy, luz.data.shadow_soft_size))


def main():
    print("Objetos LIGHTS2 reemplazados:", clear_sector(SECTOR))
    oclusion()
    luz_rasante()
    brillo_pantalla()
    luz_lava()
    save(out_path(sys.argv, bpy.data.filepath))


main()
