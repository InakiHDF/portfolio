"""
GENERADOR DE TEXTURAS DE SUPERFICIE
===================================

Reglas del sistema, iguales para todas:

  TEXEL = 2.5 cm en el mundo. Medido desde la camara fija, eso da entre 3.4
  y 7.1 pixeles de pantalla por texel segun la distancia. Lo cercano se ve
  mas grueso, que es como se comporta un juego con texturas en espacio de
  mundo. Es UN solo numero para toda la habitacion.

  Todas se cuantizan a pocos colores. Ninguna es color plano: la variacion
  de tono entre bloques es lo que las hace leer como material.

  Todas repiten sin costura.

Los patrones no salen de mi cabeza: salen de mirar las referencias ampliadas.
La pared es un aparejo de bloques chatos; la madera son duelas verticales
cada una de un tono distinto; el piso es un tejido fino; la alfombra son
manchones grandes.

Uso:
  python3 tools/make_textures.py           # genera todas + hoja de contacto
"""

import os

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "blender", "textures", "surface")

TEXEL_CM = 2.5
TILE = 64                     # texels por lado -> 1.60 m de baldosa


# ---------------------------------------------------------------------------
# RUIDO
# ---------------------------------------------------------------------------

def valor(w, h, celdas, seed):
    """Ruido de valor que repite sin costura, por interpolacion de una grilla."""
    rng = np.random.default_rng(seed)
    g = rng.random((celdas, celdas)).astype(np.float32)
    ys = np.arange(h, dtype=np.float32) / h * celdas
    xs = np.arange(w, dtype=np.float32) / w * celdas
    y0 = np.floor(ys).astype(int) % celdas
    x0 = np.floor(xs).astype(int) % celdas
    y1, x1 = (y0 + 1) % celdas, (x0 + 1) % celdas
    fy = (ys - np.floor(ys))[:, None]
    fx = (xs - np.floor(xs))[None, :]
    fy = fy * fy * (3 - 2 * fy)          # suavizado
    fx = fx * fx * (3 - 2 * fx)
    a = g[np.ix_(y0, x0)] * (1 - fx) + g[np.ix_(y0, x1)] * fx
    b = g[np.ix_(y1, x0)] * (1 - fx) + g[np.ix_(y1, x1)] * fx
    return a * (1 - fy) + b * fy


def fractal(w, h, seed, octavas=3, celdas=4):
    out = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octavas):
        out += valor(w, h, celdas * (2 ** o), seed + o * 101) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def bloques(w, h, bw, bh, seed):
    """Un valor al azar por bloque. La base de todo lo que es 'de a modulos'."""
    rng = np.random.default_rng(seed)
    nx, ny = int(np.ceil(w / bw)), int(np.ceil(h / bh))
    g = rng.random((ny, nx)).astype(np.float32)
    return np.repeat(np.repeat(g, bh, axis=0), bw, axis=1)[:h, :w]


# ---------------------------------------------------------------------------
# PALETAS  (tomadas de las referencias, ajustadas a albedo)
# ---------------------------------------------------------------------------

def rampa(colores, n):
    """Interpola una lista de colores a n pasos."""
    c = np.array(colores, dtype=np.float32) / 255.0
    xs = np.linspace(0, len(c) - 1, n)
    i0 = np.floor(xs).astype(int)
    i1 = np.minimum(i0 + 1, len(c) - 1)
    f = (xs - i0)[:, None]
    return c[i0] * (1 - f) + c[i1] * f


def aplicar(v, pal):
    """Mapea un campo 0..1 a una paleta discreta. Aca nace el look retro."""
    idx = np.clip((v * len(pal)).astype(int), 0, len(pal) - 1)
    return pal[idx]


