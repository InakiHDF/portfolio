"""
REFINADO DE OBJETOS PUNTUALES  (sector "PROPS2")
================================================

  - Maletin de la cama -> mochila negra sencilla
  - Lampara de lava modelada (base, cuello, campana conica, burbujas)
  - Reloj circular con agujas quietas pero listas para animar en la web
  - GRID_PANEL: de panel macizo a reja de barras metalicas
  - Polaroids de la pared norte, tres veces mas grandes
  - Los siete cuadros de la escalera pasan a ser polaroids del mismo tamano
  - Vinilos otra vez mas grandes
  - La revista de la mesa ratona pasa a ser un libro
  - La caja de la discoteca deja de tener madera entablada
  - Puerta verde -> marron

Uso:
  Blender --background ARCHIVO.blend --python refine_props.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix
from lib_blockout import box, col, mat, obj, resize_box, clear_sector, out_path, save

SECTOR = "PROPS2"
PROPS = None
FURN = None

VINYL = 0.420          # antes 0.36
# Dos tamanos: las de la escalera algo mas grandes que las de la pared.
POLAROID_ESCALERA = (0.264, 0.360)   # 20% menos que 0.33 x 0.45
POLAROID_NORTE = (0.190, 0.259)      # el 3x se fue de mano


def ancla(clave, calcular):
    """Guarda una posicion de referencia la primera vez y la reusa siempre.

    Sin esto el script no se puede volver a correr: cada funcion se apoya en
    el objeto que ella misma reemplazo, y en la segunda corrida ese objeto ya
    no existe. Las anclas viven en la escena, asi sobreviven al borrado."""
    sc = bpy.context.scene
    k = "ancla_" + clave
    if k not in sc:
        v = calcular()
        if v is None:
            return None
        sc[k] = [float(x) for x in v]
    return tuple(sc[k])


def ancla_padre(clave, calcular):
    sc = bpy.context.scene
    k = "ancla_padre_" + clave
    if k not in sc:
        o = calcular()
        sc[k] = o.name if o else ""
    return bpy.data.objects.get(sc[k]) if sc[k] else None


def cilindro(nombre, radio, alto, lados, loc, material, parent=None,
             radio_top=None, rot=None):
    """Prisma de N lados. Con 12 o 16 lados lee redondo y sigue siendo poco
    poligono, que es lo que corresponde al estilo."""
    rt = radio if radio_top is None else radio_top
    verts, faces = [], []
    for i in range(lados):
        a = math.tau * i / lados
        verts.append((radio * math.cos(a), radio * math.sin(a), -alto / 2))
    for i in range(lados):
        a = math.tau * i / lados
        verts.append((rt * math.cos(a), rt * math.sin(a), alto / 2))
    for i in range(lados):
        j = (i + 1) % lados
        faces.append((i, j, j + lados, i + lados))
    faces.append(tuple(range(lados - 1, -1, -1)))
    faces.append(tuple(range(lados, lados * 2)))

    mesh = bpy.data.meshes.new(nombre + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    o = bpy.data.objects.new(nombre, mesh)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(mat(material))
    PROPS.objects.link(o)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = Matrix.Identity(4)
    from lib_blockout import tag
    tag(o, SECTOR, {"asset_type": "prop"})
    return o


# ---------------------------------------------------------------------------

def mochila():
    """Mochila negra: cuerpo, tapa, bolsillo, dos tirantes y asa.

    Sencilla a proposito. Lo que la hace leer mochila no es el detalle, es la
    silueta: cuerpo mas alto que ancho, tapa que sobresale y tirantes."""
    bed = obj("BED_01_ROOT")
    viejos = [o for o in bpy.data.objects if o.name.startswith("BAG_BED_")]

    def calcular():
        if viejos:
            return (sum(o.location.x for o in viejos) / len(viejos),
                    sum(o.location.y for o in viejos) / len(viejos))
        return (0.998, -2.34)

    cx, cy = ancla("mochila", calcular)
    manta = obj("BLANKET_PROXY")
    z0 = manta.matrix_world.translation.z + manta.dimensions.z / 2

    for o in viejos:
        bpy.data.objects.remove(o, do_unlink=True)

    # Acostada sobre la cama: alto = eje Y, ancho = eje X, espesor = Z
    # Mas grande y mas clara: a 0.34 x 0.52 y casi negra no se
    # entendia que era.
    W, L, H = 0.44, 0.66, 0.28
    piezas = [
        ("BACKPACK_BODY", (W, L, H), (0, 0, H / 2), "MAT_BACKPACK"),
        ("BACKPACK_FLAP", (W + 0.015, L * 0.42, H * 0.55),
         (0, L * 0.27, H * 0.78), "MAT_BACKPACK"),
        ("BACKPACK_POCKET", (W * 0.70, L * 0.30, H * 0.30),
         (0, -L * 0.22, H * 0.86), "MAT_BACKPACK_POCKET"),
        ("BACKPACK_HANDLE", (0.10, 0.035, 0.045),
         (0, L * 0.47, H * 0.90), "MAT_BACKPACK_POCKET"),
    ]
    for nombre, size, loc, m in piezas:
        box(nombre, size, (cx + loc[0], cy + loc[1], z0 + loc[2]), PROPS, m,
            parent=bed, sector=SECTOR, props={"asset_type": "bag"})
        bpy.data.objects[nombre].matrix_parent_inverse = bed.matrix_world.inverted()

    # Tirantes: dos tiras que cruzan la espalda, apenas levantadas
    for lado, dx in (("L", -0.09), ("R", 0.09)):
        o = box("BACKPACK_STRAP_" + lado, (0.055, L * 0.66, 0.030),
                (cx + dx, cy - L * 0.06, z0 + H + 0.012), PROPS,
                "MAT_BACKPACK_POCKET", sector=SECTOR,
                props={"asset_type": "bag"})
        o.parent = bed
        o.matrix_parent_inverse = bed.matrix_world.inverted()
    # Hebillas
    for lado, dx in (("L", -0.09), ("R", 0.09)):
        o = box("BACKPACK_BUCKLE_" + lado, (0.045, 0.035, 0.020),
                (cx + dx, cy - L * 0.30, z0 + H + 0.020), PROPS,
                "MAT_BLOCKOUT_METAL", sector=SECTOR, props={"asset_type": "bag"})
        o.parent = bed
        o.matrix_parent_inverse = bed.matrix_world.inverted()
    print("  mochila: %d piezas, %.2f x %.2f x %.2f m" % (8, W, L, H))


def lampara_lava():
    """Base metalica, cuello, campana conica y burbujas adentro."""
    def calcular():
        b = bpy.data.objects.get("LAVA_LAMP_BASE")
        if b:
            return (b.location.x, b.location.y, b.location.z - b.dimensions.z / 2)
        tapa = bpy.data.objects.get("RECORDS_TOP")     # respaldo permanente
        if tapa:
            return (0.34, 0.0, tapa.location.z + tapa.dimensions.z / 2)
        return None

    pos = ancla("lava", calcular)
    padre = ancla_padre("lava", lambda: (bpy.data.objects.get("LAVA_LAMP_BASE")
                                         or bpy.data.objects.get("RECORDS_TOP")).parent)

    if pos is None:
        print("  no encuentro donde va la lampara de lava")
        return
    x, y, z0 = pos
    for n in ("LAVA_LAMP_BASE", "LAVA_LAMP_GLASS"):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)

    cilindro("LAVA_BASE", 0.075, 0.075, 12, (x, y, z0 + 0.037),
             "MAT_BLOCKOUT_METAL", padre, radio_top=0.055)
    cilindro("LAVA_CUELLO", 0.040, 0.030, 12, (x, y, z0 + 0.088),
             "MAT_BLOCKOUT_METAL", padre)
    cilindro("LAVA_CAMPANA", 0.058, 0.240, 12, (x, y, z0 + 0.223),
             "MAT_BLOCKOUT_EMISSIVE", padre, radio_top=0.026)
    cilindro("LAVA_TAPA", 0.030, 0.038, 12, (x, y, z0 + 0.362),
             "MAT_BLOCKOUT_METAL", padre, radio_top=0.042)
    # Burbujas: tres bloques de distinto porte adentro de la campana
    for i, (dz, r) in enumerate(((0.06, 0.030), (0.14, 0.022), (0.21, 0.016))):
        cilindro("LAVA_BURBUJA_%02d" % (i + 1), r, r * 1.6, 8,
                 (x + (0.010 if i % 2 else -0.008), y, z0 + 0.115 + dz),
                 "MAT_BLOCKOUT_ACCENT_ORANGE", padre)
    print("  lampara de lava: 7 piezas, 0.40 m de alto")


def reloj():
    """Circulo con agujas. Quedan quietas: en la web se animan girando el
    empty RELOJ_AGUJAS, que ya esta centrado en el eje."""
    def calcular():
        v = bpy.data.objects.get("CLOCK_WALL")
        return (v.location.x, v.location.y, v.location.z,
                v.dimensions.x / 2) if v else None

    pos = ancla("reloj", calcular)
    padre = ancla_padre("reloj", lambda: (
        bpy.data.objects.get("CLOCK_WALL").parent
        if bpy.data.objects.get("CLOCK_WALL")
        else bpy.data.objects.get("DECOR_NORTH_ROOT")))
    if pos is None:
        print("  no encuentro donde va el reloj")
        return
    x, y, z, r = pos
    viejo = bpy.data.objects.get("CLOCK_WALL")
    if viejo:
        bpy.data.objects.remove(viejo, do_unlink=True)

    ROT = (math.radians(90), 0, 0)     # el disco mira al sur
    cilindro("CLOCK_CASE", r, 0.045, 16, (x, y, z), "MAT_BLOCKOUT_PLASTIC_BLACK",
             padre, rot=ROT)
    cilindro("CLOCK_FACE", r * 0.86, 0.010, 16, (x, y - 0.026, z),
             "MAT_BLOCKOUT_PAPER", padre, rot=ROT)
    for i in range(12):                # marcas horarias
        a = math.tau * i / 12
        largo = 0.030 if i % 3 == 0 else 0.018
        box("CLOCK_MARK_%02d" % (i + 1), (0.014, 0.006, largo),
            (x + math.sin(a) * r * 0.72, y - 0.032, z + math.cos(a) * r * 0.72),
            PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK", rotation=(0, a, 0),
            parent=padre, sector=SECTOR, props={"asset_type": "clock"})

    from lib_blockout import root
    eje = root("CLOCK_HANDS_PIVOT", (x, y - 0.038, z), PROPS, SECTOR,
               {"asset_type": "clock",
                "notes": "girar en Y para animar la hora en la web"})
    eje.parent = padre
    eje.matrix_parent_inverse = Matrix.Identity(4)
    # Agujas quietas, marcando las 10:10, que es como se fotografia un reloj
    for nombre, largo, ancho, ang in (("HOUR", r * 0.48, 0.018, -60.0),
                                      ("MINUTE", r * 0.72, 0.012, 60.0)):
        o = box("CLOCK_HAND_" + nombre, (ancho, 0.008, largo),
                (0, 0, 0), PROPS, "MAT_BLOCKOUT_PLASTIC_BLACK",
                sector=SECTOR, props={"asset_type": "clock"})
        o.parent = eje
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.rotation_euler = (0, math.radians(ang), 0)
        o.location = (math.sin(math.radians(ang)) * largo / 2, 0,
                      math.cos(math.radians(ang)) * largo / 2)
    print("  reloj: caja, esfera, 12 marcas y 2 agujas sobre un eje")


def reja():
    """De panel macizo a reja: barras verticales y horizontales."""
    def calcular():
        p = bpy.data.objects.get("GRID_PANEL")
        return (p.location.x, p.location.y, p.location.z,
                p.dimensions.x, p.dimensions.z) if p else None

    pos = ancla("reja", calcular)
    padre = ancla_padre("reja", lambda: (
        bpy.data.objects.get("GRID_PANEL").parent
        if bpy.data.objects.get("GRID_PANEL")
        else bpy.data.objects.get("DECOR_NORTH_ROOT")))
    if pos is None:
        print("  no encuentro donde va la reja")
        return
    x, y, z, w, h = pos
    t = 0.022
    panel = bpy.data.objects.get("GRID_PANEL")
    if panel:
        bpy.data.objects.remove(panel, do_unlink=True)

    nv, nh = 11, 6
    for i in range(nv):
        bx = x - w / 2 + w * i / (nv - 1)
        box("GRID_BAR_V_%02d" % (i + 1), (t, t, h), (bx, y, z), PROPS,
            "MAT_BLOCKOUT_METAL", parent=padre, sector=SECTOR,
            props={"asset_type": "grid"})
    for j in range(nh):
        bz = z - h / 2 + h * j / (nh - 1)
        box("GRID_BAR_H_%02d" % (j + 1), (w, t * 0.9, t * 0.9), (x, y, bz),
            PROPS, "MAT_BLOCKOUT_METAL", parent=padre, sector=SECTOR,
            props={"asset_type": "grid"})
    print("  reja: %d barras verticales y %d horizontales (antes 1 panel macizo)"
          % (nv, nh))


def agrandar_vinilos():
    n = 0
    for i in range(1, 7):
        o = bpy.data.objects.get("VINYL_WALL_%02d" % i)
        if not o:
            continue
        # Se reescribe la caja conservando el centro
        resize_box(o, (VINYL, o.dimensions.y, VINYL), o.location)
        n += 1
    print("  vinilos: %d a %.2f m de lado" % (n, VINYL))


def polaroids_norte():
    """Tres veces mas grandes: a 11 cm no se veian."""
    for i in range(1, 5):
        o = bpy.data.objects.get("PHOTO_NORTH_%02d" % i)
        if o:
            resize_box(o, (POLAROID_NORTE[0], 0.025, POLAROID_NORTE[1]), o.location)
    print("  polaroids norte: 4 a %.0f x %.0f cm"
          % (POLAROID_NORTE[0] * 100, POLAROID_NORTE[1] * 100))


def polaroids_escalera():
    """Los siete cuadros de la escalera pasan a polaroids del mismo tamano."""
    for i in range(1, 8):
        o = bpy.data.objects.get("FRAME_STAIR_%02d" % i)
        if o:
            resize_box(o, (POLAROID_ESCALERA[0], 0.025, POLAROID_ESCALERA[1]),
                       o.location)
    print("  escalera: 7 polaroids de %.0f x %.0f cm"
          % (POLAROID_ESCALERA[0] * 100, POLAROID_ESCALERA[1] * 100))


def cuaderno():
    """El cuaderno pasa de bloque macizo a tapa + hojas + contratapa.

    Un bloque no se puede abrir. La tapa de arriba se construye con su origen
    sobre el lomo: girandola en X se abre sola, sin mover nada mas. Queda
    cerrada; la animacion es cosa de la web."""
    def calcular():
        v = bpy.data.objects.get("NOTEBOOK_EAST")
        return tuple(v.location) if v else None

    pos = ancla("cuaderno", calcular)
    padre = ancla_padre("cuaderno", lambda: (
        bpy.data.objects.get("NOTEBOOK_EAST").parent
        if bpy.data.objects.get("NOTEBOOK_EAST")
        else bpy.data.objects.get("TABLE_EAST_01_ROOT")))
    if pos is None:
        print("  no encuentro donde va el cuaderno")
        return
    x, y, z = pos
    w, d = 0.30, 0.22
    tapa, hojas = 0.006, 0.020
    base_z = z - 0.017
    for n in ("NOTEBOOK_EAST", "NOTEBOOK_EAST_BAND", "NOTEBOOK_EAST_RIBBON"):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)

    box("NOTEBOOK_EAST_COVER_BOTTOM", (w, d, tapa),
        (x, y, base_z + tapa / 2), PROPS, "MAT_NOTEBOOK_LEATHER",
        parent=padre, sector=SECTOR, props={"asset_type": "book"})
    box("NOTEBOOK_EAST", (w - 0.012, d - 0.014, hojas),
        (x, y, base_z + tapa + hojas / 2), PROPS, "MAT_BLOCKOUT_PAPER",
        parent=padre, sector=SECTOR,
        props={"asset_type": "paper", "notes": "el taco de hojas"})

    # Tapa de arriba con el origen sobre el lomo (canto norte)
    from lib_blockout import box_verts, BOX_FACES
    verts = [(vx, vy - d / 2, vz) for vx, vy, vz in box_verts((w, d, tapa))]
    mesh = bpy.data.meshes.new("NOTEBOOK_EAST_COVER_TOP_MESH")
    mesh.from_pydata(verts, [], BOX_FACES)
    mesh.update()
    o = bpy.data.objects.new("NOTEBOOK_EAST_COVER_TOP", mesh)
    o.location = (x, y + d / 2, base_z + tapa + hojas + tapa / 2)
    o.data.materials.append(mat("MAT_NOTEBOOK_LEATHER"))
    PROPS.objects.link(o)
    o.parent = padre
    o.matrix_parent_inverse = Matrix.Identity(4)
    from lib_blockout import tag
    tag(o, SECTOR, {"asset_type": "book",
                    "notes": "origen sobre el lomo: girar en X abre el cuaderno"})

    # Elastico y senalador, otra vez
    box("NOTEBOOK_EAST_BAND", (w - 0.02, 0.016, tapa * 2 + hojas + 0.006),
        (x, y - d / 2 + 0.045, base_z + (tapa * 2 + hojas) / 2), PROPS,
        "MAT_BLOCKOUT_ACCENT_ORANGE", parent=padre, sector=SECTOR,
        props={"asset_type": "book"})
    print("  cuaderno: contratapa + hojas + tapa con bisagra en el lomo")


def lava_sin_sombra():
    """La luz de la lava estaba adentro de la campana cerrada.

    Una malla cerrada que proyecta sombra atrapa la luz que tiene adentro: la
    lampara se veia encendida y no iluminaba nada. Se le saca la proyeccion de
    sombra a la campana y a la tapa, que es lo que se hace con toda practica."""
    for n in ("LAVA_CAMPANA", "LAVA_TAPA", "LAVA_BURBUJA_01",
              "LAVA_BURBUJA_02", "LAVA_BURBUJA_03"):
        o = bpy.data.objects.get(n)
        if o:
            o.visible_shadow = False
    luz = bpy.data.objects.get("LIGHT_LAVA")
    if luz:
        luz.data.energy = 90.0
        luz.data.shadow_soft_size = 0.10
        luz["_energia_base"] = 90.0
    print("  lava: campana sin proyectar sombra, luz a 90 W")


def apuntar_riel():
    """El spot mas al sur del riel: apunta al cuadro pero lava toda la pared.

    La orientacion se calcula UNA sola vez. Despues queda a cargo del usuario:
    si el script volviera a apuntarlo, le pisaria el ajuste manual cada vez.
    Lo que si se aplica siempre es la apertura del cono, que es lo que hace
    que ademas del cuadro se ilumine el resto de la pared."""
    luz = bpy.data.objects.get("LIGHT_TRACK_01")
    if not luz:
        print("  falta LIGHT_TRACK_01")
        return
    sc = bpy.context.scene
    if "riel_apuntado" not in sc:
        cuadro = bpy.data.objects.get("POSTER_WEST_02")
        if cuadro:
            from mathutils import Vector
            destino = cuadro.matrix_world.translation + Vector((0.10, 0.0, 0.0))
            luz.rotation_euler = (
                destino - luz.matrix_world.translation).to_track_quat(
                    "-Z", "Y").to_euler()
        sc["riel_apuntado"] = 1
        print("  riel sur: apuntado al cuadro (primera y unica vez)")
    else:
        print("  riel sur: orientacion respetada, la ajustaste vos")
    if hasattr(luz.data, "spot_size"):
        luz.data.spot_size = math.radians(96)      # antes 52: era un foco
        luz.data.spot_blend = 0.85
    luz["_energia_base"] = 46.0
    luz.data.energy = 46.0
    print("  cono de 96 grados y 46 W: baña la pared entera")

    graze = bpy.data.objects.get("LIGHT_WEST_GRAZE")
    if graze:
        graze.data.energy = 34.0
        print("  rasante de la pared oeste a 34 W")


def varios():
    rev = bpy.data.objects.get("MAGAZINE_TABLE_01")
    if rev:
        resize_box(rev, (0.34, 0.25, 0.038),
                   (rev.location.x, rev.location.y, rev.location.z + 0.012))
        rev["asset_type"] = "book"
        print("  revista de la mesa ratona -> libro de 3.8 cm de lomo")

    canasta = bpy.data.objects.get("RECORDS_BASKET")
    if canasta:
        canasta.data.materials.clear()
        canasta.data.materials.append(mat("MAT_BLOCKOUT_WOOD_PLAIN"))
        print("  caja de la discoteca -> madera de una pieza")

    puerta = bpy.data.materials.get("MAT_BLOCKOUT_DOOR")
    if puerta:
        b = next((n for n in puerta.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b:
            b.inputs["Base Color"].default_value = (0.20, 0.11, 0.06, 1.0)
        print("  puerta: verde -> marron")


def guardar_anclas():
    """Calcula y guarda TODAS las anclas antes de borrar nada.

    Si se calcularan dentro de cada funcion, ya seria tarde: clear_sector
    corre primero y se lleva puestas las piezas de la corrida anterior, que
    son justamente de donde hay que sacar la posicion."""
    def caja_de(prefijo):
        piezas = [o for o in bpy.data.objects
                  if o.name.startswith(prefijo) and o.type == "MESH"]
        if not piezas:
            return None
        xs = [o.location.x for o in piezas]
        zs = [o.location.z for o in piezas]
        return (sum(xs) / len(xs), piezas[0].location.y, sum(zs) / len(zs),
                max(xs) - min(xs), max(zs) - min(zs))

    def calc_reloj():
        v = bpy.data.objects.get("CLOCK_WALL")
        if v:
            return (v.location.x, v.location.y, v.location.z, v.dimensions.x / 2)
        c = bpy.data.objects.get("CLOCK_CASE")     # de una corrida anterior
        if c:
            return (c.location.x, c.location.y, c.location.z, c.dimensions.x / 2)
        return None

    def calc_reja():
        p = bpy.data.objects.get("GRID_PANEL")
        if p:
            return (p.location.x, p.location.y, p.location.z,
                    p.dimensions.x, p.dimensions.z)
        c = caja_de("GRID_BAR_")                   # de una corrida anterior
        if c:
            return (c[0], c[1], c[2], c[3] + 0.022, c[4] + 0.022)
        return None

    ancla("reloj", calc_reloj)
    ancla_padre("reloj", lambda: _padre_de("CLOCK_WALL", "CLOCK_CASE",
                                           "DECOR_NORTH_ROOT"))
    ancla("reja", calc_reja)
    ancla_padre("reja", lambda: _padre_de("GRID_PANEL", "GRID_BAR_V_01",
                                          "DECOR_NORTH_ROOT"))


def _padre_de(*nombres):
    for n in nombres:
        o = bpy.data.objects.get(n)
        if o:
            return o.parent or o
    return None


def main():
    global PROPS, FURN
    PROPS = col("30_PROPS")
    FURN = col("20_FURNITURE")
    from lib_blockout import PALETTE
    PALETTE["MAT_BLOCKOUT_WOOD_PLAIN"] = ((0.245, 0.16, 0.10), 0.9)
    # La mochila negra sobre una manta oscura y en sombra se leia como un
    # cuadrado. Sube el albedo del cuerpo y las piezas de encima aun mas,
    # para que la silueta se despegue sola.
    PALETTE["MAT_BACKPACK"] = ((0.150, 0.145, 0.140), 0.75)
    PALETTE["MAT_BACKPACK_POCKET"] = ((0.215, 0.208, 0.200), 0.70)
    PALETTE["MAT_NOTEBOOK_LEATHER"] = ((0.075, 0.045, 0.030), 0.65)

    guardar_anclas()
    print("Objetos PROPS2 reemplazados:", clear_sector(SECTOR))
    mochila()
    lampara_lava()
    cuaderno()
    reloj()
    reja()
    agrandar_vinilos()
    polaroids_norte()
    polaroids_escalera()
    varios()
    lava_sin_sombra()
    apuntar_riel()
    save(out_path(sys.argv, bpy.data.filepath))


main()
