"""Text measurement with the real font file; fails loudly when no font is found."""
import os
from functools import lru_cache
from PIL import ImageFont


@lru_cache(maxsize=None)
def _font(paths, size8):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size8)
    raise FileNotFoundError(f"no font file found in {paths}; set font.regular/bold in the token override")


def text_width(tok, text, size, bold, safety, face=None):
    """face="value" measures the figure font used for big numbers (lining digits; Georgia has old-style ones)."""
    paths = tuple(tok["font"]["value"]["bold"] if face == "value" else tok["font"]["bold" if bold else "regular"])
    return _font(paths, int(size * 8)).getlength(text) / 8 * safety
