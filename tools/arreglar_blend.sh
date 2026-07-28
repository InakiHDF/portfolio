#!/usr/bin/env bash
# SACARLE LA ANIMACIÓN AL ARCHIVO DE POSE  (se corre una sola vez)
# ================================================================
#
# El archivo tenía una "Action" de Blender. Una Action con fotogramas clavados
# le pisa la pose viva cada vez que Blender recalcula la animación, y cambiar
# de modo con Tab la recalcula. Resultado: apretar Tab borraba la pose.
#
# Esto le saca la Action SIN tocar la pose: la pose queda exactamente como está
# guardada, pero ya nada la puede pisar.
#
# Correr con Blender CERRADO, y después volver a abrir el archivo.

set -euo pipefail
cd "$(dirname "$0")/.."

BLEND="blender/AVATAR_POSE.blend"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

[ -f "$BLEND" ] || { echo "No existe $BLEND"; exit 1; }

cp "$BLEND" "${BLEND%.blend}_respaldo.blend"
echo "respaldo: ${BLEND%.blend}_respaldo.blend"

"$BLENDER" --background "$BLEND" --python-expr '
import bpy
arm = bpy.data.objects["AVATAR_RIG"]

# Fotografiar la pose tal cual está ahora.
foto = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy())
        for pb in arm.pose.bones}
sitio = (arm.location.copy(), arm.rotation_quaternion.copy(), arm.scale.copy())

# Sacar la animación.
arm.animation_data_clear()
for a in list(bpy.data.actions):
    a.use_fake_user = False
    bpy.data.actions.remove(a)

# Volver a poner la pose fotografiada, por las dudas.
arm.location, arm.rotation_quaternion, arm.scale = sitio
for pb in arm.pose.bones:
    if pb.name in foto:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion, pb.location, pb.scale = foto[pb.name]
bpy.context.view_layer.update()

# La pantalla del teléfono, colgada del teléfono y no del hueso: así se mueve
# un objeto solo y la pantalla no se queda atrás.
cuerpo = bpy.data.objects.get("TELEFONO")
pantalla = bpy.data.objects.get("TELEFONO_PANTALLA_LUZ")
if cuerpo and pantalla and pantalla.parent is not cuerpo:
    mundo = pantalla.matrix_world.copy()
    pantalla.parent = cuerpo
    pantalla.parent_type = "OBJECT"
    pantalla.parent_bone = ""
    bpy.context.view_layer.update()
    pantalla.matrix_parent_inverse = cuerpo.matrix_world.inverted()
    pantalla.matrix_world = mundo

bpy.ops.wm.save_mainfile()
rotados = sum(1 for pb in arm.pose.bones if tuple(pb.rotation_quaternion) != (1.0, 0.0, 0.0, 0.0))
print("ARREGLADO=%s" % {
    "actions_que_quedan": len(bpy.data.actions),
    "huesos_rotados_en_la_pose": rotados,
    "ubicacion": [round(v, 3) for v in arm.location],
})
' 2>&1 | grep -E "^ARREGLADO|Error"

echo
echo "Listo. Ya podés abrir el archivo y usar Tab sin miedo."
