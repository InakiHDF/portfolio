#!/usr/bin/env python3
"""
EL CONTENIDO REAL — de las fuentes a `web/contenido.js`
=======================================================

La página no sale a buscar nada en vivo: Substack no manda CORS, AOTY está
detrás de Cloudflare y las capturas necesitan un navegador. Todo eso se
resuelve acá, una vez, y queda commiteado.

Este script:

  1. Baja el archivo de Substack (título, subtítulo, fecha, URL, portada).
  2. Captura los tres sitios con Chrome headless.
  3. Baja las tapas de los discos favoritos de AOTY.
  4. Escribe `web/contenido.js`, que es lo único que lee `sala.js`.

Correrlo de nuevo cuando Iñaki publique un artículo o cambie un sitio:

    python3 tools/fetch_contenido.py

Es idempotente: reescribe todo desde cero. Si una fuente se cae, aborta sin
tocar `contenido.js`, así nunca deja la página a medias.
"""

import json
import re
import subprocess
import sys
import unicodedata
import urllib.request
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"
CONTENIDO = WEB / "contenido"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SUBSTACK = "https://inakigongorarosi.substack.com"

# Los tres sitios. El `nombre` es como los quiere Iñaki en la página, no el
# título que trae cada sitio.
SITIOS = [
    {
        "nombre": "helicopters.ar",
        "tipo": "Sitio institucional",
        "fecha": "2026",
        "url": "https://www.helicopters.com.ar",
        "descripcion": "Trabajo aéreo y alta montaña.",
        "slug": "helicopters",
        "captura_url": "https://www.helicopters.com.ar/es",
    },
    {
        "nombre": "Cru",
        "tipo": "Recetario personal",
        "fecha": "2026",
        "url": "https://cru-ten.vercel.app",
        "descripcion": "Un recetario que se lee como una revista.",
        "slug": "cru",
        "captura_url": "https://cru-ten.vercel.app/",
    },
    {
        "nombre": "Opus",
        "tipo": "Catálogo musical",
        "fecha": "2026",
        "url": "https://opus-alpha.vercel.app",
        "descripcion": "El catálogo de todo lo que sabés tocar.",
        "slug": "opus",
        "captura_url": "https://opus-alpha.vercel.app/",
    },
]

# El video vive en el repo, no se baja de ningún lado.
#
# `poster` es LA MINIATURA, y la elige Iñaki: es el cuadro que se ve en la tela
# del proyector antes de darle play y el que aparece en la tira si algún día hay
# más de un video. No se saca del mp4 ni se elige solo — se pone acá el archivo
# que él quiera, cualquier PNG o JPG dentro de `web/videos/`. El script verifica
# que exista y aborta si no.
VIDEOS = [
    {
        "titulo": "Cru. Launch Film",
        "tipo": "Launch film",
        "fecha": "2026",
        "archivo": "./videos/cru-launch.mp4",
        "poster": "./videos/cru-launch-poster.jpg",
        "url": "https://cru-ten.vercel.app",
    },
    # ─── PROVISORIO — BORRAR ────────────────────────────────────────────────
    # Ficha de relleno para poder ver la tira de selección, que con un solo
    # video no existe. Apunta al mismo mp4 y sólo cambia el título y la
    # miniatura. Se saca en cuanto haya un segundo video de verdad, o antes.
    {
        "titulo": "Video de prueba, para ver la tira",
        "tipo": "Prueba",
        "fecha": "2026",
        "archivo": "./videos/cru-launch.mp4",
        "poster": "./videos/prueba-poster.jpg",
        "url": "https://cru-ten.vercel.app",
    },
]

# AOTY. Cloudflare protege tanto el sitio como el CDN de tapas, así que esto
# no se puede scrapear ni bajar: va fijo acá y se actualiza a mano. Las tapas
# no se rehostean — las fichas de la pared son tipográficas.
AOTY_USUARIO = "inakihdf"
AOTY_PERFIL = f"https://www.albumoftheyear.org/user/{AOTY_USUARIO}/"
AOTY_RATINGS = 1151
AOTY_FAVORITOS = [
    ("Radiohead", "In Rainbows", "/album/363-radiohead-in-rainbows.php"),
    ("Deftones", "White Pony", "/album/2214-deftones-white-pony.php"),
    ("Magdalena Bay", "Imaginal Disk", "/album/1012480-magdalena-bay-imaginal-disk.php"),
    ("Black Country, New Road", "Ants From Up There",
     "/album/424961-black-country-new-road-ants-from-up-there.php"),
    ("Interpol", "Turn on the Bright Lights", "/album/578-interpol-turn-on-the-bright-lights.php"),
]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def bajar(url, referer=None):
    """Se baja con curl a propósito.

    El Python de este Mac no trae el paquete de certificados raíz, así que
    `urllib` falla en cualquier https. curl usa el llavero del sistema.
    """
    orden = ["curl", "-sSL", "--max-time", "60", "-A", UA]
    if referer:
        orden += ["-e", referer]
    r = subprocess.run(orden + [url], capture_output=True, timeout=90)
    if r.returncode or not r.stdout:
        raise RuntimeError(f"no se pudo bajar {url}: {r.stderr.decode()[:200] or 'respuesta vacía'}")
    return r.stdout


