"""
APLICAR TEXTURAS DE CONTENIDO
=============================

Automatico: por cada PNG en textures/content/ que se llame igual que un
objeto de la escena, le pone esa imagen en su cara visible.

Como sabe cual es la cara visible: prueba las seis direcciones (+-X, +-Y, +-Z)
y se queda con la que mas apunta hacia CAM_ISO_SW. No sirve elegir "la cara
mas grande": en un libro parado la cara visible es el lomo, que es la mas
chica de las tres.

Los ejes de la imagen se toman desde el punto de vista de quien mira, no
desde la normal, si no la imagen sale espejada y dada vuelta.

Filtro "Closest": el texel se tiene que ver como bloque.

Uso:
  Blender --background ARCHIVO.blend --python apply_content_textures.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lib_blockout import out_path, save

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(REPO, "blender", "textures", "content")

EJES = [Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                            (0, -1, 0), (0, 0, 1), (0, 0, -1))]

# Casos donde la regla automatica no acierta. Una consola es mas ancha que
# alta, asi que su cara "grande" es la tapa; pero lo que se ve dentro del
# mueble es el FRENTE.
FORZADOS = {
    "RETRO_CONSOLE_01": (0, -1, 0),
    "RETRO_CONSOLE_02": (0, -1, 0),
    "RETRO_CONSOLE_03": (0, -1, 0),
}


def cara_visible(obj, camara):
    """Que cara lleva la imagen.

    No alcanza con "la que mas mira a la camara": un cuadro visto de costado
    elige su canto, que mide 3 cm. Y tampoco alcanza con "la mas grande": en
    un libro parado la cara util es el lomo, que es la mas chica de las tres,
    porque las tapas las tapan los libros de al lado.

    Entonces: primero se decide QUE EJE segun la forma del objeto, y recien
    despues el signo, con la camara.
    """
    if obj.name in FORZADOS:
        return Vector(FORZADOS[obj.name])
    d = list(obj.dimensions)
    fino = d.index(min(d))
    tipo = obj.get("asset_type")
    # Un libro PARADO muestra el lomo; uno ACOSTADO muestra la tapa. Se
    # distinguen por donde cae la dimension mas fina: si es la vertical, el
    # libro esta acostado y va como cualquier placa.
    if tipo in ("book", "books") and fino != 2:
        eje = next(i for i in range(3) if i != fino and i != 2)
    else:
        eje = fino

    rot = obj.matrix_world.to_3x3()
    hacia = (camara.matrix_world.translation - obj.matrix_world.translation).normalized()
    positivo = Vector([1 if i == eje else 0 for i in range(3)])
    return positivo if (rot @ positivo).normalized().dot(hacia) > 0 else -positivo


def uv_frontal(obj, facing):
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active.data

    f = Vector(facing).normalized()
    mirando = -f
    arriba = Vector((0, 0, 1))
    right = mirando.cross(arriba)
    if right.length < 1e-4:
        right = Vector((1, 0, 0))
    right.normalize()
    up = right.cross(mirando).normalized()

    co = [v.co for v in mesh.vertices]
    us = [c.dot(right) for c in co]
    vs = [c.dot(up) for c in co]
    u0, du = min(us), max(1e-6, max(us) - min(us))
    v0, dv = min(vs), max(1e-6, max(vs) - min(vs))

    frontales = 0
    for poly in mesh.polygons:
        de_frente = poly.normal.dot(f) > 0.7
        frontales += de_frente
        for li in poly.loop_indices:
            c = mesh.vertices[mesh.loops[li].vertex_index].co
            uv[li].uv = (((c.dot(right) - u0) / du, (c.dot(up) - v0) / dv)
                         if de_frente else (0.004, 0.004))
    return frontales


def material_imagen(nombre, path):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.get(os.path.basename(path))
    if img is None:
        img = bpy.data.images.load(path)
    img.reload()
    tex.image = img
    tex.interpolation = "Closest"
    tex.extension = "EXTEND"
    bsdf.inputs["Roughness"].default_value = 0.88
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    out.location, bsdf.location, tex.location = (300, 0), (0, 0), (-320, 0)
    return m


def main():
    camara = bpy.data.objects.get("CAM_ISO_SW")
    if camara is None:
        raise SystemExit("no esta CAM_ISO_SW: sin camara no se cual es la cara visible")

    por_grupo = {}
    for archivo in sorted(os.listdir(TEX)):
        if not archivo.endswith(".png") or archivo.startswith("POOL_"):
            continue
        nombre = archivo[:-4]
        obj = bpy.data.objects.get(nombre)
        if obj is None or obj.type != "MESH":
            continue
        facing = cara_visible(obj, camara)
        uv_frontal(obj, facing)
        obj.data.materials.clear()
        obj.data.materials.append(
            material_imagen("MAT_TEX_" + nombre, os.path.join(TEX, archivo)))
        obj["texture_id"] = archivo
        grupo = nombre.rsplit("_", 1)[0]
        por_grupo.setdefault(grupo, []).append(tuple(facing))

    total = 0
    for grupo, caras in sorted(por_grupo.items()):
        dirs = {c for c in caras}
        print("  %-18s %2d objetos   cara visible: %s"
              % (grupo, len(caras),
                 ", ".join("(%g,%g,%g)" % d for d in sorted(dirs))))
        total += len(caras)
    print("\nTexturas de contenido aplicadas:", total)
    save(out_path(sys.argv, bpy.data.filepath))


main()
