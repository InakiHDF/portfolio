"""
INVENTARIO DE HUECOS DE CONTENIDO
=================================

Lista cada superficie de la escena donde puede ir una imagen elegida por el
usuario: cuadros, vinilos, lomos de libros, fotos, pantallas, revistas.

Para cada una informa el tamano real de la cara visible y su proporcion, que
es el dato que hace falta para conseguir o recortar la imagen correcta.

Escribe docs/HUECOS.md y lo imprime por consola.

Uso:
  Blender --background ARCHIVO.blend --python inventory_textures.py
"""

import json
import os

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(REPO, "docs", "HUECOS.md")
JSON = os.path.join(REPO, "docs", "huecos.json")

# (titulo, test, se_ve_el_lomo)
GRUPOS = [
    ("Vinilos de pared (reja norte)", lambda o: o.name.startswith("VINYL_WALL"), False),
    ("Lomos de libros (estanteria de discos)", lambda o: o.name.startswith("BOOK_NORTH"), True),
    ("Cuadros de la escalera", lambda o: o.name.startswith("FRAME_STAIR"), False),
    ("Cuadros de la pared oeste", lambda o: o.name.startswith("POSTER_WEST"), False),
    ("Cuadros del retranqueo (junto a la puerta)", lambda o: o.name.startswith("FRAME_NW"), False),
    ("Fotos chicas (pared norte)", lambda o: o.name.startswith("PHOTO_NORTH"), False),
    ("Pantallas", lambda o: o.get("asset_type") in ("screen", "monitor")
     and "PANEL" in o.name or o.name == "SCREEN_SURFACE", False),
    ("Reloj", lambda o: o.name.startswith("CLOCK_"), False),
    ("Alfombra", lambda o: o.name.startswith("RUG_"), False),
    ("Libros del estante oeste", lambda o: o.name.startswith("SHELF_BOOK"), True),
    ("Libros y revistas sueltos", lambda o: o.name.startswith(
        ("BOOK_TABLE", "BOOK_FLOOR", "MAGAZINE_", "NOTEBOOK_", "PAPER_STACK")), False),
    ("Planos sobre la mesa este", lambda o: o.name.startswith("SHEET_EAST"), False),
]


def cara(obj, lomo=False):
    """Devuelve (ancho, alto, proporcion) de la cara que se ve.

    En un libro parado en un estante la cara visible es el LOMO, que es la
    dimension mas fina por la altura. En un cuadro o un vinilo es al reves:
    la fina es el espesor y la cara es la grande."""
    d = list(obj.dimensions)
    if lomo:
        return min(d), d[2], (min(d) / d[2] if d[2] else 0)
    thin = d.index(min(d))
    resto = [d[i] for i in range(3) if i != thin]
    if thin == 2:                       # superficie horizontal: tapa hacia arriba
        w, h = max(resto), min(resto)
    else:                               # colgada o parada: el alto es Z
        w, h = [d[i] for i in range(3) if i != thin and i != 2][0], d[2]
    return w, h, (w / h if h else 0)


def pixeles(obj):
    """Cuanto mide el objeto en pantalla desde CAM_ISO_SW, en pixeles.

    Es el dato que ordena la lista: un lomo de libro que ocupa 8 px no
    necesita una imagen elegida, con un color y una banda alcanza."""
    scene = bpy.context.scene
    cam = bpy.data.objects.get("CAM_ISO_SW")
    if not cam:
        return 0, 0
    rx, ry = 1712, 945
    us, vs = [], []
    for corner in obj.bound_box:
        p = world_to_camera_view(scene, cam, obj.matrix_world @ Vector(corner))
        if p.z <= 0:
            return 0, 0
        us.append(p.x * rx)
        vs.append(p.y * ry)
    return max(us) - min(us), max(vs) - min(vs)


def main():
    lineas = ["# Huecos de contenido", "",
              "Cada fila es una superficie donde puede ir una imagen elegida.",
              "La proporcion es ancho / alto: 1.00 es cuadrado, mayor que 1 es",
              "apaisado, menor que 1 es vertical.", ""]
    total = 0
    usados = set()
    datos = {}

    for titulo, test, lomo in GRUPOS:
        objs = []
        for o in bpy.data.objects:
            if o.type != "MESH" or o.name in usados:
                continue
            try:
                if test(o):
                    objs.append(o)
            except Exception:
                pass
        if not objs:
            continue
        objs.sort(key=lambda o: o.name)
        for o in objs:
            usados.add(o.name)
        total += len(objs)

        lineas += ["## %s  (%d)" % (titulo, len(objs)), "",
                   "| objeto | ancho x alto (cm) | proporcion | en pantalla |",
                   "|---|---|---|---|"]
        for o in objs:
            w, h, r = cara(o, lomo)
            px, py = pixeles(o)
            grande = max(px, py)
            marca = "legible" if grande >= 90 else ("chico" if grande >= 35 else "ilegible")
            lineas.append("| `%s` | %.1f x %.1f | %.2f | %d px, %s |"
                          % (o.name, w * 100, h * 100, r, grande, marca))
            datos[o.name] = {"ancho_cm": round(w * 100, 1),
                             "alto_cm": round(h * 100, 1),
                             "proporcion": round(r, 4),
                             "px_pantalla": int(grande),
                             "lomo": lomo}
        lineas.append("")
        leg = sum(1 for o in objs if max(pixeles(o)) >= 90)
        chi = sum(1 for o in objs if 35 <= max(pixeles(o)) < 90)
        print("%-44s %3d   legibles=%-3d chicos=%-3d ilegibles=%d"
              % (titulo, len(objs), leg, chi, len(objs) - leg - chi))

    lineas.insert(5, "**Total: %d huecos.**" % total)
    lineas.insert(6, "")
    os.makedirs(os.path.dirname(DOC), exist_ok=True)
    with open(DOC, "w") as f:
        f.write("\n".join(lineas) + "\n")
    with open(JSON, "w") as f:
        json.dump(datos, f, indent=1, sort_keys=True)
    print("\nTotal:", total)
    print("Escrito:", DOC, "y", JSON)


main()
