# PS2-ish automático para un avatar GLB de Avaturn
# Probado conceptualmente para Blender 4.x/5.x.
# No cambia la geometría ni las UV: conserva cara, pelo, ropa y rig.
# Hace los materiales más mate, elimina detalles PBR modernos,
# usa muestreo de textura "Closest" y configura un render retro.

import bpy

# ---------- AJUSTES ----------
ANCHO = 640
ALTO = 480
TEXTURA_MAX = 512       # 512 = retro moderado; 256 = más pixelado
DESACTIVAR_NORMALS = True
DESACTIVAR_METAL = True
RUGOSIDAD = 0.9
ESPECULAR = 0.15
SOMBREADO_PLANO = False # True = polígonos más visibles; puede afear la cara
# ----------------------------

def entrada(principled, *nombres):
    for nombre in nombres:
        sock = principled.inputs.get(nombre)
        if sock:
            return sock
    return None

# Render retro y rápido
scene = bpy.context.scene
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    pass

scene.render.resolution_x = ANCHO
scene.render.resolution_y = ALTO
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

# Procesar materiales sin rehacer las UV
imagenes_vistas = set()

for mat in bpy.data.materials:
    if not mat or not mat.use_nodes or not mat.node_tree:
        continue

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    for node in nodes:
        if node.type == "TEX_IMAGE" and node.image:
            # Pixelado limpio, sin interpolación borrosa
            node.interpolation = "Closest"

            # Reducir resolución sin tocar el mapeado UV
            img = node.image
            if img.name not in imagenes_vistas:
                imagenes_vistas.add(img.name)
                try:
                    w, h = img.size
                    if w > 0 and h > 0 and max(w, h) > TEXTURA_MAX:
                        escala = TEXTURA_MAX / max(w, h)
                        nuevo_w = max(1, round(w * escala))
                        nuevo_h = max(1, round(h * escala))
                        img.scale(nuevo_w, nuevo_h)
                        try:
                            img.pack()
                        except Exception:
                            pass
                except Exception as exc:
                    print(f"No se pudo reducir {img.name}: {exc}")

    for node in nodes:
        if node.type != "BSDF_PRINCIPLED":
            continue

        roughness = entrada(node, "Roughness", "Rugosidad")
        if roughness:
            roughness.default_value = RUGOSIDAD

        specular = entrada(
            node,
            "Specular IOR Level",
            "Specular",
            "Nivel IOR especular",
            "Especular",
        )
        if specular:
            specular.default_value = ESPECULAR

        metallic = entrada(node, "Metallic", "Metálico")
        if metallic and DESACTIVAR_METAL:
            # Desconectar mapas metálicos y dejar valor cero
            for link in list(metallic.links):
                links.remove(link)
            metallic.default_value = 0.0

        normal = entrada(node, "Normal")
        if normal and DESACTIVAR_NORMALS:
            for link in list(normal.links):
                links.remove(link)

# Sombreado opcional
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    for poly in obj.data.polygons:
        poly.use_smooth = not SOMBREADO_PLANO

print("Listo: estilo PS2-ish aplicado sin rehacer texturas ni UV.")
print(f"Render: {ANCHO}x{ALTO}; texturas: máximo {TEXTURA_MAX}px.")
