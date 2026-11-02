"""Turn the supplied monogram (white background) into transparent web images."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Pixels this close to white become fully transparent (removes JPEG/AI noise).
NOISE_FLOOR = 0.035


class Command(BaseCommand):
    help = (
        "Remove the white background from the monogram and write static/img/monogram.png, "
        "monogram-sm.png (+ WebP) and og-image.jpg."
    )

    def add_arguments(self, parser):
        parser.add_argument("--source", default=str(settings.BASE_DIR / "assets/our_monogram.png"))
        parser.add_argument("--out", default=str(settings.BASE_DIR / "static/img"))

    def handle(self, *args, source, out, **options):
        import numpy as np
        from PIL import Image

        source, out = Path(source), Path(out)
        if not source.exists():
            raise CommandError(f"Monogram not found: {source}")
        out.mkdir(parents=True, exist_ok=True)

        rgb = np.asarray(Image.open(source).convert("RGB"), dtype=np.float64) / 255.0
        # "Colour to alpha" against white: the most opaque version of each pixel that
        # still looks identical when placed on white. Watercolour edges stay soft.
        alpha = (1.0 - rgb).max(axis=2)
        alpha = np.clip((alpha - NOISE_FLOOR) / (1.0 - NOISE_FLOOR), 0.0, 1.0)
        safe = np.where(alpha > 0, alpha, 1.0)[..., None]
        colour = np.clip(1.0 - (1.0 - rgb) / safe, 0.0, 1.0)
        rgba = np.dstack([colour, alpha]) * 255.0
        image = Image.fromarray(rgba.round().astype(np.uint8), "RGBA")
        image = image.crop(image.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())

        def save(img, size, name):
            img = img.copy()
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            path = out / name
            img.save(path, optimize=True)
            img.save(path.with_suffix(".webp"), quality=86, method=6)
            self.stdout.write(f"Wrote {path} {img.size} {path.stat().st_size // 1024} KB")

        save(image, 600, "monogram.png")
        save(image, 200, "monogram-sm.png")

        # Open Graph preview: opaque, 1200x630, on the page's paper colour.
        og = Image.new("RGB", (1200, 630), (255, 253, 253))
        mark = image.copy()
        mark.thumbnail((520, 520), Image.Resampling.LANCZOS)
        og.paste(mark, ((1200 - mark.width) // 2, (630 - mark.height) // 2), mark)
        og.save(out / "og-image.jpg", quality=85, optimize=True)
        self.stdout.write(f"Wrote {out / 'og-image.jpg'}")
