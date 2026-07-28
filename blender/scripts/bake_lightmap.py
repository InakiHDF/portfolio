"""
HORNEAR LA ILUMINACION FIJA EN UN ATLAS GLOBAL
==============================================

Trabaja siempre sobre una copia. Crea UV2 (LIGHTMAP), empaqueta todas las
mallas visibles en un atlas, hornea luz directa + indirecta sin color y deja
el atlas conectado como Occlusion para que glTF exporte TEXCOORD_1.

El sistema del proyector queda deliberadamente fuera del bake:
  - LIGHT_SCREEN
  - PROJECTOR_BEAM
  - la emision de MAT_SCREEN_PROJ

Uso:
  Blender --background ENTRADA.blend --python bake_lightmap.py -- \
    SALIDA.blend ATLAS.png SALIDA.glb [tamano] [samples]
"""

import json
import os
import sys
import time

import bpy


PROJECTOR_LIGHTS = {"LIGHT_SCREEN"}
PROJECTOR_MESHES = {"PROJECTOR_BEAM"}
UV_NAME = "LIGHTMAP"
IMAGE_NAME = "LIGHTMAP_ATLAS"
NODE_NAME = "LIGHTMAP_BAKE"


def args():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(extra) < 3:
        raise SystemExit("faltan SALIDA.blend ATLAS.png SALIDA.glb")
    return extra[0], extra[1], extra[2], int(extra[3]) if len(extra) > 3 else 4096, int(extra[4]) if len(extra) > 4 else 64


def visible_meshes():
    return [
        o for o in bpy.context.scene.objects
        if o.type == "MESH" and not o.hide_render and o.name not in PROJECTOR_MESHES
    ]


def disable_projector():
    state = {"objects": {}, "emission": []}
    for name in PROJECTOR_LIGHTS | PROJECTOR_MESHES:
        obj = bpy.data.objects.get(name)
        if obj:
            state["objects"][name] = obj.hide_render
            obj.hide_render = True

    mat = bpy.data.materials.get("MAT_SCREEN_PROJ")
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED" and "Emission Strength" in node.inputs:
                socket = node.inputs["Emission Strength"]
                state["emission"].append((socket, socket.default_value))
                socket.default_value = 0.0
    return state


def restore_projector(state):
    for name, hidden in state["objects"].items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = hidden
    for socket, value in state["emission"]:
        socket.default_value = value


def make_unique_and_apply_scale(meshes):
    # El lightmap pertenece al objeto, no a una malla instanciada.
    for obj in meshes:
        if obj.data.users > 1:
            obj.data = obj.data.copy()

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def create_and_pack_uv2(meshes):
    for obj in meshes:
        uv = obj.data.uv_layers.get(UV_NAME) or obj.data.uv_layers.new(name=UV_NAME)
        # El atlas debe estar activo solamente mientras Blender hornea. No debe
        # quedar como UV de render: las texturas base que no tienen un nodo UV
        # explícito dependen del UV original (TEXCOORD_0 en glTF).
        obj.data.uv_layers.active = uv

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.lightmap_pack(
        PREF_CONTEXT="ALL_FACES",
        PREF_PACK_IN_ONE=True,
        PREF_NEW_UVLAYER=False,
        PREF_BOX_DIV=24,
        PREF_MARGIN_DIV=0.25,
    )
    bpy.ops.object.mode_set(mode="OBJECT")


def restore_base_uv(meshes):
    """Deja UV0 para materiales y LIGHTMAP como UV2 explícito del atlas."""
    repaired = 0
    for obj in meshes:
        layers = obj.data.uv_layers
        base = next((uv for uv in layers if uv.name != UV_NAME), None)
        if base is None:
            # Las mallas sin UV original no tienen texturas base que preservar.
            base = layers.get(UV_NAME)
        if base is None:
            continue
        for uv in layers:
            uv.active_render = uv == base
        layers.active = base
        repaired += 1
    return repaired


