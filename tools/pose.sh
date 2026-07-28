#!/usr/bin/env bash
# GUARDAR Y RECUPERAR POSES
# =========================
#
# blender/AVATAR_POSE.blend tiene siempre UNA pose: la que estás editando.
# Las que ya están listas viven en blender/poses/<nombre>.json.
#
#   tools/pose.sh guardar cama_celular    guarda la pose que tenés ahora
#   tools/pose.sh lista                   muestra las guardadas
#   tools/pose.sh abrir cama_celular      la vuelve a poner en el .blend
#
# "guardar" NO toca el archivo de Blender: podés tenerlo abierto.
# "abrir" SÍ lo reescribe: hay que tener Blender cerrado.

set -euo pipefail
cd "$(dirname "$0")/.."

BLEND="blender/AVATAR_POSE.blend"
POSES="blender/poses"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
ORDEN="${1:-lista}"
NOMBRE="${2:-}"

case "$ORDEN" in
  lista)
    if ! ls "$POSES"/*.json >/dev/null 2>&1; then
      echo "Todavía no hay ninguna pose guardada."
      echo "Guardá la que tenés con:  tools/pose.sh guardar <nombre>"
      exit 0
    fi
    echo "Poses guardadas:"
    for f in "$POSES"/*.json; do
      echo "  · $(basename "${f%.json}")"
    done
    ;;

  guardar)
    [ -n "$NOMBRE" ] || { echo "Falta el nombre:  tools/pose.sh guardar cama_celular"; exit 1; }
    [ -f "$BLEND" ] || { echo "No existe $BLEND"; exit 1; }
    echo "Leyendo la pose de $BLEND"
    echo "(si no aparece lo último que hiciste, guardá en Blender con Ctrl+S y repetí)"
    "$BLENDER" --background "$BLEND" --python blender/scripts/pose_io.py -- \
      guardar "$POSES/$NOMBRE.json" 2>&1 | grep -E "^POSE_GUARDADA|Error" || true
    echo
    echo "Guardada como '$NOMBRE'. Ya podés seguir posando la siguiente en el mismo archivo."
    echo "Cuando quieras verlas todas en la página:  tools/avatar.sh"
    ;;

  abrir)
    [ -n "$NOMBRE" ] || { echo "Falta el nombre:  tools/pose.sh abrir cama_celular"; exit 1; }
    [ -f "$POSES/$NOMBRE.json" ] || { echo "No existe la pose '$NOMBRE'"; "$0" lista; exit 1; }
    echo "OJO: esto reescribe $BLEND. Tiene que estar cerrado en Blender."
    cp "$BLEND" "${BLEND%.blend}_respaldo.blend"
    "$BLENDER" --background "$BLEND" --python blender/scripts/pose_io.py -- \
      abrir "$POSES/$NOMBRE.json" --guardar-blend 2>&1 | grep -E "^POSE_ABIERTA|Error" || true
    echo
    echo "Listo. Abrí $BLEND y vas a tener la pose '$NOMBRE' para seguir editándola."
    ;;

  *)
    echo "No entiendo '$ORDEN'. Las órdenes son: guardar, lista, abrir"
    exit 1
    ;;
esac
