"""
SONDA DE LUZ — mide la iluminación real del cuarto en un punto
==============================================================

El problema que resuelve: la habitación está horneada en un lightmap, así que
cada rincón tiene su brillo y su color propios, pero nada de eso alcanza a un
objeto agregado después. El avatar quedaba con una iluminación inventada,
uniforme, que no se parecía a la de las cosas que tenía al lado.

Esto fotografía el entorno desde el punto donde está el avatar y lo resume en
9 coeficientes de armónicos esféricos: el color y la dirección de la luz que
de verdad le llega ahí. La página los usa en el shader del avatar. Es el mismo
horneado que tienen las paredes, pero para él.

Se renderiza un cubo de seis caras y no una panorámica: en un cubo la
dirección de cada píxel se conoce exactamente, sin depender de a qué convención
de ejes se ajuste la cámara equirectangular de Blender.

Devuelve los coeficientes ya en los ejes de three.js (Y arriba) y en el orden
que espera `SphericalHarmonics3`.
"""

import math
import os
import tempfile

import bpy
from mathutils import Matrix, Vector

LADO = 24          # píxeles por cara del cubo
MUESTRAS = 24

# Las seis caras. Cada una es hacia dónde mira la cámara y cuál es su "arriba".
CARAS = (
    (Vector((1, 0, 0)), Vector((0, 0, 1))),
    (Vector((-1, 0, 0)), Vector((0, 0, 1))),
    (Vector((0, 1, 0)), Vector((0, 0, 1))),
    (Vector((0, -1, 0)), Vector((0, 0, 1))),
    (Vector((0, 0, 1)), Vector((0, 1, 0))),
    (Vector((0, 0, -1)), Vector((0, 1, 0))),
)


def _base(mira, arriba):
    """Matriz de cámara: mira a `mira`, con la cámara apuntando a su -Z."""
    z = -mira.normalized()
    x = arriba.cross(z)
    if x.length < 1e-6:
        x = Vector((1, 0, 0))
    x.normalize()
    y = z.cross(x)
    return Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z))).to_4x4()


def _armar_escena(escena):
    previo = {
        "engine": escena.render.engine,
        "x": escena.render.resolution_x,
        "y": escena.render.resolution_y,
        "pct": escena.render.resolution_percentage,
        "formato": escena.render.image_settings.file_format,
        "profundidad": escena.render.image_settings.color_depth,
        "vista": escena.view_settings.view_transform,
        "exposicion": escena.view_settings.exposure,
        "filepath": escena.render.filepath,
        "camara": escena.camera,
    }
    escena.render.engine = "BLENDER_EEVEE"
    escena.render.resolution_x = escena.render.resolution_y = LADO
    escena.render.resolution_percentage = 100
    escena.render.image_settings.file_format = "OPEN_EXR"
    escena.render.image_settings.color_depth = "32"
    # Sin AgX ni exposición: la sonda mide radiancia lineal, no una foto.
    escena.view_settings.view_transform = "Standard"
    escena.view_settings.exposure = 0.0
    if hasattr(escena.eevee, "taa_render_samples"):
        escena.eevee.taa_render_samples = MUESTRAS
    return previo


def _restaurar(escena, previo):
    escena.render.engine = previo["engine"]
    escena.render.resolution_x = previo["x"]
    escena.render.resolution_y = previo["y"]
    escena.render.resolution_percentage = previo["pct"]
    escena.render.image_settings.file_format = previo["formato"]
    escena.render.image_settings.color_depth = previo["profundidad"]
    escena.view_settings.view_transform = previo["vista"]
    escena.view_settings.exposure = previo["exposicion"]
    escena.render.filepath = previo["filepath"]
    escena.camera = previo["camara"]


def _base_sh(d):
    """Los 9 armónicos reales, en el orden de three.js SphericalHarmonics3."""
    x, y, z = d
    return (
        0.282095,
        0.488603 * y, 0.488603 * z, 0.488603 * x,
        1.092548 * x * y, 1.092548 * y * z,
        0.315392 * (3.0 * z * z - 1.0),
        1.092548 * x * z, 0.546274 * (x * x - y * y),
    )


def medir(punto, ocultar=()):
    """Coeficientes SH de la luz que llega a `punto`, en ejes de three.js.

    `ocultar` son los objetos que no deben entrar en la medición: el propio
    avatar, que si no se mide a sí mismo.
    """
    escena = bpy.context.scene
    previo = _armar_escena(escena)
    escondidos = [(o, o.hide_render) for o in ocultar]
    for o, _ in escondidos:
        o.hide_render = True

    cam_datos = bpy.data.cameras.new("SONDA")
    cam_datos.type = "PERSP"
    cam_datos.sensor_fit = "AUTO"
    cam_datos.lens_unit = "FOV"
    cam_datos.angle = math.radians(90.0)
    cam = bpy.data.objects.new("SONDA", cam_datos)
    escena.collection.objects.link(cam)
    escena.camera = cam

    coef = [[0.0, 0.0, 0.0] for _ in range(9)]
    carpeta = tempfile.mkdtemp()
    try:
        for i, (mira, arriba) in enumerate(CARAS):
            giro = _base(mira, arriba)
            cam.matrix_world = Matrix.Translation(punto) @ giro

            ruta = os.path.join(carpeta, "cara%d.exr" % i)
            escena.render.filepath = ruta
            bpy.ops.render.render(write_still=True)

            img = bpy.data.images.load(ruta)
            pix = list(img.pixels)          # RGBA lineal, fila de abajo primero
            bpy.data.images.remove(img)

            for fila in range(LADO):
                for col in range(LADO):
                    u = 2.0 * (col + 0.5) / LADO - 1.0
                    v = 2.0 * (fila + 0.5) / LADO - 1.0
                    # Dirección del píxel en espacio de cámara (mira a -Z).
                    d = Vector((u, v, -1.0))
                    largo2 = d.length_squared
                    d.normalize()
                    mundo = (giro.to_3x3() @ d).normalized()

                    # De ejes de Blender (Z arriba) a los de three.js (Y arriba).
                    tres = (mundo.x, mundo.z, -mundo.y)

                    # Ángulo sólido del píxel de un cubo.
                    dw = (4.0 / (LADO * LADO)) / (largo2 * math.sqrt(largo2))

                    p = (fila * LADO + col) * 4
                    rgb = (pix[p], pix[p + 1], pix[p + 2])
                    for k, Y in enumerate(_base_sh(tres)):
                        peso = Y * dw
                        coef[k][0] += rgb[0] * peso
                        coef[k][1] += rgb[1] * peso
                        coef[k][2] += rgb[2] * peso
    finally:
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.cameras.remove(cam_datos)
        for o, estaba in escondidos:
            o.hide_render = estaba
        _restaurar(escena, previo)
        for f in os.listdir(carpeta):
            os.remove(os.path.join(carpeta, f))
        os.rmdir(carpeta)

    return [[round(c, 5) for c in banda] for banda in coef]
