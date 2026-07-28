#!/usr/bin/env bash
# AGREGAR EL LIBRO ABIERTO AL ARCHIVO DE POSE
# ===========================================
#
# Correr con Blender CERRADO. Guardá antes con Ctrl+S: esto escribe el archivo
# y si Blender queda abierto, el próximo guardado tuyo se lo lleva puesto.
#
# No toca la pose que tengas: sólo agrega los objetos del libro.
# Si lo corrés de nuevo, rehace el libro donde estaba al principio.

set -euo pipefail
cd "$(dirname "$0")/.."

BLEND="blender/AVATAR_POSE.blend"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

[ -f "$BLEND" ] || { echo "No existe $BLEND"; exit 1; }

cp "$BLEND" "${BLEND%.blend}_respaldo.blend"
echo "respaldo: ${BLEND%.blend}_respaldo.blend"

"$BLENDER" --background "$BLEND" --python blender/scripts/agregar_libro.py -- --guardar \
  2>&1 | grep -E "^LIBRO=|Error" || true

echo
echo "Listo. Abrí $BLEND: el libro está en la mano izquierda."
echo "Se agarra el objeto LIBRO (el lomo); las tapas y las hojas lo siguen."
