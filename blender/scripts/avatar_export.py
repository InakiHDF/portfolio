"""
EXPORTA LA POSE  ->  un GLB con la pose y la ubicación adentro
==============================================================

Sale todo lo que NO esté en la colección REFERENCIA: la habitación está en el
archivo sólo para posar mirando dónde va cada cosa, no viaja.

Primero aplica la pose del JSON que se le pasa; el .blend abierto es sólo el
molde (avatar, teléfono, habitación). Nunca lo modifica: Blender corre sobre
una copia en memoria y no guarda.

No lo corras a mano: lo llama `tools/avatar.sh`.

Uso:
  Blender --background blender/AVATAR_POSE.blend \
    --python blender/scripts/avatar_export.py -- POSE.json SALIDA.glb
"""

import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sonda_luz import medir

extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(extra) < 2:
    raise SystemExit("uso: POSE.json SALIDA.glb")
pose_json, destino = os.path.abspath(extra[0]), os.path.abspath(extra[1])
os.makedirs(os.path.dirname(destino), exist_ok=True)

# --- Aplicar la pose ---------------------------------------------------------
arm = bpy.data.objects["AVATAR_RIG"]
with open(pose_json, "r", encoding="utf-8") as f:
    pose = json.load(f)

arm.rotation_mode = "QUATERNION"
arm.location = pose["rig"]["loc"]
arm.rotation_quaternion = pose["rig"]["rot"]
arm.scale = pose["rig"]["esc"]
for nombre, h in pose["huesos"].items():
    pb = arm.pose.bones.get(nombre)
    if pb is None:
        continue
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = h["rot"]
    pb.location = h["loc"]
    pb.scale = h["esc"]
ocultos = []
for nombre, d in pose.get("objetos", {}).items():
    o = bpy.data.objects.get(nombre)
    if o is None:
        continue
    m = d["base"]
    o.matrix_basis = Matrix([m[0:4], m[4:8], m[8:12], m[12:16]])
    if not d.get("visible", True):
        ocultos.append(nombre)
bpy.context.view_layer.update()

if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

referencia = bpy.data.collections.get("REFERENCIA")
quedan = set(referencia.objects) if referencia else set()


def sale(o):
    """El cuerpo va siempre; lo que lo acompaña, sólo si la pose lo pide.

    Un prop que no figura en el JSON es un prop que no existía cuando esa pose
    se guardó. Si se exportara por venir visible en el archivo, aparecería
    flotando en todas las poses viejas.
    """
    if o in quedan or o.type not in {"ARMATURE", "MESH"}:
        return False
    if o is arm or (o.parent is arm and o.parent_type == "OBJECT"):
        return True
    return o.name in pose.get("objetos", {}) and o.name not in ocultos


salen = [o for o in bpy.data.objects if sale(o)]
if not salen:
    raise SystemExit("no hay nada para exportar fuera de REFERENCIA")

for o in bpy.data.objects:
    o.hide_select = False
    o.hide_viewport = False
    # `hide_set` es el ojito del Outliner y es OTRA cosa que `hide_viewport`.
    # Blender no deja seleccionar un objeto tapado por el ojito y `select_set`
    # falla en silencio: si el teléfono quedó oculto de posar otra escena, la
    # pose que sí lo lleva se exportaba sin él. Manda la pose, no el estado en
    # que quedó el archivo.
    o.hide_set(False)
    o.select_set(o in salen)
bpy.context.view_layer.objects.active = next(o for o in salen if o.type == "ARMATURE")

opciones = dict(
    filepath=destino,
    export_format="GLB",
    use_selection=True,
    export_apply=False,          # aplicar modificadores rompería el skinning
    export_extras=True,
    export_cameras=False,
    export_lights=False,
    export_yup=True,
    export_skins=True,
    export_animations=False,     # la pose viaja en la transformación, no como clip
    # LA OPCIÓN CLAVE. En True (el valor por defecto) el exportador escribe la
    # postura de REPOSO y la pose se pierde entera: el avatar llega a la página
    # en T abierto de brazos. En False escribe la pose actual.
    export_rest_position_armature=False,
    export_image_format="AUTO",
    export_materials="EXPORT",
    export_normals=True,
    export_tangents=False,
)
validas = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
bpy.ops.export_scene.gltf(**{k: v for k, v in opciones.items() if k in validas})

# La luz que de verdad le llega en este lugar del cuarto. Se mide desde el
# pecho y sin el avatar puesto, para que no se mida a sí mismo.
pecho = arm.matrix_world @ arm.pose.bones["Spine2"].head
sh = medir(pecho, ocultar=salen)

print("AVATAR_EXPORT=" + json.dumps({
    "pose": os.path.basename(pose_json),
    "glb": destino,
    "objetos": sorted(o.name for o in salen),
    "ocultos": ocultos,
    "caras": sum(len(o.data.polygons) for o in salen if o.type == "MESH"),
    "sonda": [round(v, 4) for v in pecho],
}, ensure_ascii=False))
print("SONDA=" + json.dumps(sh))