def slug(texto):
    limpio = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", limpio.lower()).strip("-")[:48]


def acento(ruta):
    """El color de acento de cada ficha sale de su propia imagen.

    Se toma el promedio y se lo lleva a una saturación y una luminosidad
    utilizables sobre papel oscuro: si se usa el promedio crudo, casi todas
    las fichas terminan del mismo gris.
    """
    from PIL import ImageStat
    im = Image.open(ruta).convert("RGB").resize((32, 32))
    r, g, b = ImageStat.Stat(im).mean

    import colorsys
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    r, g, b = colorsys.hls_to_rgb(h, min(max(l, 0.42), 0.62), min(max(s * 1.8, 0.32), 0.72))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def guardar_imagen(datos_o_ruta, destino, ancho, alto=None, calidad=86, recorte=False):
    """Normaliza cualquier fuente a un JPG del tamaño que necesita el canvas.

    `recorte=True` llena el marco y recorta el sobrante (capturas de sitio);
    si no, respeta la proporción original (tapas de disco, portadas).
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(datos_o_ruta, bytes):
        import io
        im = Image.open(io.BytesIO(datos_o_ruta))
    else:
        im = Image.open(datos_o_ruta)
    im = im.convert("RGB")

    if alto and recorte:
        escala = max(ancho / im.width, alto / im.height)
        im = im.resize((round(im.width * escala), round(im.height * escala)), Image.LANCZOS)
        x = (im.width - ancho) // 2
        im = im.crop((x, 0, x + ancho, min(alto, im.height)))
    else:
        escala = ancho / im.width
        im = im.resize((ancho, round(im.height * escala)), Image.LANCZOS)

    im.save(destino, "JPEG", quality=calidad, optimize=True, progressive=True)
    return destino


def capturar(url, destino_png):
    destino_png.parent.mkdir(parents=True, exist_ok=True)
    if destino_png.exists():
        destino_png.unlink()
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--virtual-time-budget=9000", "--window-size=1440,900",
         f"--screenshot={destino_png}", url],
        check=False, capture_output=True, timeout=120,
    )
    if not destino_png.exists() or destino_png.stat().st_size < 5000:
        raise RuntimeError(f"la captura de {url} salió vacía")
    return destino_png


def fecha_es(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f"{MESES[d.month - 1].capitalize()} {d.year}", d.strftime("%Y-%m-%d")


def textos():
    print("· Substack")
    crudo = json.loads(bajar(f"{SUBSTACK}/api/v1/archive?sort=new&limit=50&offset=0"))
    if not isinstance(crudo, list) or not crudo:
        raise RuntimeError("el archivo de Substack vino vacío")

    salida = []
    for post in crudo:
        if post.get("audience") not in (None, "everyone", "only_paid", "founding"):
            continue
        titulo = (post.get("title") or "").strip()
        if not titulo:
            continue
        subtitulo = (post.get("subtitle") or post.get("description") or "").strip()
        legible, orden = fecha_es(post["post_date"])
        ficha = {
            "titulo": titulo,
            "subtitulo": subtitulo,
            "fecha": legible,
            "orden": orden,
            "url": post["canonical_url"],
            "color": "#7c8d99",
        }

        portada = post.get("cover_image")
        if portada:
            nombre = f"{orden}-{slug(titulo)}.jpg"
            ruta = CONTENIDO / "portadas" / nombre
            try:
                guardar_imagen(bajar(portada), ruta, 760, 428, recorte=True)
                ficha["portada"] = f"./contenido/portadas/{nombre}"
                ficha["color"] = acento(ruta)
            except Exception as e:
                print(f"  ! sin portada para «{titulo}»: {e}")

        salida.append(ficha)
        print(f"  {orden}  {titulo}")
    return salida


def logo(sitio):
    """El favicon del sitio, el mismo que se ve en la pestaña del navegador.

    Se prefiere el más grande que declare el HTML: `apple-touch-icon` suele ser
    de 180 px y los `icon` con `sizes` a veces llegan a 512. El `/favicon.ico`
    de toda la vida queda de último recurso. Los SVG se saltean porque PIL no
    los abre; si no queda ninguno usable, devuelve None y la página dibuja la
    inicial del sitio en su lugar — nunca un hueco.
    """
    destino = CONTENIDO / "logos" / f"{sitio['slug']}.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    base = sitio["captura_url"]

    candidatos = []
    try:
        html = bajar(base).decode("utf-8", "ignore")
        for tag in re.findall(r"<link\b[^>]*>", html, re.I):
            rel = re.search(r'rel\s*=\s*["\']([^"\']+)', tag, re.I)
            href = re.search(r'href\s*=\s*["\']([^"\']+)', tag, re.I)
            if not rel or not href or "icon" not in rel.group(1).lower():
                continue
            ruta = href.group(1)
            if ruta.lower().endswith(".svg"):
                continue
            medida = re.search(r'sizes\s*=\s*["\'](\d+)', tag, re.I)
            peso = int(medida.group(1)) if medida else (
                180 if "apple" in rel.group(1).lower() else 32)
            candidatos.append((peso, urljoin(base, ruta)))
    except Exception as e:
        print(f"    (no se pudo leer el HTML de {sitio['nombre']}: {e})")

    candidatos.append((0, urljoin(base, "/favicon.ico")))
    candidatos.sort(key=lambda c: -c[0])

    vistas = set()
    for _, url in candidatos:
        if url in vistas:
            continue
        vistas.add(url)
        try:
            im = Image.open(BytesIO(bajar(url)))
            # Un .ico trae varios tamaños; PIL abre el mayor si se lo pide.
            if getattr(im, "format", "") == "ICO":
                mayor = max(im.ico.sizes())
                im = im.ico.getimage(mayor)
            im = im.convert("RGBA")
            if min(im.size) < 16:
                continue
            im.thumbnail((256, 256), Image.LANCZOS)
            im.save(destino)
            print(f"    logo {sitio['nombre']}: {im.size[0]}×{im.size[1]}  ←  {url}")
            return f"./contenido/logos/{sitio['slug']}.png"
        except Exception:
            continue

    print(f"    logo {sitio['nombre']}: NO SE ENCONTRÓ, va la inicial")
    return None


def webs():
    print("· Capturas de los sitios")
    salida = []
    for sitio in SITIOS:
        png = CONTENIDO / "capturas" / f"{sitio['slug']}.png"
        jpg = CONTENIDO / "capturas" / f"{sitio['slug']}.jpg"
        capturar(sitio["captura_url"], png)
        guardar_imagen(png, jpg, 1120, 700, calidad=84, recorte=True)
        png.unlink()
        salida.append({
            "titulo": sitio["nombre"],
            "tipo": sitio["tipo"],
            "fecha": sitio["fecha"],
            "descripcion": sitio["descripcion"],
            "url": sitio["url"],
            "captura": f"./contenido/capturas/{sitio['slug']}.jpg",
            "logo": logo(sitio),
            "color": acento(jpg),
        })
        print(f"  {sitio['nombre']}")
    return salida


def musica():
    print("· AOTY")
    for artista, album, _ in AOTY_FAVORITOS:
        print(f"  {artista} — {album}")
    return {
        "usuario": "InakiHDF",
        "perfil": AOTY_PERFIL,
        "ratings": AOTY_RATINGS,
        "enlaces": [
            {"etiqueta": "Ratings", "url": AOTY_PERFIL + "ratings/"},
            {"etiqueta": "Mejor de 2026", "url": AOTY_PERFIL + "ratings/highest/?y=2026"},
        ],
        "favoritos": [
            {"artista": a, "album": d, "url": "https://www.albumoftheyear.org" + r}
            for a, d, r in AOTY_FAVORITOS
        ],
    }


CABECERA = '''/**
 * CONTENIDO — GENERADO, NO EDITAR A MANO
 * ======================================
 *
 * Lo escribe `tools/fetch_contenido.py`. Para actualizarlo:
 *
 *     python3 tools/fetch_contenido.py
 *
 * Las URLs de los sitios, el video y los favoritos de AOTY se configuran
 * arriba de ese script. Los artículos salen solos del archivo de Substack.
 *
 * Generado: %s
 */

export const CONTENIDO = %s;
'''


def videos():
    """Los videos, con la miniatura que eligió Iñaki verificada.

    Si el archivo no está, se aborta. Una miniatura rota deja la tela del
    proyector con un marco vacío y nadie se entera hasta abrir la página.
    """
    for v in VIDEOS:
        for clave in ("archivo", "poster"):
            ruta = WEB / v[clave].lstrip("./")
            if not ruta.exists():
                raise RuntimeError(
                    f"«{v['titulo']}»: falta {clave} en {ruta.relative_to(RAIZ)}. "
                    f"Poné el archivo o cambiá la ruta en VIDEOS, arriba de este script."
                )
        print(f"  video  {v['titulo']}  ·  miniatura {Path(v['poster']).name}")
    return VIDEOS


def main():
    CONTENIDO.mkdir(parents=True, exist_ok=True)
    datos = {
        "web": webs(),
        "video": videos(),
        "texto": textos(),
        "musica": musica(),
    }
    destino = WEB / "contenido.js"
    destino.write_text(
        CABECERA % (datetime.now().strftime("%Y-%m-%d %H:%M"),
                    json.dumps(datos, ensure_ascii=False, indent=2)),
        encoding="utf-8",
    )
    print(f"\n→ {destino.relative_to(RAIZ)}  "
          f"({len(datos['web'])} sitios · {len(datos['video'])} video · "
          f"{len(datos['texto'])} textos · {len(datos['musica']['favoritos'])} discos)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nABORTADO sin tocar contenido.js: {e}", file=sys.stderr)
        raise SystemExit(1)
