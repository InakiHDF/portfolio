#!/usr/bin/env bash
# LLEVAR TODAS LAS POSES A LA PÁGINA
# ==================================
#
# Recorre blender/poses/*.json, y por cada una deja un GLB en
# web/modelos/avatar/. Después: refrescar la página, que sortea una.
#
# Por cada pose:
#   1. La aplica sobre blender/AVATAR_POSE.blend (en una copia temporal, el
#      archivo original no se toca) y exporta lo que no sea la habitación.
#   2. Le da el pasaje retro con meshoptimizer: baja triángulos y texturas.
#      Va DESPUÉS de posar, nunca antes: posar sobre una malla ya decimada es
#      posar a ciegas.
#
# La página baja UN solo GLB por visita, el sorteado: tener muchas poses no la
# hace más lenta, sólo ocupa más disco.
#
# Uso:  tools/avatar.sh              # como está calibrado
#       tools/avatar.sh 0.35 256     # más detalle (ratio de caras, px)
#       tools/avatar.sh 0.10 64      # más duro

set -euo pipefail
cd "$(dirname "$0")/.."

RATIO="${1:-0.20}"
TEX="${2:-128}"
BLEND="blender/AVATAR_POSE.blend"
POSES="blender/poses"
DESTINO="web/modelos/avatar"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

[ -f "$BLEND" ] || { echo "No existe $BLEND"; exit 1; }
if ! ls "$POSES"/*.json >/dev/null 2>&1; then
  echo "No hay ninguna pose guardada todavía."
  echo "Guardá la que tenés en Blender con:  tools/pose.sh guardar <nombre>"
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
GT="npx --yes @gltf-transform/cli@4"
mkdir -p "$DESTINO"
rm -f "$DESTINO"/*.glb

for JSON in "$POSES"/*.json; do
  NOMBRE="$(basename "${JSON%.json}")"
  printf '%-22s' "$NOMBRE"

  rm -f "$TMP/pose.glb"
  "$BLENDER" --background "$BLEND" --python blender/scripts/avatar_export.py -- \
    "$JSON" "$TMP/pose.glb" >"$TMP/log.txt" 2>&1 || { echo "ERROR"; tail -5 "$TMP/log.txt"; exit 1; }
  [ -f "$TMP/pose.glb" ] || { echo "ERROR: Blender no generó el GLB"; tail -5 "$TMP/log.txt"; exit 1; }

  # La sonda de luz de esta pose: la iluminación real del cuarto en ese punto.
  grep '^SONDA=' "$TMP/log.txt" | sed 's/^SONDA=//' > "$TMP/sh_${NOMBRE}.json" || true

  $GT weld     "$TMP/pose.glb" "$TMP/w.glb" >/dev/null 2>&1
  $GT simplify "$TMP/w.glb"    "$TMP/s.glb" --ratio "$RATIO" --error 0.02 --lock-border true >/dev/null 2>&1
  $GT resize   "$TMP/s.glb"    "$TMP/r.glb" --width "$TEX" --height "$TEX" >/dev/null 2>&1
  $GT prune    "$TMP/r.glb"    "$DESTINO/avatar_${NOMBRE}.glb" >/dev/null 2>&1

  node -e '
const fs=require("fs"),p=process.argv[1];
const d=fs.readFileSync(p);let o=12,j=null;
while(o<d.length){const l=d.readUInt32LE(o),t=d.readUInt32LE(o+4);o+=8;
if(t===0x4E4F534A)j=JSON.parse(d.slice(o,o+l));o+=l;}
let tris=0;for(const m of j.meshes)for(const pr of m.primitives)tris+=j.accessors[pr.indices].count/3;
console.log(`${(d.length/1048576).toFixed(2)} MB   ${tris} triángulos`);
' "$DESTINO/avatar_${NOMBRE}.glb"
done

# El índice que lee la página: qué poses hay y con qué luz va cada una. Lleva
# una versión con la hora de esta corrida, porque sin eso el navegador sigue
# mostrando el GLB viejo de su caché y parece que el comando no hizo nada.
python3 - "$DESTINO" "$TMP" <<'EOF'
import glob, json, os, sys, time
destino, tmp = sys.argv[1], sys.argv[2]
poses = []
for glb in sorted(glob.glob(os.path.join(destino, "avatar_*.glb"))):
    nombre = os.path.basename(glb)[len("avatar_"):-len(".glb")]
    sonda = os.path.join(tmp, "sh_%s.json" % nombre)
    sh = None
    if os.path.exists(sonda):
        texto = open(sonda).read().strip()
        if texto:
            sh = json.loads(texto)
    poses.append({"archivo": os.path.basename(glb), "sh": sh})
json.dump({"v": int(time.time()), "poses": poses},
          open(os.path.join(destino, "poses.json"), "w"), indent=1)
print("   sondas de luz:", sum(1 for p in poses if p["sh"]), "de", len(poses))
EOF

echo
echo "listo: $(ls "$DESTINO"/avatar_*.glb | wc -l | tr -d ' ') pose(s). Refrescá la página."
