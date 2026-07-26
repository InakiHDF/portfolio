"""
APLICAR TEXTURAS DE SUPERFICIE
==============================

Dos cosas:

1. UVs por proyeccion cubica EN ESPACIO DE MUNDO. Cada cara se proyecta
   segun el eje dominante de su normal, dividido por el tamano de baldosa.
   Consecuencia: la veta no se corta al pasar de una pieza a la otra, y no
   hay que desplegar nada a mano en 300 objetos.

2. Se reconecta cada material del blockout a su textura, con interpolacion
   "Closest": el texel tiene que verse como bloque.

Baldosa = 1.60 m (64 texels de 2.5 cm). Ese 2.5 cm es la regla del proyecto.

No toca los objetos que ya tienen textura de contenido (MAT_TEX_*).

Uso:
  Blender --background ARCHIVO.blend --python apply_surface_textures.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import out_path, save

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(REPO, "blender", "textures", "surface")
TILE_M = 1.60

MAPA = {
    "MAT_BLOCKOUT_ARCH":         "TEX_ARCH.png",
    "MAT_BLOCKOUT_FLOOR":        "TEX_FLOOR.png",
    "MAT_BLOCKOUT_WOOD":         "TEX_WOOD.png",
    "MAT_BLOCKOUT_WOOD_LIGHT":   "TEX_WOOD_LIGHT.png",
    "MAT_BLOCKOUT_RUG":          "TEX_RUG.png",
    "MAT_BLOCKOUT_FABRIC":       "TEX_FABRIC.png",
    "MAT_BLOCKOUT_FABRIC_LIGHT": "TEX_FABRIC_LIGHT.png",
    "MAT_BLOCKOUT_STAIR":        "TEX_STAIR.png",
    "MAT_BLOCKOUT_METAL":        "TEX_METAL.png",
    "MAT_BLOCKOUT_SKIRTING":     "TEX_SKIRTING.png",
    "MAT_BLOCKOUT_DOOR":         "TEX_DOOR.png",
    "MAT_BLOCKOUT_SCREEN":       "TEX_SCREEN.png",
    "MAT_BLOCKOUT_PLASTIC_BLACK": "TEX_PLASTIC_BLACK.png",
    "MAT_BLOCKOUT_PAPER":        "TEX_PAPER.png",
    "MAT_BLOCKOUT_PLANT":        "TEX_PLANT.png",
    "MAT_BLOCKOUT_CERAMIC":      "TEX_CERAMIC.png",
    "MAT_BLOCKOUT_ACCENT_BLUE":  "TEX_ACCENT_BLUE.png",
    "MAT_BLOCKOUT_PLASTIC_BLUE": "TEX_PLASTIC_BLUE.png",
    "MAT_BLOCKOUT_ACCENT_ORANGE": "TEX_ACCENT_ORANGE.png",
    "MAT_BLOCKOUT_PLASTIC_LIGHT": "TEX_PLASTIC_LIGHT.png",
    "MAT_BLOCKOUT_WOOD_PLAIN":   "TEX_WOOD_PLAIN.png",
    "MAT_NOTEBOOK_LEATHER":      "TEX_NOTEBOOK_LEATHER.png",
    "MAT_SCREEN_PROJ":           "TEX_SCREEN_PROJ.png",
}

# Estos NO se proyectan en mundo: la textura se mapea una sola vez sobre el
# objeto, para que su dibujo (orilla, motivo) caiga donde tiene que caer.
UV_UNICA = {"MAT_BLOCKOUT_RUG", "MAT_SCREEN_PROJ"}


def uv_cubica(obj):
    """Proyeccion cubica en mundo. Devuelve cuantas caras mapeo."""
    mesh = obj.data
    if not mesh.polygons:
        return 0
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active.data

    mw = obj.matrix_world
    nm = mw.to_3x3().inverted_safe().transposed()

    for poly in mesh.polygons:
        n = nm @ poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            c = mw @ mesh.vertices[mesh.loops[li].vertex_index].co
            if ax == 0:                      # cara mirando a X: se usa Y,Z
                u, v = c.y, c.z
            elif ax == 1:                    # cara mirando a Y: se usa X,Z
                u, v = c.x, c.z
            else:                            # cara horizontal: se usa X,Y
                u, v = c.x, c.y
            uv[li].uv = (u / TILE_M, v / TILE_M)
    return len(mesh.polygons)


def uv_unica(obj):
    """La textura entera, una sola vez, sobre la cara mas grande del objeto."""
    mesh = obj.data
    if not mesh.polygons:
        return 0
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active.data

    co = [v.co for v in mesh.vertices]
    ext = [max(c[i] for c in co) - min(c[i] for c in co) for i in range(3)]
    fino = ext.index(min(ext))
    ejes = [i for i in range(3) if i != fino]
    lo = [min(c[i] for c in co) for i in range(3)]
    rango = [max(ext[i], 1e-6) for i in range(3)]

    for poly in mesh.polygons:
        for li in poly.loop_indices:
            c = mesh.vertices[mesh.loops[li].vertex_index].co
            uv[li].uv = ((c[ejes[0]] - lo[ejes[0]]) / rango[ejes[0]],
                         (c[ejes[1]] - lo[ejes[1]]) / rango[ejes[1]])
    return len(mesh.polygons)


def conectar(mat, archivo):
    """Mete la imagen en el Base Color conservando la rugosidad."""
    path = os.path.join(TEX, archivo)
    if not os.path.exists(path):
        return False
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return False

    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
    if tex is None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.location = (-360, 120)
    img = bpy.data.images.get(archivo)
    if img is None:
        img = bpy.data.images.load(path)
    tex.image = img
    tex.interpolation = "Closest"
    tex.extension = "REPEAT"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return True


def main():
    protegidos = 0
    por_material = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.data.materials:
            continue
        nombres = [m.name for m in obj.data.materials if m]
        if any(n.startswith("MAT_TEX_") for n in nombres):
            protegidos += 1
            continue
        if not any(n in MAPA for n in nombres):
            continue
        por_material.setdefault(nombres[0], []).append(obj)

    total_caras = 0
    for nombre, objs in sorted(por_material.items()):
        mat = bpy.data.materials.get(nombre)
        if not conectar(mat, MAPA[nombre]):
            print("  sin textura:", nombre)
            continue
        proyecta = uv_unica if nombre in UV_UNICA else uv_cubica
        caras = sum(proyecta(o) for o in objs)
        total_caras += caras
        print("  %-28s %3d objetos %5d caras  %s  <- %s"
              % (nombre, len(objs), caras,
                 "unica " if nombre in UV_UNICA else "cubica", MAPA[nombre]))

    # Segunda pasada: TODA malla tiene que quedar con UVs, aunque su material
    # no lleve textura. Sin UVs no se puede hornear luz despues, y ademas el
    # GLB sale con mallas incompletas.
    sueltas = 0
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.data.polygons:
            continue
        if o.data.uv_layers and len(o.data.uv_layers.active.data):
            continue
        uv_cubica(o)
        sueltas += 1
    if sueltas:
        print("  UVs de respaldo (material sin textura): %d mallas" % sueltas)

    print("\nCaras mapeadas: %d   |  intactos por tener contenido: %d"
          % (total_caras, protegidos))
    print("Baldosa: %.2f m  =  64 texels de %.1f cm" % (TILE_M, TILE_M / 64 * 100))
    save(out_path(sys.argv, bpy.data.filepath))


main()