def a_lineal(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def a_srgb(a):
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def calibrar(a, objetivo):
    """Ajusta la textura para que su albedo MEDIO EN LINEAL de `objetivo`.

    Sin esto la escena se oscurece: los colores salen de referencias que ya
    estan iluminadas, y ademas el PNG es sRGB mientras que el color plano que
    reemplaza estaba en lineal. Son dos espacios distintos y la diferencia
    llega al 84 por ciento."""
    if objetivo is None:
        return a
    lin = a_lineal(a)
    for _ in range(6):
        m = float(lin.mean())
        if m < 1e-6:
            break
        lin = np.clip(lin * (objetivo / m), 0.0, 1.0)
        if abs(float(lin.mean()) - objetivo) < objetivo * 0.02:
            break
    return a_srgb(lin)


# ---------------------------------------------------------------------------
# PATRONES
# ---------------------------------------------------------------------------

def pared(w=TILE, h=TILE, seed=1):
    """Aparejo de bloques chatos, trabado, con junta apenas mas oscura."""
    # Los dos tienen que dividir TILE, si no la baldosa no cierra.
    bw, bh = 8, 4                        # 20 x 10 cm
    v = np.zeros((h, w), dtype=np.float32)
    rng = np.random.default_rng(seed)
    filas = h // bh
    for f in range(filas):
        desfase = (f * bw // 2) % w      # traba a media pieza
        tonos = rng.random(w // bw + 2)
        for i, t in enumerate(tonos):
            x0 = (desfase + i * bw) % w
            for dx in range(bw):
                v[f * bh:(f + 1) * bh, (x0 + dx) % w] = t
    v = v * 0.55 + fractal(w, h, seed + 7, octavas=2, celdas=6) * 0.45
    junta = np.ones((h, w), dtype=np.float32)
    junta[::bh, :] *= 0.55               # linea horizontal de junta
    v = v * (0.75 + 0.25 * junta)
    pal = rampa([(92, 86, 78), (116, 108, 98), (134, 126, 115), (148, 140, 128)], 6)
    return aplicar(v, pal)


def piso(w=TILE, h=TILE, seed=2):
    """Tablas largas con veta fina en diagonal, cada tabla de otro tono."""
    tabla_h = 5                          # 12.5 cm de ancho de tabla
    v = bloques(w, h, w, tabla_h, seed) * 0.5
    # corte de las tablas a lo largo, desfasado por fila
    corte = bloques(w, h, 16, tabla_h, seed + 3) * 0.22
    veta = fractal(w, h, seed + 9, octavas=3, celdas=16)
    # La frecuencia tiene que dar un numero ENTERO de periodos en la
    # baldosa, si no el seno no cierra al repetir.
    fase = (np.arange(w)[None, :] * 2 + np.arange(h)[:, None]) * (2 * np.pi * 6 / w)
    diag = np.sin(fase) * 0.5 + 0.5
    v = v + corte + veta * 0.20 + diag * 0.08
    v[::tabla_h, :] *= 0.72              # junta entre tablas
    pal = rampa([(96, 72, 46), (124, 96, 62), (146, 116, 78), (166, 136, 96)], 6)
    return aplicar(np.clip(v, 0, 1), pal)


def duelas(w=TILE, h=TILE, seed=3, claro=False):
    """Madera de mueble: duelas verticales angostas, tono muy dispar entre si.

    Esa disparidad es la firma de la referencia. Si las duelas comparten
    tono, la madera vuelve a leer como plastico pintado."""
    dw = 4                               # 10 cm por duela
    v = bloques(w, h, dw, h, seed) * 0.62
    v += bloques(w, h, dw, 16, seed + 5) * 0.24     # cortes a lo largo
    v += fractal(w, h, seed + 12, octavas=3, celdas=20) * 0.14
    v[:, ::dw] *= 0.70                   # junta vertical
    base = ([(74, 52, 34), (98, 70, 44), (122, 90, 58), (144, 110, 72)] if claro
            else [(38, 26, 16), (54, 37, 22), (72, 50, 30), (92, 66, 40)])
    return aplicar(np.clip(v, 0, 1), rampa(base, 6))


def alfombra(w=140, h=90, seed=4):
    """Alfombra tejida: bandas de orilla y un campo de rombos.

    No repite: se mapea una sola vez sobre el objeto, por eso puede tener
    orilla de verdad. El camuflaje anterior no leia como alfombra.
    """
    C_OSCURO, C_MEDIO, C_CLARO, C_CREMA = 0, 1, 2, 3
    m = np.full((h, w), C_MEDIO, dtype=np.int32)

    # Campo: rombos en grilla al tresbolillo
    cw, ch = 20, 14
    yy, xx = np.mgrid[0:h, 0:w]
    fil = yy // ch
    despl = (fil % 2) * (cw // 2)
    dx = ((xx + despl) % cw) - cw / 2.0
    dy = (yy % ch) - ch / 2.0
    d = np.abs(dx) / (cw / 2.0) + np.abs(dy) / (ch / 2.0)
    m[d < 0.95] = C_CREMA
    m[d < 0.52] = C_OSCURO
    m[(d >= 0.95) & (d < 1.15)] = C_CLARO

    # Orillas concentricas
    borde = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    m[borde < 9] = C_CLARO
    m[borde < 7] = C_OSCURO
    m[borde < 4] = C_CREMA
    m[borde < 2] = C_OSCURO

    # Desgaste: algunos texels saltan de tono, como fibra gastada
    rng = np.random.default_rng(seed)
    ruido = fractal(w, h, seed + 3, octavas=3, celdas=7)
    gasto = (ruido > 0.62) & (rng.random((h, w)) < 0.35)
    m[gasto & (m == C_MEDIO)] = C_CLARO
    m[gasto & (m == C_CREMA)] = C_CLARO

    pal = np.array([(30, 25, 21), (62, 52, 42), (116, 98, 80), (176, 156, 132)],
                   dtype=np.float32) / 255.0
    return pal[m]


def tela(w=TILE, h=TILE, seed=5, clara=False):
    """Trama de tejido.

    La trama tiene que insinuarse, no dibujarse: con amplitud alta el damero
    de hilos se lee como tablero de ajedrez y arruina almohadas y sabanas.
    La variacion la aporta sobre todo el ruido, no la grilla."""
    hilo = ((np.arange(w)[None, :] // 2 + np.arange(h)[:, None] // 2) % 2)
    amp = 0.05 if clara else 0.10
    v = fractal(w, h, seed, octavas=3, celdas=8) * 0.70 + hilo * amp + 0.15
    base = ([(186, 184, 182), (200, 198, 195), (212, 210, 206), (222, 220, 216)]
            if clara else
            [(40, 46, 58), (52, 60, 74), (64, 74, 90), (78, 88, 106)])
    return aplicar(np.clip(v, 0, 1), rampa(base, 5))


def hormigon(w=TILE, h=TILE, seed=6):
    """Escalones y plataforma: granulado con manchas."""
    v = fractal(w, h, seed, octavas=4, celdas=8) * 0.72
    rng = np.random.default_rng(seed + 2)
    v += (rng.random((h, w)) < 0.09) * 0.22          # grano suelto
    pal = rampa([(88, 84, 78), (106, 102, 95), (124, 119, 111), (140, 135, 126)], 5)
    return aplicar(np.clip(v, 0, 1), pal)


def metal(w=TILE, h=TILE, seed=7):
    """Metal negro mate con cepillado horizontal apenas perceptible."""
    v = fractal(w, h, seed, octavas=2, celdas=24) * 0.55
    v += (np.arange(h)[:, None] % 4 == 0) * 0.12
    pal = rampa([(16, 16, 18), (26, 26, 29), (38, 38, 42), (52, 52, 56)], 4)
    return aplicar(np.clip(v, 0, 1), pal)


def papel(w=TILE, h=TILE, seed=8):
    """Fibra de papel: grano fino, casi sin contraste."""
    v = fractal(w, h, seed, octavas=4, celdas=16) * 0.7 + 0.15
    pal = rampa([(198, 194, 186), (214, 210, 202), (228, 224, 216),
                 (238, 235, 228)], 4)
    return aplicar(np.clip(v, 0, 1), pal)


def follaje(w=TILE, h=TILE, seed=9):
    """Hoja: nervadura y manchas de tono, no verde plano."""
    nervio = (np.abs(((np.arange(w)[None, :] % 9) - 4.5)) < 0.9) * 0.22
    v = fractal(w, h, seed, octavas=3, celdas=9) * 0.68 + nervio + 0.10
    pal = rampa([(26, 52, 22), (38, 74, 30), (54, 96, 40), (74, 120, 52)], 5)
    return aplicar(np.clip(v, 0, 1), pal)


def ceramica(w=TILE, h=TILE, seed=10):
    """Barro esmaltado: motas y variacion suave."""
    v = fractal(w, h, seed, octavas=3, celdas=12) * 0.6 + 0.2
    rng = np.random.default_rng(seed + 1)
    v += (rng.random((h, w)) < 0.05) * 0.18
    pal = rampa([(126, 118, 108), (152, 144, 132), (176, 168, 156),
                 (196, 188, 176)], 4)
    return aplicar(np.clip(v, 0, 1), pal)


def plastico(w=TILE, h=TILE, seed=11, base=(28, 28, 32)):
    """Plastico: casi liso, con una variacion minima para que no sea plano."""
    v = fractal(w, h, seed, octavas=2, celdas=20) * 0.5 + 0.25
    b = np.array(base, dtype=np.float32)
    pal = rampa([tuple(b * 0.75), tuple(b), tuple(b * 1.25), tuple(b * 1.5)], 4)
    return aplicar(np.clip(v, 0, 1), pal)


def pintado(w=TILE, h=TILE, seed=12, base=(96, 58, 34)):
    """Madera pintada: duelas anchas y desgaste en las juntas."""
    dw = 10
    v = bloques(w, h, dw, h, seed) * 0.35 + 0.35
    v += fractal(w, h, seed + 4, octavas=3, celdas=14) * 0.22
    v[:, ::dw] *= 0.72
    b = np.array(base, dtype=np.float32)
    pal = rampa([tuple(b * 0.65), tuple(b), tuple(b * 1.3), tuple(b * 1.6)], 5)
    return aplicar(np.clip(v, 0, 1), pal)


def plastico_blanco(w=TILE, h=TILE, seed=27):
    """Plastico blanco de aparato.

    El generico `plastico` reparte la rampa entre 0.75 y 1.5 veces la base, y
    sobre un blanco eso deja manchas grises bien visibles. Aca la variacion
    es de menos del 4 por ciento: se lee blanco, con apenas vida."""
    v = fractal(w, h, seed, octavas=2, celdas=26)
    pal = rampa([(236, 234, 230), (243, 241, 238), (249, 248, 245)], 3)
    return aplicar(np.clip(v, 0, 1), pal)


def madera_lisa(w=TILE, h=TILE, seed=28):
    """Madera de una pieza: veta fina, sin tablas ni juntas.

    Para cajones y cajas donde el entablado de `duelas` se lee como error de
    escala: son piezas chicas y el despiece queda enorme."""
    veta = fractal(w, h, seed, octavas=4, celdas=3)
    fino = fractal(w, h, seed + 40, octavas=2, celdas=30)
    v = veta * 0.72 + fino * 0.28
    pal = rampa([(86, 62, 40), (104, 76, 50), (120, 90, 60), (134, 102, 70)], 4)
    return aplicar(np.clip(v, 0, 1), pal)


def pantalla_lisa(w=16, h=16, seed=14):
    """Pantalla de proyeccion: tiene que ser LISA.

    Una tela con trama visible aca lee como error: la pantalla es la
    superficie mas plana del cuarto y ademas es fuente de luz."""
    v = fractal(w, h, seed, octavas=1, celdas=4) * 0.10 + 0.72
    pal = rampa([(206, 206, 204), (214, 214, 212), (220, 220, 218)], 3)
    return aplicar(np.clip(v, 0, 1), pal)


def display(w=TILE, h=TILE, seed=16, base=(24, 110, 190)):
    """Display encendido: lineas de barrido horizontales."""
    linea = (np.arange(h)[:, None] % 3 == 0) * 0.30
    v = fractal(w, h, seed, octavas=2, celdas=18) * 0.25 + linea + 0.42
    b = np.array(base, dtype=np.float32)
    pal = rampa([tuple(b * 0.55), tuple(b), tuple(np.minimum(b * 1.4, 255))], 4)
    return aplicar(np.clip(v, 0, 1), pal)


# nombre -> (funcion, kwargs, albedo lineal objetivo)
PATRONES = {
    "TEX_ARCH":          (pared, {}, 0.597),
    "TEX_FLOOR":         (piso, {}, 0.330),
    "TEX_WOOD":          (duelas, {}, 0.153),
    "TEX_WOOD_LIGHT":    (duelas, {"claro": True, "seed": 13}, 0.280),
    "TEX_RUG":           (alfombra, {}, 0.240),
    "TEX_FABRIC":        (tela, {}, 0.240),
    "TEX_FABRIC_LIGHT":  (tela, {"clara": True, "seed": 15}, 0.727),
    "TEX_STAIR":         (hormigon, {}, 0.467),
    "TEX_METAL":         (metal, {}, 0.060),
    "TEX_SKIRTING":      (plastico, {"seed": 21, "base": (78, 82, 90)}, 0.323),
    "TEX_DOOR":          (pintado, {}, 0.157),
    "TEX_SCREEN":        (plastico, {"seed": 22, "base": (14, 14, 18)}, 0.023),
    "TEX_PLASTIC_BLACK": (plastico, {"seed": 23}, 0.043),
    "TEX_PAPER":         (papel, {}, 0.790),
    "TEX_PLANT":         (follaje, {}, 0.150),
    "TEX_CERAMIC":       (ceramica, {}, 0.517),
    "TEX_ACCENT_BLUE":   (display, {}, 0.393),
    "TEX_PLASTIC_BLUE":  (plastico, {"seed": 24, "base": (40, 70, 108)}, 0.223),
    "TEX_ACCENT_ORANGE": (pintado, {"seed": 25, "base": (150, 66, 24)}, 0.353),
    "TEX_PLASTIC_LIGHT": (plastico_blanco, {}, 0.800),
    "TEX_WOOD_PLAIN":    (madera_lisa, {}, 0.245),
    "TEX_SCREEN_PROJ":   (pantalla_lisa, {}, 0.720),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    hechas = []
    for nombre, (fn, kw, objetivo) in PATRONES.items():
        a = calibrar(fn(**kw), objetivo)
        img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
        img.save(os.path.join(OUT, nombre + ".png"))
        colores = len(set(map(tuple, np.round(a * 255).astype(int).reshape(-1, 3).tolist())))
        medio = float(a_lineal(a).mean())
        hechas.append((nombre, img.size, colores))
        print("%-20s %3dx%-3d texels  %2d colores  albedo %.3f (pedido %.3f)"
              % (nombre, img.size[0], img.size[1], colores, medio, objetivo))

    # Hoja de contacto: cada textura repetida 2x2 para ver que no tenga costura
    cel = 260
    cols = 3
    filas = (len(hechas) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * cel, filas * cel), (16, 16, 18))
    for i, (nombre, _, _) in enumerate(hechas):
        t = Image.open(os.path.join(OUT, nombre + ".png"))
        rep = Image.new("RGB", (t.width * 2, t.height * 2))
        for dx in (0, 1):
            for dy in (0, 1):
                rep.paste(t, (dx * t.width, dy * t.height))
        hoja.paste(rep.resize((cel, cel), Image.NEAREST),
                   ((i % cols) * cel, (i // cols) * cel))
    dest = os.path.join(REPO, "blender", "renders", "HOJA_TEXTURAS.png")
    hoja.save(dest)
    print("\nhoja (cada una repetida 2x2 para ver costuras):", dest)

    # Comprobacion dura: la columna 0 tiene que continuar de la ultima, y
    # lo mismo entre la fila 0 y la ultima. Si no, hay costura visible.
    print("\nCOSTURAS")
    for nombre, _, _ in hechas:
        a = np.asarray(Image.open(os.path.join(OUT, nombre + ".png")),
                       dtype=np.int16)
        dx = np.abs(a[:, 0] - a[:, -1]).mean()
        dy = np.abs(a[0, :] - a[-1, :]).mean()
        # Se compara contra el salto mas grande que ya existe adentro: si la
        # textura tiene juntas, un salto grande al envolver es correcto.
        col = np.abs(a[:, 1:] - a[:, :-1]).mean(axis=(0, 2))
        fil = np.abs(a[1:, :] - a[:-1, :]).mean(axis=(1, 2))
        max_x, max_y = col.max(), fil.max()
        ok = dx <= max_x * 1.05 and dy <= max_y * 1.05
        print("  %-20s envolver=%5.1f/%5.1f   mayor interno=%5.1f/%5.1f   %s"
              % (nombre, dx, dy, max_x, max_y, "ok" if ok else "COSTURA"))


if __name__ == "__main__":
    main()
