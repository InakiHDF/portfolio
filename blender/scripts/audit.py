"""
AUDITORIA DE LA ESCENA
======================

Recorre el archivo abierto e informa el estado segun las reglas del brief.
No modifica nada.

Uso:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
      blender/HABITACION_v001.blend --python blender/scripts/audit.py
"""

import bpy

GENERIC = ("Cube", "Plane", "Sphere", "Cylinder", "Empty", "Material",
           "Camera", "Light", "Suzanne", "Icosphere", "Circle", "Cone", "Torus")

EXPECTED_COLLECTIONS = [
    "00_REFERENCES", "10_ARCHITECTURE_LOCKED", "20_FURNITURE", "30_PROPS",
    "40_LIGHTS", "50_CAMERAS", "60_MATERIALS_GUIDES", "80_WIP",
    "90_APPROVED", "99_EXPORT",
]


def section(title):
    print("\n" + "-" * 62)
    print(title)
    print("-" * 62)


def main():
    scene = bpy.context.scene

    section("1. ESCENA")
    print("  Escena          :", scene.name)
    print("  Unidades        :", scene.unit_settings.system,
          "/", scene.unit_settings.length_unit,
          "/ scale", scene.unit_settings.scale_length)
    print("  Resolucion      : %dx%d" % (scene.render.resolution_x,
                                         scene.render.resolution_y))
    print("  Camara activa   :", scene.camera.name if scene.camera else "NINGUNA")
    print("  Objetos totales :", len(bpy.data.objects))
    tris = sum(len(o.data.loop_triangles) if o.type == "MESH" and
               o.data.loop_triangles else 0 for o in bpy.data.objects)
    verts = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == "MESH")
    print("  Vertices        :", verts, "| caras:",
          sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH"))

    section("2. COLECCIONES")
    present = {c.name for c in bpy.data.collections}
    for name in EXPECTED_COLLECTIONS:
        col = bpy.data.collections.get(name)
        count = len(col.objects) if col else 0
        mark = "  OK " if col else "  -- "
        print("%s %-26s %d objeto(s)" % (mark, name, count))
    extra = present - set(EXPECTED_COLLECTIONS) - {"SCENE_ROOT"}
    if extra:
        print("  Colecciones fuera del esquema:", ", ".join(sorted(extra)))

    section("3. CAMARAS")
    for obj in sorted((o for o in bpy.data.objects if o.type == "CAMERA"),
                      key=lambda o: o.name):
        bgs = len(obj.data.background_images)
        print("  %-12s loc=(%.2f, %.2f, %.2f)  rotZ=%6.1f  lens=%.1fmm  fondos=%d"
              % (obj.name, *obj.location,
                 obj.rotation_euler.z * 57.29578, obj.data.lens, bgs))

    section("4. OBJETOS POR COLECCION")
    for name in EXPECTED_COLLECTIONS:
        col = bpy.data.collections.get(name)
        if not col or not col.objects:
            continue
        print("  [%s]" % name)
        for obj in sorted(col.objects, key=lambda o: o.name):
            dim = "%.2f x %.2f x %.2f" % tuple(obj.dimensions)
            parent = " -> hijo de %s" % obj.parent.name if obj.parent else ""
            print("     %-26s %-22s %s%s"
                  % (obj.name, dim, obj.get("status", "?"), parent))

    section("5. PROBLEMAS DETECTADOS")
    problems = []
    for obj in bpy.data.objects:
        if any(obj.name.startswith(g) for g in GENERIC):
            problems.append("nombre generico: " + obj.name)
        s = obj.scale
        if obj.type == "MESH" and any(abs(v - 1.0) > 1e-4 for v in s):
            problems.append("escala sin aplicar: %s (%.3f, %.3f, %.3f)"
                            % (obj.name, *s))
        if obj.type == "MESH" and not obj.data.materials:
            problems.append("sin material: " + obj.name)
        if obj.type == "MESH" and len(obj.data.polygons) > 5000:
            problems.append("malla densa (%d caras): %s"
                            % (len(obj.data.polygons), obj.name))
        if not obj.users_collection:
            problems.append("fuera de toda coleccion: " + obj.name)
    for mat in bpy.data.materials:
        if any(mat.name.startswith(g) for g in GENERIC) or "." in mat.name:
            problems.append("material con nombre generico o duplicado: " + mat.name)

    if problems:
        for p in problems:
            print("  !", p)
    else:
        print("  Ninguno.")

    section("6. MATERIALES")
    for mat in sorted(bpy.data.materials, key=lambda m: m.name):
        print("  %-32s %d usuario(s)" % (mat.name, mat.users))

    print("\nAuditoria terminada.\n")


main()
