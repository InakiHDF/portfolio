"""
TANDA 2 — LO QUE NO PUEDE SER UNA CAJA
======================================

Reemplaza la malla de las plantas, las almohadas y la manta por geometria
propia. NO crea ni borra objetos: le cambia la malla a los que ya existen,
asi conservan nombre, padre, propiedades, materiales y las transformadas que
ajustaste vos. Cada modelo se construye para llenar el mismo volumen que
tenia la caja que reemplaza.

  Macetas    prisma de 12 lados con boca mas ancha que la base y labio
  Hojas      tiras curvas con doblez en V al medio (una hoja plana no
             engancha luz; el doblez si)
  Enredadera tallo que cae con hojas alternadas
  Almohadas  malla abombada con esquinas blandas
  Manta      malla con caida sobre los costados, dobladillo y arrugas

Uso:
  Blender --background ARCHIVO.blend --python refine_organic.py -- SALIDA.blend
"""

import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib_blockout import out_path, save

TAU = math.tau


# ---------------------------------------------------------------------------
# INFRAESTRUCTURA
# ---------------------------------------------------------------------------

def replace_mesh(name, verts, faces):
    """Cambia la malla de un objeto existente. Conserva todo lo demas."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        print("  FALTA", name)
        return None
    old = obj.data
    mats = [m for m in old.materials]

    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    for m in mats:
        mesh.materials.append(m)

    obj.data = mesh
    if old.users == 0:
        bpy.data.meshes.remove(old)

    d = obj.dimensions
    print("  %-24s %5d caras   %.2f x %.2f x %.2f"
          % (name, len(mesh.polygons), d.x, d.y, d.z))
    return obj


def grid_faces(verts, faces, ring_a, ring_b):
    """Une dos anillos de indices con quads."""
    for i in range(len(ring_a) - 1):
        faces.append((ring_a[i], ring_a[i + 1], ring_b[i + 1], ring_b[i]))


# ---------------------------------------------------------------------------
# MACETA
# ---------------------------------------------------------------------------

def pot(width, height, sides=12, taper=0.70, lip=0.055):
    """Prisma troncoconico: base angosta, boca ancha, labio saliente."""
    r_top = width / 2.0
    r_bot = r_top * taper
    body_h = height * (1.0 - lip)
    verts, faces = [], []

    def ring(r, z):
        start = len(verts)
        for i in range(sides):
            a = TAU * i / sides
            verts.append((r * math.cos(a), r * math.sin(a), z))
        return list(range(start, start + sides)) + [start]

    bot = ring(r_bot, 0.0)
    top = ring(r_top, body_h)
    rim_out = ring(r_top * 1.05, body_h)
    rim_top = ring(r_top * 1.05, height)
    inner = ring(r_top * 0.90, height - 0.012)

    grid_faces(verts, faces, bot, top)          # pared
    grid_faces(verts, faces, top, rim_out)      # arranque del labio
    grid_faces(verts, faces, rim_out, rim_top)  # canto del labio
    grid_faces(verts, faces, rim_top, inner)    # borde hacia adentro
    faces.append(tuple(reversed(bot[:-1])))     # fondo
    # Tierra: un n-gono hundido
    soil = ring(r_top * 0.90, height - 0.055)
    grid_faces(verts, faces, inner, soil)
    faces.append(tuple(soil[:-1]))

    z0 = -height / 2.0
    return [(x, y, z + z0) for x, y, z in verts], faces


# ---------------------------------------------------------------------------
# HOJAS
# ---------------------------------------------------------------------------

def blade(verts, faces, origin, azimuth, length, base_w, tip_w,
          elev_start, elev_end, fold, segments=6):
    """Una hoja: tira curva de quads con el nervio central levantado."""
    ca, sa = math.cos(azimuth), math.sin(azimuth)
    perp = (-sa, ca, 0.0)
    x, y, z = origin
    step = length / segments
    prev = None

    for i in range(segments + 1):
        t = i / segments
        if i:
            e = math.radians(elev_start + (elev_end - elev_start) * (t ** 0.8))
            x += step * math.cos(e) * ca
            y += step * math.cos(e) * sa
            z += step * math.sin(e)
        # Una hoja real no tiene ancho parejo: arranca angosta, se ensancha
        # cerca del primer tercio y termina en punta.
        bulge = math.sin(math.pi * min(1.0, t * 1.15 + 0.12)) ** 0.7
        w = max(base_w * max(0.06, bulge), tip_w * 0.5)
        rise = fold * (1.0 - t) * (1.0 - abs(2 * t - 1) * 0.4)
        base = len(verts)
        verts.append((x - perp[0] * w, y - perp[1] * w, z))
        verts.append((x, y, z + rise))
        verts.append((x + perp[0] * w, y + perp[1] * w, z))
        cur = (base, base + 1, base + 2)
        if prev:
            faces.append((prev[0], cur[0], cur[1], prev[1]))
            faces.append((prev[1], cur[1], cur[2], prev[2]))
        prev = cur
    return verts, faces


def rosette(width, height, count, base_w, tip_w, elev_a, elev_b, fold,
            seed_offset=0.0, stem_h=0.0):
    """Planta de hojas en abanico. Se construye dos veces: la primera para
    medir cuanto se va a deformar al encajarla en el volumen, la segunda ya
    con los anchos precompensados, si no las hojas salen finitas como pasto."""
    sx, sz = 1.0, 1.0
    for _ in range(2):
        verts, faces = _rosette_pass(width, height, count, base_w / sx,
                                     tip_w / sx, elev_a, elev_b, fold,
                                     seed_offset, stem_h)
        xs = [v[0] for v in verts]
        zs = [v[2] for v in verts]
        sx = width / max(1e-4, (max(xs) - min(xs)))
        sz = height / max(1e-4, (max(zs) - min(zs)))
    z0 = min(v[2] for v in verts)
    return ([(x * sx, y * sx, (z - z0) * sz - height / 2.0) for x, y, z in verts],
            faces)


def _rosette_pass(width, height, count, base_w, tip_w, elev_a, elev_b, fold,
                  seed_offset, stem_h):
    verts, faces = [], []
    reach = width / 2.0
    for i in range(count):
        a = TAU * i / count + seed_offset
        wobble = 0.85 + 0.30 * ((i * 7919) % 11) / 10.0
        length = math.hypot(reach, height - stem_h) * wobble
        blade(verts, faces, (0.0, 0.0, stem_h), a, length,
              base_w, tip_w,
              elev_a + ((i * 5717) % 7) * 2.0,
              elev_b + ((i * 3313) % 9) * 3.0,
              fold, segments=7)
    return verts, faces


def vine(length, thickness=0.012, leaves=9):
    """Tallo colgante con hojas alternadas."""
    verts, faces = [], []
    segments = 10
    pts = []
    for i in range(segments + 1):
        t = i / segments
        pts.append((0.055 * math.sin(t * 2.4) * t,
                    0.030 * math.sin(t * 3.7),
                    -length * t))
    prev = None
    for i, (x, y, z) in enumerate(pts):
        w = thickness * (1.0 - 0.45 * i / segments)
        base = len(verts)
        verts += [(x - w, y, z), (x, y + w, z), (x + w, y, z), (x, y - w, z)]
        cur = [base, base + 1, base + 2, base + 3]
        if prev:
            for k in range(4):
                faces.append((prev[k], cur[k], cur[(k + 1) % 4], prev[(k + 1) % 4]))
        prev = cur

    for i in range(leaves):
        t = 0.18 + 0.80 * i / max(1, leaves - 1)
        k = min(segments, int(t * segments))
        x, y, z = pts[k]
        a = TAU * (i * 0.41)
        blade(verts, faces, (x, y, z), a, 0.090, 0.042, 0.010,
              -18.0, -46.0, 0.010, segments=3)

    zs = [v[2] for v in verts]
    mid = (max(zs) + min(zs)) / 2.0
    return [(x, y, z - mid) for x, y, z in verts], faces


# ---------------------------------------------------------------------------
# ALMOHADA
# ---------------------------------------------------------------------------

def pillow(w, d, h, nx=10, ny=8, tilt=0.0):
    """Malla cerrada con perfil abombado: las esquinas se afinan solas."""
    half = h / 2.0
    top_idx, bot_idx = {}, {}
    verts, faces = [], []

    for j in range(ny + 1):
        for i in range(nx + 1):
            u = 2.0 * i / nx - 1.0
            v = 2.0 * j / ny - 1.0
            x, y = u * w / 2.0, v * d / 2.0
            bulge = ((1.0 - abs(u) ** 2.8) * (1.0 - abs(v) ** 2.8)) ** 0.42
            bulge = max(0.0, bulge)
            if bulge <= 1e-4:                      # borde: un solo vertice
                idx = len(verts)
                verts.append((x, y, 0.0))
                top_idx[(i, j)] = bot_idx[(i, j)] = idx
            else:
                z = half * bulge
                sag = 1.0 - 0.38 * bulge            # abajo se aplasta contra el colchon
                top_idx[(i, j)] = len(verts)
                verts.append((x, y, z + tilt * u * 0.35 * bulge))
                bot_idx[(i, j)] = len(verts)
                verts.append((x, y, -z * sag))

    for j in range(ny):
        for i in range(nx):
            a, b = top_idx[(i, j)], top_idx[(i + 1, j)]
            c, e = top_idx[(i + 1, j + 1)], top_idx[(i, j + 1)]
            if len({a, b, c, e}) == 4:
                faces.append((a, b, c, e))
            a, b = bot_idx[(i, j)], bot_idx[(i + 1, j)]
            c, e = bot_idx[(i + 1, j + 1)], bot_idx[(i, j + 1)]
            if len({a, b, c, e}) == 4:
                faces.append((e, c, b, a))
    return verts, faces


# ---------------------------------------------------------------------------
# MANTA
# ---------------------------------------------------------------------------

def blanket(w, d, h, mattress_half, drop, nx=18, ny=15):
    """Superficie que cae por los costados, con dobladillo al sur y arrugas."""
    top, bot = {}, {}
    verts, faces = [], []
    half_h = h / 2.0

    def surface(x, y):
        over = max(0.0, abs(x) - mattress_half) / max(1e-4, w / 2.0 - mattress_half)
        z = half_h - drop * (over ** 1.6)
        z += 0.016 * math.sin(x * 5.1 + y * 2.3)          # arrugas
        z += 0.011 * math.sin(x * 2.7 - y * 6.4 + 1.2)
        hem = math.exp(-((y + d / 2.0) / 0.16) ** 2)       # dobladillo al sur
        z += 0.045 * hem
        return z

    for j in range(ny + 1):
        for i in range(nx + 1):
            x = (i / nx - 0.5) * w
            y = (j / ny - 0.5) * d
            z = surface(x, y)
            top[(i, j)] = len(verts)
            verts.append((x, y, z))
            bot[(i, j)] = len(verts)
            verts.append((x, y, z - 0.030))

    for j in range(ny):
        for i in range(nx):
            faces.append((top[(i, j)], top[(i + 1, j)],
                          top[(i + 1, j + 1)], top[(i, j + 1)]))
            faces.append((bot[(i, j + 1)], bot[(i + 1, j + 1)],
                          bot[(i + 1, j)], bot[(i, j)]))
    for i in range(nx):                                   # cantos
        faces.append((top[(i, 0)], bot[(i, 0)], bot[(i + 1, 0)], top[(i + 1, 0)]))
        faces.append((top[(i + 1, ny)], bot[(i + 1, ny)], bot[(i, ny)], top[(i, ny)]))
    for j in range(ny):
        faces.append((top[(0, j + 1)], bot[(0, j + 1)], bot[(0, j)], top[(0, j)]))
        faces.append((top[(nx, j)], bot[(nx, j)], bot[(nx, j + 1)], top[(nx, j + 1)]))
    return verts, faces


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("MACETAS")
    replace_mesh("PLANT_WEST_POT", *pot(0.340, 0.380))
    replace_mesh("PLANT_NORTH_02_POT", *pot(0.440, 0.506, taper=0.76))
    replace_mesh("PLANT_HANGING_POT", *pot(0.200, 0.170, sides=10, taper=0.80))

    print("FOLLAJE")
    # Oeste: tipo yuca, hojas largas y punzantes muy abiertas
    replace_mesh("PLANT_WEST_FOLIAGE",
                 *rosette(0.560, 0.820, count=14, base_w=0.052, tip_w=0.008,
                          elev_a=76, elev_b=22, fold=0.022))
    # Noreste: mas alta, penacho arriba de un tallo
    replace_mesh("PLANT_NORTH_02_FOLIAGE",
                 *rosette(0.720, 1.400, count=13, base_w=0.060, tip_w=0.010,
                          elev_a=84, elev_b=30, fold=0.026,
                          seed_offset=0.4, stem_h=0.45))
    # Estante noroeste: matita chica y tupida
    replace_mesh("PLANT_SHELF_NW",
                 *rosette(0.300, 0.340, count=11, base_w=0.040, tip_w=0.007,
                          elev_a=62, elev_b=12, fold=0.014, seed_offset=0.9))

    print("ENREDADERA")
    for name, length in (("PLANT_HANGING_VINE_01", 0.52),
                         ("PLANT_HANGING_VINE_02", 0.34),
                         ("PLANT_HANGING_VINE_03", 0.66),
                         ("PLANT_HANGING_VINE_04", 0.24)):
        replace_mesh(name, *vine(length, leaves=max(4, int(length * 15))))

    print("CAMA")
    replace_mesh("PILLOW_L_PROXY", *pillow(0.680, 0.380, 0.150, tilt=0.10))
    replace_mesh("PILLOW_R_PROXY", *pillow(0.680, 0.380, 0.150, tilt=-0.14))
    # La manta baja por los costados del colchon: eso se sale del volumen
    # original hacia abajo, y tiene que ser asi para leerse como manta.
    replace_mesh("BLANKET_PROXY",
                 *blanket(1.900, 1.600, 0.100, mattress_half=0.860, drop=0.120))

    total = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
    print("\nCaras totales de la escena:", total)
    save(out_path(sys.argv, bpy.data.filepath))


main()
