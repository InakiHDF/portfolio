"""
CREA EL ARCHIVO DE POSE  ->  blender/AVATAR_POSE.blend
=====================================================

OJO: esto reconstruye el archivo desde cero y borra la pose que tenga.
Sólo se corre para empezar de nuevo.

La pose es simplemente la pose del rig guardada en el archivo, como cualquier
cosa que uno guarda en Blender. Sin Actions ni fotogramas de por medio.

  (Hubo una versión con Actions. Una Action con fotogramas clavados le pisa la
  pose viva cada vez que Blender recalcula la animación, y cambiar de modo con
  Tab la recalcula: borró una pose entera. No volver ahí.)

Qué trae el archivo:

  - El avatar de Avaturn SIN tocar: geometría y texturas originales. Lo que lo
    vuelve retro lo hace `tools/avatar.sh` al exportar, no acá; posar sobre una
    malla ya decimada es posar a ciegas.
  - La habitación entera como referencia, en la colección REFERENCIA y
    bloqueada con `hide_select` para que no se pueda mover ni borrar sin
    querer. Las coordenadas son las mismas que las del archivo maestro: donde
    quede acá queda en la página.
  - Un teléfono colgado de la mano izquierda. Si la pose no lo lleva, se borra.

Regla de exportación: sale TODO lo que no esté en REFERENCIA.

Uso:
  Blender --background blender/HABITACION_v020_CONSOLE_UI.blend \
    --python blender/scripts/avatar_pose_file.py -- blender/poses/cama_celular.blend
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(AQUI, "..", "model-2.glb")

COL_AVATAR = "AVATAR"
COL_REFERENCIA = "REFERENCIA"

# --- Ubicación de arranque sobre la cama, medida en v020 ---------------------
# BLANKET_PROXY  y=-3.226..-0.986  z tope 0.980
# PILLOW_L_PROXY x=-0.809..0.127   y=-3.800..-3.282  z tope 0.981
# BACKPACK_*     x= 0.778..1.218   -> la mochila ocupa el lado +X
LADO_X = -0.30
APOYO_Z = 0.955      # la manta está en 0,980: el cuerpo se hunde 2,5 cm
PIES_Y = -1.88

# (hueso, eje, grados) en los ejes de la armadura EN REPOSO:
#   +X = izquierda del personaje   +Y = espalda   +Z = arriba (cabeza)
# Los hijos van antes que los padres: cada articulación usa su eje natural.
POSE = [
    *[(f"LeftHand{d}{i}", "Y", b * k)
      for d, b in (("Index", 62), ("Middle", 68), ("Ring", 74), ("Pinky", 80))
      for i, k in ((1, .55), (2, .80), (3, .55))],
    *[(f"RightHand{d}{i}", "Y", -b * k)
      for d, b in (("Index", 46), ("Middle", 54), ("Ring", 60), ("Pinky", 66))
      for i, k in ((1, .55), (2, .80), (3, .55))],
    ("LeftHandThumb1", "Z", -30), ("LeftHandThumb2", "Y", 26),
    ("RightHandThumb1", "Z", 24), ("RightHandThumb2", "Y", -22),

    ("Spine", "X", 3), ("Spine1", "X", 7), ("Spine2", "X", 6),
    ("Neck", "X", 15), ("Head", "X", 11),
    ("LeftShoulder", "Z", -6), ("RightShoulder", "Z", 6),

    ("LeftUpLeg", "X", -9), ("LeftUpLeg", "Z", -13), ("LeftUpLeg", "Y", -2),
    ("LeftLeg", "X", 11),
    ("RightUpLeg", "X", -2), ("RightUpLeg", "Z", 9), ("RightUpLeg", "Y", 3),
    ("RightLeg", "X", 3),
    ("LeftFoot", "X", 30), ("LeftFoot", "Y", -12),
    ("RightFoot", "X", 26), ("RightFoot", "Y", 9),
]

# Brazos por IK: dónde va la mano y hacia dónde cae el codo, medido desde la
# cadera en el mundo. Rotar hombro y codo a ojo deja los brazos imposibles.
BRAZOS = (
    (["LeftArm", "LeftForeArm", "LeftHand"], (-0.075, -0.30, 0.315), (-0.38, -0.12, -0.06), -95),
    (["RightArm", "RightForeArm", "RightHand"], (0.045, -0.03, 0.195), (0.35, 0.02, -0.05), -18),
)

TEL = (0.071, 0.146, 0.009)
EJES = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}


def salida():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not extra:
        raise SystemExit("falta SALIDA.blend")
    return os.path.abspath(extra[0])


def coleccion(nombre):
    col = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    if nombre not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


def mudar(objetos, col):
    for o in objetos:
        for vieja in list(o.users_collection):
            vieja.objects.unlink(o)
        col.objects.link(o)


def guardar_habitacion():
    """La habitación entera pasa a REFERENCIA y queda bloqueada."""
    ref = coleccion(COL_REFERENCIA)
    mudar(list(bpy.data.objects), ref)
    for o in bpy.data.objects:
        o.hide_select = True
    for col in list(bpy.data.collections):
        if col is not ref and not col.objects and not col.children:
            bpy.data.collections.remove(col)
    return len(ref.objects)


def importar():
    grupo = bpy.data.node_groups.get("glTF Material Output")
    if grupo:
        # El horneado dejó un grupo con un solo socket y el importador revienta.
        grupo.name = "glTF Material Output (lightmap)"
    antes = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=os.path.abspath(GLB))
    finally:
        if grupo:
            grupo.name = "glTF Material Output"
    nuevos = [o for o in bpy.data.objects if o not in antes]
    for o in list(nuevos):
        if o.type == "MESH" and not o.data.materials:   # esfera de entorno
            nuevos.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)
    return next(o for o in nuevos if o.type == "ARMATURE"), [o for o in nuevos if o.type == "MESH"]


def girar(arm, hueso, eje, grados):
    pb = arm.pose.bones[hueso]
    pb.rotation_mode = "QUATERNION"
    m = pb.matrix.to_3x3()
    local = m.inverted() @ (m @ Vector((0, 1, 0)) if eje == "SELF" else EJES[eje])
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(local, math.radians(grados))
    bpy.context.view_layer.update()


def apuntar(arm, hueso, direccion):
    """Orienta un hueso hacia una dirección, en espacio de la armadura."""
    pb = arm.pose.bones[hueso]
    q = (pb.tail - pb.head).normalized().rotation_difference(direccion.normalized())
    local = pb.matrix.to_3x3().inverted() @ q.axis
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(local, q.angle)
    bpy.context.view_layer.update()


def ik(arm, a, b, c, objetivo, polo):
    """Dos huesos por ley del coseno, todo en espacio de la armadura."""
    p = lambda n: arm.pose.bones[n].head
    pa, l1, l2 = p(a).copy(), (p(a) - p(b)).length, (p(b) - p(c)).length
    hacia = objetivo - pa
    d = min(hacia.length, (l1 + l2) * 0.998)
    hacia.normalize()
    ang = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    eje = hacia.cross(polo - pa)
    eje = eje.normalized() if eje.length > 1e-6 else Vector((0, 0, 1))
    apuntar(arm, a, Matrix.Rotation(ang, 3, eje) @ hacia)   # el codo va al polo
    apuntar(arm, b, objetivo - p(b))


def posar(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = Quaternion()
    bpy.context.view_layer.update()
    for hueso, eje, grados in POSE:
        girar(arm, hueso, eje, grados)


def acostar(arm, mallas):
    """De pie mirando -Y  ->  boca arriba con la cabeza hacia -Y."""
    arm.rotation_mode = "QUATERNION"
    arm.rotation_quaternion = Quaternion(Vector((0, -1, 1)).normalized(), math.pi)
    arm.location = Vector((LADO_X, PIES_Y, APOYO_Z + 0.12))
    bpy.context.view_layer.update()

    # Apoya la pelvis, no el abrigo: la capucha tendida bajo los hombros deja
    # el cuerpo flotando 12 cm si se mide el punto más bajo de la ropa.
    cuerpo = next(o for o in mallas if o.name.upper().endswith("BODY"))
    cadera = arm.matrix_world @ arm.pose.bones["Hips"].head
    dg = bpy.context.evaluated_depsgraph_get()
    ev = cuerpo.evaluated_get(dg)
    puntos = [ev.matrix_world @ v.co for v in ev.data.vertices]
    espalda = min((q.z for q in puntos if (q - cadera).length < 0.18), default=cadera.z)
    arm.location.z += APOYO_Z - espalda
    bpy.context.view_layer.update()


def telefono(arm, col):
    mano = arm.pose.bones["LeftHand"]
    centro = (arm.matrix_world @ mano.tail) + Vector((0.012, -0.020, 0.030))
    normal = ((arm.matrix_world @ arm.pose.bones["Head"].tail) - centro).normalized()
    largo = Vector((0, -1, 0))
    largo = (largo - normal * largo.dot(normal)).normalized()
    ancho = largo.cross(normal).normalized()
    base = Matrix((
        (ancho.x, largo.x, normal.x, centro.x),
        (ancho.y, largo.y, normal.y, centro.y),
        (ancho.z, largo.z, normal.z, centro.z),
        (0, 0, 0, 1)))

    creados = []
    for nombre, tam, dz, color, emite in (
        ("TELEFONO", TEL, 0.0, (0.03, 0.031, 0.034, 1), False),
        # `_LUZ`: la página lo convierte en superficie que emite y le cuelga
        # una luz. Es la única fuente que llega a ese rincón de la cama.
        ("TELEFONO_PANTALLA_LUZ", (TEL[0] * .90, TEL[1] * .90, TEL[2] * .22),
         TEL[2] * .55, (0.02, 0.02, 0.02, 1), True),
    ):
        bpy.ops.mesh.primitive_cube_add(size=1)
        o = bpy.context.object
        o.name = nombre
        o.scale = tam
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mat = bpy.data.materials.new("MAT_" + nombre)
        mat.use_nodes = True
        b = mat.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = color
        b.inputs["Metallic"].default_value = 0.0
        b.inputs["Roughness"].default_value = 0.35 if emite else 0.6
        if emite:
            b.inputs["Emission Color"].default_value = (0.62, 0.74, 0.98, 1)
            b.inputs["Emission Strength"].default_value = 6.0
        o.data.materials.append(mat)
        o.parent = arm
        o.parent_type = "BONE"
        o.parent_bone = "LeftHand"
        bpy.context.view_layer.update()
        o.matrix_world = base @ Matrix.Translation(Vector((0, 0, dz)))
        creados.append(o)

    # La pantalla cuelga del cuerpo del teléfono, no del hueso: así se mueve
    # un objeto solo y la pantalla no se queda atrás.
    cuerpo, pantalla = creados
    mundo = pantalla.matrix_world.copy()
    pantalla.parent = cuerpo
    pantalla.parent_type = "OBJECT"
    pantalla.parent_bone = ""
    bpy.context.view_layer.update()
    pantalla.matrix_parent_inverse = cuerpo.matrix_world.inverted()
    pantalla.matrix_world = mundo

    mudar(creados, col)
    bpy.context.view_layer.update()
    return creados


def camara():
    cam = bpy.data.objects.new("CAM_POSE", bpy.data.cameras.new("CAM_POSE"))
    coleccion(COL_REFERENCIA).objects.link(cam)
    cam.location = Vector((1.95, -4.75, 1.95))
    cam.rotation_euler = (cam.location - Vector((-0.30, -2.75, 1.05))).to_track_quat("Z", "Y").to_euler()
    cam.data.lens = 42
    cam.hide_select = True
    bpy.context.scene.camera = cam
    return cam


def main():
    destino = salida()
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    referencia = guardar_habitacion()

    arm, mallas = importar()
    arm.name = "AVATAR_RIG"
    arm.data.name = "AVATAR_RIG"
    arm.show_in_front = True
    for o in mallas:
        o.name = "AVATAR_" + o.name.replace("avaturn_", "").upper()
    col = coleccion(COL_AVATAR)
    mudar([arm] + mallas, col)

    posar(arm)
    acostar(arm, mallas)
    aArmadura = arm.matrix_world.inverted()
    cadera = arm.matrix_world @ arm.pose.bones["Hips"].head
    for huesos, mano, codo, torsion in BRAZOS:
        ik(arm, *huesos, aArmadura @ (cadera + Vector(mano)), aArmadura @ (cadera + Vector(codo)))
        girar(arm, huesos[2], "SELF", torsion)

    tel = telefono(arm, col)
    camara()

    # Nada de animación: si el rig tiene una Action, sus fotogramas le pisan la
    # pose viva cada vez que Blender recalcula. Que no tenga ninguna.
    arm.animation_data_clear()
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)

    # Que el archivo abra en Modo Pose sobre el rig.
    for o in bpy.data.objects:
        o.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    bpy.ops.wm.save_as_mainfile(filepath=destino)
    print("POSE_FILE=" + str({
        "blend": destino,
        "referencia_bloqueada": referencia,
        "caras_avatar": sum(len(o.data.polygons) for o in mallas),
        "objetos_que_se_exportan": sorted(o.name for o in col.objects),
        "actions": len(bpy.data.actions),
    }))


main()
