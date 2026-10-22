"""Token loading: default.json deep-merged with an optional project override."""
import json, pathlib

DEFAULT = pathlib.Path(__file__).resolve().parent.parent / "tokens" / "default.json"


def _merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load(override=None):
    tok = json.loads(DEFAULT.read_text())
    if override:
        _merge(tok, json.loads(pathlib.Path(override).read_text()))
    return tok


# role names in the dataviz "Chart chrome & ink" table -> figure colour tokens
ROLES = {"page plane": "bg", "chart surface": "surface", "primary ink": "ink", "secondary ink": "muted", "baseline": "hair"}
SANS = {
    "family": "system-ui, -apple-system, 'Segoe UI', sans-serif",
    "regular": ["/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}


def from_palette(path, mode="dark", font=None):
    """A token override from a dataviz-style palette file, so charts and diagrams share one palette.
    The file holds two markdown tables: the categorical hues (| slot | hue | light | dark |) and the chrome and ink roles
    (| role | light | dark |). Slot 1 becomes the accent. font="sans" also sets the system sans the dataviz method uses."""
    import re
    text = pathlib.Path(path).read_text()
    col = 1 if mode == "light" else 2
    hexc = r"`(#[0-9a-fA-F]{6})`"
    colors = {}
    for m in re.finditer(r"^\|\s*([A-Za-z][^|]*?)\s*\|\s*" + hexc + r"\s*\|\s*" + hexc + r"\s*\|", text, re.M):
        role = m.group(1).lower()
        for key, tok in ROLES.items():
            if role.startswith(key):
                colors[tok] = m.group(1 + col)
    slot = re.search(r"^\|\s*1\s*\|[^|]*\|\s*" + hexc + r"\s*\|\s*" + hexc + r"\s*\|", text, re.M)
    if slot:
        colors["accent"] = slot.group(col)
    missing = [t for t in ("bg", "surface", "ink", "muted", "hair", "accent") if t not in colors]
    if missing:
        raise ValueError(f"{path}: no value for {', '.join(missing)}; the file needs a 'Chart chrome & ink' table with the rows "
                         f"{', '.join(ROLES)} and a categorical table whose slot 1 is the accent")
    out = {"colors": colors}
    if font == "sans":
        out["font"] = {**SANS, "value": {"family": SANS["family"], "bold": SANS["bold"]}}
    return out
