"""
HAZ DEL PROYECTOR Y NIEBLA  (sector "BEAM")
===========================================

Dos caminos distintos para el mismo efecto, y conviene tener claro cual es
cual porque en la web se comportan MUY distinto:

  1. HAZ COMO GEOMETRIA. Un cono que va de la lente a la pantalla, con
     material emisivo y transparencia. Es una malla comun: viaja en el GLB y
     se ve igual en Blender que en el navegador, sin costo.

  2. NIEBLA VOLUMETRICA de escena. Hace que TODAS las luces dejen su rastro
     en el aire. Se ve mejor, pero es un efecto de motor: no se exporta. En
     three.js habria que rehacerlo con bloom y niebla, que se parece pero no
     es lo mismo.

Este script hace las dos para poder compararlas.

Uso:
  Blender --background ARCHIVO.blend --python add_projector_beam.py -- SALIDA.blend [niebla]
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lib_blockout import col, tag, clear_sector, out_path, save

SECTOR = "BEAM"


def material_haz():
    """Emisivo aditivo con caida hacia el borde del cono."""
    m = bpy.data.materials.get("MAT_PROJECTOR_BEAM")
    if m is None:
        m = bpy.data.materials.new("MAT_PROJECTOR_BEAM")
    m.use_nodes = True
    # Blender 5 renombro esto: sin BLENDED el cono sale macizo.
    for attr, valor in (("surface_render_method", "BLENDED"),
                        ("blend_method", "BLEND")):
        if hasattr(m, attr):
            try:
                setattr(m, attr, valor)
            except (TypeError, ValueError):
                pass
    m.use_backface_culling = False
    if hasattr(m, "use_transparent_shadow"):
        m.use_transparent_shadow = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    emis = nt.nodes.new("ShaderNodeEmission")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    fres = nt.nodes.new("ShaderNodeLayerWeight")

    emis.inputs["Color"].default_value = (0.78, 0.85, 1.0, 1.0)
    emis.inputs["Strength"].default_value = 0.40
    fres.inputs["Blend"].default_value = 0.35

    # Un haz se ve MAS en el borde, donde la mirada atraviesa mas aire, y
    # casi nada de frente. Por eso va el Fresnel, no el Facing.
    nt.links.new(fres.outputs["Fresnel"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emis.outputs["Emission"], mix.inputs[2])
    # Se limita cuanto llega a emitir: un haz nunca es opaco.
    tope = nt.nodes.new("ShaderNodeMath")
    tope.operation = "MULTIPLY"
    tope.inputs[1].default_value = 0.085
    tope.location = (100, 200)
    nt.links.new(fres.outputs["Fresnel"], tope.inputs[0])
    nt.links.new(tope.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    for n, loc in ((out, (400, 0)), (mix, (200, 0)), (emis, (0, -120)),
                   (trans, (0, 60)), (fres, (0, 200))):
        n.location = loc
    return m


def cono(nombre, origen, destino, r0, r1, lados=16):
    """Tronco de cono entre dos puntos del mundo."""
    d = Vector(destino) - Vector(origen)
    largo = d.length
    verts, faces = [], []
    for r, z in ((r0, 0.0), (r1, largo)):
        for i in range(lados):
            a = math.tau * i / lados
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(lados):
        j = (i + 1) % lados
        faces.append((i, j, j + lados, i + lados))

    mesh = bpy.data.meshes.new(nombre + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    o = bpy.data.objects.new(nombre, mesh)
    o.location = origen
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(material_haz())
    o.visible_shadow = False          # un haz no proyecta sombra
    col("30_PROPS").objects.link(o)
    tag(o, SECTOR, {"asset_id": nombre.lower(), "asset_type": "beam",
                    "notes": "malla: viaja en el GLB y se ve igual en la web"})
    return o


def haz_proyector():
    lente = bpy.data.objects.get("PROJECTOR_LENS")
    pantalla = bpy.data.objects.get("SCREEN_SURFACE")
    if not lente or not pantalla:
        print("  falta PROJECTOR_LENS o SCREEN_SURFACE")
        return
    a = lente.matrix_world.translation
    b = pantalla.matrix_world.translation
    # Arranca chico en la lente y termina del tamano de la pantalla
    # El haz cierra sobre el ALTO de la pantalla, no sobre el ancho: si se
    # toma el ancho, el cono tapa media pared.
    r1 = pantalla.dimensions.z * 0.52
    cono("PROJECTOR_BEAM", (a.x, a.y, a.z), (b.x, b.y, b.z), 0.045, r1)
    print("  haz: de la lente a la pantalla, %.2f m, de 4.5 cm a %.0f cm"
          % ((b - a).length, r1 * 100))


def niebla(densidad=0.0022):
    """Niebla de escena: hace visible el rastro de TODAS las luces."""
    w = bpy.context.scene.world
    nt = w.node_tree
    vol = next((n for n in nt.nodes if n.type == "VOLUME_SCATTER"), None)
    if vol is None:
        vol = nt.nodes.new("ShaderNodeVolumeScatter")
        vol.location = (-200, -260)
    vol.inputs["Color"].default_value = (0.88, 0.90, 1.0, 1.0)
    vol.inputs["Density"].default_value = densidad
    vol.inputs["Anisotropy"].default_value = 0.55      # dispersa hacia adelante
    salida = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    nt.links.new(vol.outputs["Volume"], salida.inputs["Volume"])

    ev = bpy.context.scene.eevee
    for k, v in (("use_volumetric_lights", True), ("use_volumetric_shadows", True),
                 ("volumetric_start", 0.1), ("volumetric_end", 30.0),
                 ("volumetric_tile_size", "2"), ("volumetric_samples", 96)):
        if hasattr(ev, k):
            try:
                setattr(ev, k, v)
            except (TypeError, ValueError):
                pass
    print("  niebla de escena: densidad %.4f" % densidad)


def main():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    con_niebla = len(extra) > 1 and extra[1] == "niebla"

    print("Objetos BEAM reemplazados:", clear_sector(SECTOR))
    haz_proyector()
    if con_niebla:
        niebla()
    else:
        print("  sin niebla (pasar 'niebla' como segundo argumento)")
    save(out_path(sys.argv, bpy.data.filepath))


main()
