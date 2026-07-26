"""
Utilidades compartidas por los scripts de construccion del blockout.

Regla central: cada objeto creado por un script lleva la propiedad "sector".
Al reconstruir un sector solo se borran los objetos con ESE sector, nunca los
que hayas creado o editado vos a mano.
"""

import bpy
from mathutils import Matrix

# ---------------------------------------------------------------------------
# MATERIALES
# ---------------------------------------------------------------------------

PALETTE = {
    "MAT_BLOCKOUT_ARCH":          ((0.62, 0.60, 0.57), 0.9),
    "MAT_BLOCKOUT_FLOOR":         ((0.45, 0.33, 0.21), 0.9),
    "MAT_BLOCKOUT_SKIRTING":      ((0.30, 0.32, 0.35), 0.9),
    "MAT_BLOCKOUT_STAIR":         ((0.48, 0.47, 0.45), 0.9),
    "MAT_BLOCKOUT_DOOR":          ((0.12, 0.22, 0.13), 0.8),
    "MAT_BLOCKOUT_METAL":         ((0.06, 0.06, 0.06), 0.4),
    "MAT_BLOCKOUT_WOOD":          ((0.24, 0.14, 0.08), 0.9),
    "MAT_BLOCKOUT_WOOD_LIGHT":    ((0.42, 0.27, 0.15), 0.9),
    "MAT_BLOCKOUT_FABRIC":        ((0.20, 0.23, 0.29), 0.9),
    "MAT_BLOCKOUT_FABRIC_LIGHT":  ((0.72, 0.72, 0.74), 0.9),
    "MAT_BLOCKOUT_SCREEN":        ((0.02, 0.02, 0.03), 0.3),
    "MAT_BLOCKOUT_PLASTIC_BLACK": ((0.04, 0.04, 0.05), 0.6),
    "MAT_BLOCKOUT_PAPER":         ((0.82, 0.80, 0.75), 0.9),
    "MAT_BLOCKOUT_PLANT":         ((0.09, 0.28, 0.08), 0.8),
    "MAT_BLOCKOUT_CERAMIC":       ((0.55, 0.52, 0.48), 0.6),
    "MAT_BLOCKOUT_RUG":           ((0.26, 0.24, 0.22), 1.0),
    "MAT_BLOCKOUT_ACCENT_BLUE":   ((0.08, 0.40, 0.70), 0.5),
    "MAT_BLOCKOUT_PLASTIC_BLUE":  ((0.07, 0.22, 0.38), 0.6),
    "MAT_BLOCKOUT_ACCENT_ORANGE": ((0.72, 0.26, 0.08), 0.7),
    "MAT_BLOCKOUT_EMISSIVE":      ((1.00, 0.72, 0.34), 0.4),
}

EMISSIVE = {"MAT_BLOCKOUT_EMISSIVE", "MAT_BLOCKOUT_ACCENT_BLUE"}


def mat(name):
    """Devuelve el material, creandolo la primera vez. Nunca duplica."""
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    rgb, rough = PALETTE.get(name, ((0.8, 0.0, 0.8), 0.9))  # magenta = falta
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        if name in EMISSIVE:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 2.0
    m.diffuse_color = (*rgb, 1.0)
    return m


# ---------------------------------------------------------------------------
# GEOMETRIA
# ---------------------------------------------------------------------------

BOX_FACES = [
    (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
    (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
]


def box_verts(size):
    sx, sy, sz = (s / 2.0 for s in size)
    return [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
    ]


def resize_box(obj, size, location=None):
    """Reescribe los vertices de una caja existente sin recrear el objeto.
    Conserva nombre, propiedades, materiales y estado de visibilidad."""
    mesh = obj.data
    mesh.clear_geometry()
    mesh.from_pydata(box_verts(size), [], BOX_FACES)
    mesh.update()
    if location is not None:
        obj.location = location
    return obj


def box(name, size, location, collection, material=None, rotation=None,
        parent=None, sector=None, props=None):
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(box_verts(size), [], BOX_FACES)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    if material:
        obj.data.materials.append(mat(material) if isinstance(material, str) else material)
    collection.objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
    tag(obj, sector, props)
    return obj


def root(name, location, collection, sector=None, props=None):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.25
    obj.location = location
    collection.objects.link(obj)
    tag(obj, sector, props)
    return obj


def tag(obj, sector=None, props=None):
    base = {"status": "blockout", "style": "low_poly_pixelated"}
    if sector:
        base["sector"] = sector
    base.update(props or {})
    for key, value in base.items():
        obj[key] = value
    return obj


# ---------------------------------------------------------------------------
# ESCENA
# ---------------------------------------------------------------------------

def col(name):
    c = bpy.data.collections.get(name)
    if c is None:
        raise RuntimeError("No existe la coleccion %s" % name)
    return c


def clear_sector(sector):
    """Borra los objetos generados por este sector.

    Candado: los objetos con status="approved" NUNCA se borran. Cuando un
    sector queda revisado se marca con close_sector.py y a partir de ahi
    volver a correr su script no puede destruir nada."""
    victims, locked = [], 0
    for o in bpy.data.objects:
        if o.get("sector") != sector:
            continue
        if o.get("status") == "approved":
            locked += 1
            continue
        victims.append(o)
    if locked:
        print("PROTEGIDOS (status=approved), no se tocan: %d objeto(s)" % locked)
        if not victims:
            raise RuntimeError(
                "El sector %s esta cerrado. Si de verdad querés regenerarlo, "
                "primero desmarcá status=approved." % sector)
    for o in victims:
        bpy.data.objects.remove(o, do_unlink=True)
    return len(victims)


def obj(name, required=True):
    o = bpy.data.objects.get(name)
    if o is None and required:
        raise RuntimeError("No existe el objeto %s" % name)
    return o


def out_path(argv, default):
    """Lee la ruta de salida despues de '--' en la linea de comandos."""
    import sys
    if "--" in sys.argv:
        extra = sys.argv[sys.argv.index("--") + 1:]
        if extra:
            return extra[0]
    return default


def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("\nGUARDADO:", path)
    print("Objetos en escena:", len(bpy.data.objects))
