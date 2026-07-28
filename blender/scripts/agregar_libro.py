"""
AGREGA UN LIBRO ABIERTO AL ARCHIVO DE POSE
==========================================

Un prop más, con la misma lógica que el teléfono: cuelga del hueso de la mano
izquierda, se mueve como un objeto solo en Modo Objeto, y cada pose decide si
lo lleva o no con el ojito del Outliner.

NO toca la pose que tenga el archivo: sólo agrega objetos.

Cinco cajas, 60 caras: el lomo (que es el objeto que se agarra y del que
cuelgan los demás), las dos tapas y los dos bloques de hojas, abiertos en V.
Los colores salen de los que ya usa la habitación —`MAT_BLOCKOUT_PAPER` para
el papel y la gama del cuero de `MAT_NOTEBOOK_LEATHER` para la tapa— así que
no desentona.

Es idempotente: borra el libro anterior y lo rehace.

No lo corras a mano: lo llama `tools/libro.sh`.

Uso:
  Blender --background blender/AVATAR_POSE.blend \
    --python blender/scripts/agregar_libro.py -- --guardar
"""

import math
import sys

import bpy
from mathutils import Matrix, Vector

PREFIJO = "LIBRO"
HUESO = "LeftHand"

# Medidas de un libro de bolsillo abierto, en metros.
ALTO = 0.212          # de arriba a abajo de la página
ANCHO = 0.150         # de una página, no del libro abierto
TAPA = 0.007
HOJAS = 0.016
LOMO = (0.020, ALTO + 0.006, 0.026)
APERTURA = 13         # grados que sube cada mitad desde el plano

# Dónde aparece respecto de la punta de la mano izquierda. Es sólo un punto de
# partida: se acomoda a mano con G y R en Modo Objeto.
DESDE_LA_MANO = Vector((0.075, -0.045, 0.045))

PAPEL = (0.820, 0.800, 0.750, 1.0)      # el mismo de MAT_BLOCKOUT_PAPER
CUERO = (0.085, 0.055, 0.042, 1.0)      # la gama de MAT_NOTEBOOK_LEATHER


def material(nombre, color, rugosidad):
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = rugosidad
    return mat


def caja(nombre, tam, mat):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = nombre
    o.scale = tam
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


def main():
    guardar = "--guardar" in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

    arm = bpy.data.objects.get("AVATAR_RIG")
    if arm is None:
        raise SystemExit("el archivo no tiene AVATAR_RIG")

    for o in [o for o in bpy.data.objects if o.name.startswith(PREFIJO)]:
        bpy.data.objects.remove(o, do_unlink=True)

    tapa_mat = material("MAT_LIBRO_TAPA", CUERO, 0.62)
    papel_mat = material("MAT_LIBRO_HOJAS", PAPEL, 0.92)

    # El lomo es el objeto que se agarra: origen en el centro del libro.
    lomo = caja(PREFIJO, LOMO, tapa_mat)

    partes = []
    for lado, signo in (("IZQ", -1), ("DER", 1)):
        giro = Matrix.Rotation(math.radians(APERTURA) * -signo, 4, "Y")
        # Cada mitad se levanta desde el lomo, así el libro queda abierto en V.
        base = giro @ Matrix.Translation(Vector((signo * (ANCHO / 2 + LOMO[0] / 2), 0, 0)))
        tapa = caja(f"{PREFIJO}_TAPA_{lado}", (ANCHO, ALTO, TAPA), tapa_mat)
        tapa.matrix_world = base @ Matrix.Translation(Vector((0, 0, -TAPA / 2)))
        hojas = caja(f"{PREFIJO}_HOJAS_{lado}", (ANCHO - 0.006, ALTO - 0.008, HOJAS), papel_mat)
        hojas.matrix_world = base @ Matrix.Translation(Vector((0, 0, HOJAS / 2)))
        partes += [tapa, hojas]

    for p in partes:
        mundo = p.matrix_world.copy()
        p.parent = lomo
        bpy.context.view_layer.update()
        p.matrix_parent_inverse = lomo.matrix_world.inverted()
        p.matrix_world = mundo

    # Colgarlo de la mano izquierda, igual que el teléfono, y orientarlo para
    # que las hojas miren a la cara.
    mano = arm.pose.bones[HUESO]
    centro = (arm.matrix_world @ mano.tail) + DESDE_LA_MANO
    ojos = arm.matrix_world @ arm.pose.bones["Head"].tail
    normal = (ojos - centro).normalized()
    largo = Vector((0, 0, 1))
    if abs(largo.dot(normal)) > 0.95:
        largo = Vector((0, -1, 0))
    largo = (largo - normal * largo.dot(normal)).normalized()
    ancho = largo.cross(normal).normalized()

    lomo.parent = arm
    lomo.parent_type = "BONE"
    lomo.parent_bone = HUESO
    bpy.context.view_layer.update()
    lomo.matrix_world = Matrix((
        (ancho.x, largo.x, normal.x, centro.x),
        (ancho.y, largo.y, normal.y, centro.y),
        (ancho.z, largo.z, normal.z, centro.z),
        (0, 0, 0, 1)))

    # A la misma colección que el avatar, para que no quede en REFERENCIA.
    col = bpy.data.collections.get("AVATAR") or bpy.context.scene.collection
    for o in [lomo] + partes:
        for vieja in list(o.users_collection):
            vieja.objects.unlink(o)
        col.objects.link(o)
        o.hide_set(False)

    bpy.context.view_layer.update()
    if guardar:
        bpy.ops.wm.save_mainfile()

    print("LIBRO=" + str({
        "objetos": [o.name for o in [lomo] + partes],
        "caras": sum(len(o.data.polygons) for o in [lomo] + partes),
        "centro": [round(v, 3) for v in lomo.matrix_world.translation],
        "guardado": guardar,
    }))


main()
