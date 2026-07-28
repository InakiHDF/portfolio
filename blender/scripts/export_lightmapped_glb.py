"""Religa un atlas ya limpio y exporta la copia horneada sin luces runtime."""

import os
import sys
import bpy


extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(extra) < 2:
    raise SystemExit("uso: ATLAS.png SALIDA.glb")

atlas_path, glb_path = map(os.path.abspath, extra[:2])
image = bpy.data.images.get("LIGHTMAP_ATLAS")
if image is None:
    raise SystemExit("la copia no contiene LIGHTMAP_ATLAS")
image.filepath = atlas_path
image.filepath_raw = atlas_path
image.reload()

repaired_uvs = 0
for obj in bpy.data.objects:
    if obj.type == "MESH":
        layers = obj.data.uv_layers
        base = next((uv for uv in layers if uv.name != "LIGHTMAP"), None)
        if base is not None:
            for uv in layers:
                uv.active_render = uv == base
            layers.active = base
            repaired_uvs += 1
    if obj.hide_get():
        obj.hide_viewport = True

bpy.context.scene["lightmap_atlas"] = os.path.basename(atlas_path)
bpy.context.scene["lightmap_base_uvs_restored"] = repaired_uvs
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)

options = dict(
    filepath=glb_path,
    export_format="GLB",
    use_visible=True,
    export_apply=True,
    export_extras=True,
    export_cameras=True,
    export_lights=True,
    export_yup=True,
    export_image_format="AUTO",
    export_materials="EXPORT",
    export_normals=True,
    export_tangents=False,
    export_animations=False,
)
valid = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
bpy.ops.export_scene.gltf(**{k: v for k, v in options.items() if k in valid})
print("LIGHTMAP_EXPORT:", glb_path, "base UVs restaurados:", repaired_uvs)