def new_atlas(path, size):
    old = bpy.data.images.get(IMAGE_NAME)
    if old:
        bpy.data.images.remove(old)
    image = bpy.data.images.new(IMAGE_NAME, width=size, height=size, alpha=False, float_buffer=False)
    image.filepath_raw = path
    image.file_format = "PNG"
    image.colorspace_settings.name = "Non-Color"
    return image


def gltf_occlusion_group():
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
    if not group.interface.items_tree.get("Occlusion"):
        group.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return group


def attach_atlas(meshes, image):
    group = gltf_occlusion_group()
    materials = {m for obj in meshes for m in obj.data.materials if m}
    for mat in materials:
        mat.use_nodes = True
        tree = mat.node_tree
        for node in list(tree.nodes):
            if node.name in {NODE_NAME, NODE_NAME + "_UV", NODE_NAME + "_GLTF"}:
                tree.nodes.remove(node)

        uv = tree.nodes.new("ShaderNodeUVMap")
        uv.name = NODE_NAME + "_UV"
        uv.uv_map = UV_NAME
        tex = tree.nodes.new("ShaderNodeTexImage")
        tex.name = NODE_NAME
        tex.image = image
        # La textura artística es pixelada; la iluminación debe interpolarse.
        tex.interpolation = "Linear"
        out = tree.nodes.new("ShaderNodeGroup")
        out.name = NODE_NAME + "_GLTF"
        out.node_tree = group
        tree.links.new(uv.outputs["UV"], tex.inputs["Vector"])
        tree.links.new(tex.outputs["Color"], out.inputs["Occlusion"])
        tree.nodes.active = tex
        tex.select = True
    return len(materials)


def bake(meshes, image, samples, size):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type != "CPU"
        scene.cycles.device = "GPU"
    except Exception as exc:
        print("METAL no disponible, se usa CPU:", exc)
        scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 1
    scene.render.bake.target = "IMAGE_TEXTURES"
    scene.render.bake.margin = max(8, size // 128)
    scene.render.bake.use_clear = True
    scene.render.bake.use_pass_direct = True
    scene.render.bake.use_pass_indirect = True
    scene.render.bake.use_pass_color = False

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.bake(type="DIFFUSE")
    image.save()


def export_glb(path):
    for obj in bpy.data.objects:
        if obj.hide_get():
            obj.hide_viewport = True
    options = dict(
        filepath=path,
        export_format="GLB",
        use_visible=True,
        export_apply=True,
        export_extras=True,
        export_cameras=True,
        export_lights=False,
        export_yup=True,
        export_image_format="AUTO",
        export_materials="EXPORT",
        export_normals=True,
        export_tangents=False,
        export_animations=False,
    )
    valid = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    bpy.ops.export_scene.gltf(**{k: v for k, v in options.items() if k in valid})


def main():
    blend_out, atlas_path, glb_out, size, samples = args()
    for path in (blend_out, atlas_path, glb_out):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    started = time.time()
    projector_state = disable_projector()
    meshes = visible_meshes()
    make_unique_and_apply_scale(meshes)
    create_and_pack_uv2(meshes)
    image = new_atlas(atlas_path, size)
    material_count = attach_atlas(meshes, image)
    bake(meshes, image, samples, size)
    restored_uvs = restore_base_uv(meshes)
    restore_projector(projector_state)

    bpy.context.scene["lightmap_atlas"] = os.path.basename(atlas_path)
    bpy.context.scene["lightmap_uv"] = UV_NAME
    bpy.context.scene["lightmap_projector_excluded"] = True
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    export_glb(glb_out)

    print("BAKE_RESULT=" + json.dumps({
        "blend": blend_out,
        "atlas": atlas_path,
        "glb": glb_out,
        "size": size,
        "samples": samples,
        "meshes": len(meshes),
        "materials": material_count,
        "base_uvs_restored": restored_uvs,
        "seconds": round(time.time() - started, 1),
    }))


main()
