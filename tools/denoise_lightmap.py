"""Limpia ruido impulsivo del bake antes del filtrado lineal del navegador."""

import argparse
from PIL import Image, ImageFilter


parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("output")
parser.add_argument("--median", type=int, default=3, choices=(3, 5))
parser.add_argument("--blur", type=float, default=0.35)
args = parser.parse_args()

image = Image.open(args.source).convert("RGB")
clean = image.filter(ImageFilter.MedianFilter(args.median))
if args.blur:
    clean = clean.filter(ImageFilter.GaussianBlur(args.blur))
clean.save(args.output, optimize=True)

print(f"lightmap limpio: {args.output} ({args.median}x{args.median}, blur {args.blur})")
