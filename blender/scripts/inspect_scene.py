"""Vuelca el estado exacto de cada objeto: transform local, mundo, dimensiones."""
import bpy, math

def deg(v):
    return tuple(round(math.degrees(a), 1) for a in v)

def r3(v):
    return tuple(round(a, 3) for a in v)

for col in sorted(bpy.data.collections, key=lambda c: c.name):
    if not col.objects:
        continue
    print("\n[%s]  visible=%s" % (col.name, not col.hide_viewport))
    for obj in sorted(col.objects, key=lambda o: o.name):
        w = obj.matrix_world.translation
        print("  %-24s type=%-6s hide=%s" % (obj.name, obj.type, obj.hide_viewport or obj.hide_render))
        print("      loc  =%s   rot=%s   scale=%s" % (r3(obj.location), deg(obj.rotation_euler), r3(obj.scale)))
        print("      world=%s   dim=%s" % (r3(w), r3(obj.dimensions)))
        if obj.parent:
            print("      parent=%s" % obj.parent.name)
        props = {k: obj[k] for k in obj.keys() if not k.startswith("_")}
        if props:
            print("      props=%s" % props)
