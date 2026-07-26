"""
ARREGLOS DE LA PARED NORTE  (sector "NORTH3")
=============================================

1. RETRO_CONSOLE_02 emitia luz. Usaba MAT_BLOCKOUT_ACCENT_BLUE, que es el
   material de los leds y displays. Pasa a un azul mate que no emite.
2. Los seis FRAME_GRID de la reja pasan a ser seis vinilos: cuadrados,
   todos del mismo tamano, en grilla de 3 x 2 centrada en la reja.
3. Las nueve RECORDS_STACK se reemplazan por libros verticales de lomo
   fino. Como vinilos de canto no se les puede poner ninguna referencia
   encima; como libros, el lomo es superficie util.

Uso:
  Blender --background ARCHIVO.blend --python fix_north_details.py -- SALIDA.blend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import box, col, mat, clear_sector, out_path, save

SECTOR = "NORTH3"

VINYL = 0.360          # lado del vinilo, cuadrado
VINYL_T = 0.030
BOOKS_PER_CUBE = 7


def fix_emissive_console():
    obj = bpy.data.objects.get("RETRO_CONSOLE_02")
    if not obj:
        print("  no esta RETRO_CONSOLE_02")
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat("MAT_BLOCKOUT_PLASTIC_BLUE"))
    print("  RETRO_CONSOLE_02 -> MAT_BLOCKOUT_PLASTIC_BLUE (no emite)")


def rebuild_vinyls():
    panel = bpy.data.objects.get("GRID_PANEL")
    if not panel:
        print("  no esta GRID_PANEL")
        return
    px, pz = panel.location.x, panel.location.z
    pw, ph = panel.dimensions.x, panel.dimensions.z
    parent = panel.parent
    y = panel.location.y - 0.032

    # Tres columnas y dos filas, con los margenes repartidos parejos.
    gap_x = (pw - 3 * VINYL) / 4.0
    gap_z = (ph - 2 * VINYL) / 3.0
    cols = [px - pw / 2 + gap_x * (i + 1) + VINYL * (i + 0.5) for i in range(3)]
    rows = [pz + ph / 2 - gap_z * (j + 1) - VINYL * (j + 0.5) for j in range(2)]

    viejos = [o for o in bpy.data.objects if o.name.startswith("FRAME_GRID_")]
    for o in viejos:
        bpy.data.objects.remove(o, do_unlink=True)

    n = 0
    for j, z in enumerate(rows):
        for i, x in enumerate(cols):
            n += 1
            box("VINYL_WALL_%02d" % n, (VINYL, VINYL_T, VINYL), (x, y, z),
                col("30_PROPS"), "MAT_BLOCKOUT_PAPER", parent=parent,
                sector=SECTOR,
                props={"asset_id": "vinyl_wall_%02d" % n,
                       "asset_type": "vinyl",
                       "texture_id": "TEX_VINYL_WALL_%02d" % n,
                       "reference_group": "norte",
                       "notes": "tapa de disco, cuadrada 1:1"})
    print("  %d FRAME_GRID reemplazados por %d vinilos de %.2f m" %
          (len(viejos), n, VINYL))


def rebuild_books():
    """Los cubos se deducen de los DIVISORES de la estanteria, no de lo que
    habia adentro. Si se dedujeran del contenido, volver a correr el script
    despues de que el propio script ya lo reemplazo deja la estanteria vacia:
    clear_sector borra los libros y despues no hay de donde sacar la posicion.
    """
    divisores = sorted((o for o in bpy.data.objects
                        if o.name.startswith("RECORDS_DIV_")),
                       key=lambda o: o.location.x)
    if len(divisores) < 2:
        print("  no encuentro los divisores de la estanteria")
        return
    parent = divisores[0].parent
    y = divisores[0].location.y - 0.02

    centros = [(divisores[i].location.x + divisores[i + 1].location.x) / 2.0
               for i in range(len(divisores) - 1)]

    # El cubo que tiene la canasta no lleva libros.
    canasta = bpy.data.objects.get("RECORDS_BASKET")
    if canasta:
        ocupado = min(range(len(centros)),
                      key=lambda i: abs(centros[i] - canasta.location.x))
        centros = [c for i, c in enumerate(centros) if i != ocupado]

    for o in [o for o in bpy.data.objects if o.name.startswith("RECORDS_STACK_")]:
        bpy.data.objects.remove(o, do_unlink=True)

    # Lomos finos y de altura despareja: una fila de libros nunca esta pareja.
    espesor = (0.034, 0.052, 0.040, 0.030, 0.058, 0.036, 0.046)
    alturas = (0.38, 0.34, 0.42, 0.30, 0.36, 0.40, 0.32)
    tonos = ("MAT_BLOCKOUT_FABRIC", "MAT_BLOCKOUT_WOOD_LIGHT",
             "MAT_BLOCKOUT_PAPER", "MAT_BLOCKOUT_ACCENT_ORANGE",
             "MAT_BLOCKOUT_FABRIC", "MAT_BLOCKOUT_PLASTIC_BLUE",
             "MAT_BLOCKOUT_PAPER")

    n = 0
    for c, cx in enumerate(centros):
        total = sum(espesor[:BOOKS_PER_CUBE])
        x = cx - total / 2.0
        for i in range(BOOKS_PER_CUBE):
            k = (i + c) % len(espesor)
            t, h = espesor[k], alturas[k]
            n += 1
            box("BOOK_NORTH_%02d" % n, (t, 0.280, h),
                (x + t / 2.0, y, 0.05 + h / 2.0), col("30_PROPS"),
                tonos[k], parent=parent, sector=SECTOR,
                props={"asset_id": "book_north_%02d" % n,
                       "asset_type": "book",
                       "texture_id": "TEX_BOOK_NORTH_%02d" % n,
                       "reference_group": "norte",
                       "notes": "lomo hacia el sur; ahi va la referencia"})
            x += t + 0.004
    print("  %d libros en %d cubos, deducidos de %d divisores"
          % (n, len(centros), len(divisores)))


def main():
    print("Objetos NORTH3 reemplazados:", clear_sector(SECTOR))
    fix_emissive_console()
    rebuild_vinyls()
    rebuild_books()
    save(out_path(sys.argv, bpy.data.filepath))


main()
