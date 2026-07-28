"""
GUARDAR Y RECUPERAR POSES  (sin Actions)
========================================

Una pose es un JSON en `blender/poses/<nombre>.json`: dónde está parado el
avatar, la rotación de cada hueso y la ubicación de cada objeto que lo
acompaña (el teléfono).

Por qué en JSON y no con el sistema de animación de Blender: una Action con
fotogramas clavados le pisa la pose viva cada vez que Blender recalcula, y
cambiar de modo la recalcula. Ya borró una pose entera. Un JSON no se ejecuta
ni recalcula nada.

`AVATAR_POSE.blend` guarda siempre UNA pose, la que se está editando. Los JSON
son el archivo de las que ya están listas.

No lo corras a mano: lo llama `tools/pose.sh`.

Uso:
  Blender --background blender/AVATAR_POSE.blend --python pose_io.py -- guardar RUTA.json
  Blender --background blender/AVATAR_POSE.blend --python pose_io.py -- abrir   RUTA.json
"""

import json
import os
import sys

import bpy
from mathutils import Matrix

RIG = "AVATAR_RIG"
REFERENCIA = "REFERENCIA"

extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(extra) < 2 or extra[0] not in ("guardar", "abrir"):
    raise SystemExit("uso: guardar|abrir RUTA.json")
modo, ruta = extra[0], os.path.abspath(extra[1])

arm = bpy.data.objects.get(RIG)
if arm is None:
    raise SystemExit("el archivo no tiene " + RIG)

if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

referencia = bpy.data.collections.get(REFERENCIA)
fijos = set(referencia.objects) if referencia else set()


def acompana(o):
    """Lo que hay que guardar aparte del esqueleto.

    Quedan afuera: la habitación, el propio rig, y las mallas del cuerpo —esas
    las deforma el esqueleto, su transformación propia no significa nada.
    """
    if o in fijos or o is arm:
        return False
    return not (o.parent is arm and o.parent_type == "OBJECT")


acompanan = [o for o in bpy.data.objects if acompana(o)]


def matriz(m):
    return [round(v, 6) for fila in m for v in fila]


if modo == "guardar":
    arm.rotation_mode = "QUATERNION"
    datos = {
        "rig": {
            "loc": [round(v, 6) for v in arm.location],
            "rot": [round(v, 6) for v in arm.rotation_quaternion],
            "esc": [round(v, 6) for v in arm.scale],
        },
        "huesos": {},
        "objetos": {},
    }
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        datos["huesos"][pb.name] = {
            "rot": [round(v, 6) for v in pb.rotation_quaternion],
            "loc": [round(v, 6) for v in pb.location],
            "esc": [round(v, 6) for v in pb.scale],
        }
    for o in acompanan:
        datos["objetos"][o.name] = {
            "base": matriz(o.matrix_basis),
            "padre": o.parent.name if o.parent else None,
            "hueso": o.parent_bone or None,
            # `hide_get()` es el ojito del Outliner, que es lo que se usa a
            # mano. `hide_render` es otro icono que ni siquiera se ve por
            # defecto: leer ese dejaba el teléfono en poses donde sobraba.
            "visible": not o.hide_get(),
        }

    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    rotados = sum(1 for h in datos["huesos"].values() if h["rot"] != [1.0, 0.0, 0.0, 0.0])
    print("POSE_GUARDADA=" + json.dumps({
        "json": ruta, "huesos_rotados": rotados,
        "objetos": sorted(datos["objetos"]),
        "ubicacion": datos["rig"]["loc"],
    }, ensure_ascii=False))

else:
    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    arm.rotation_mode = "QUATERNION"
    arm.location = datos["rig"]["loc"]
    arm.rotation_quaternion = datos["rig"]["rot"]
    arm.scale = datos["rig"]["esc"]
    faltan = []
    for nombre, h in datos["huesos"].items():
        pb = arm.pose.bones.get(nombre)
        if pb is None:
            faltan.append(nombre)
            continue
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = h["rot"]
        pb.location = h["loc"]
        pb.scale = h["esc"]
    for nombre, d in datos.get("objetos", {}).items():
        o = bpy.data.objects.get(nombre)
        if o is None:
            faltan.append(nombre)
            continue
        m = d["base"]
        o.matrix_basis = Matrix([m[0:4], m[4:8], m[8:12], m[12:16]])
        o.hide_set(not d.get("visible", True))
    bpy.context.view_layer.update()

    if "--guardar-blend" in extra:
        bpy.ops.wm.save_mainfile()
    print("POSE_ABIERTA=" + json.dumps({
        "json": ruta, "faltaban": faltan, "guardado": "--guardar-blend" in extra,
    }, ensure_ascii=False))
