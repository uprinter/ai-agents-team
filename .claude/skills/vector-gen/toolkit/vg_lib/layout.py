"""Shared layout helpers for the infographic forms."""


def wrap(c, text, size, maxw, bold=False):
    """Word wrap with balanced lines: the width shrinks while the line count stays the same, so no line
    ends on a lone word. A single word wider than maxw is an error, not a silent overflow."""
    lines = _greedy(c, text, size, maxw, bold, strict=True)
    if len(lines) > 1:
        w = maxw
        while w > 20:
            trial = _greedy(c, text, size, w - 2, bold)
            if trial is None or len(trial) != len(lines):
                break
            w, lines = w - 2, trial
    return lines


def _greedy(c, text, size, maxw, bold, strict=False):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if c.tw(trial, size, bold) <= maxw:
            cur = trial
        elif not cur:
            return _fail(c, word, maxw, size) if strict else None
        else:
            lines.append(cur)
            cur = word
            if c.tw(cur, size, bold) > maxw:
                return _fail(c, word, maxw, size) if strict else None
    return lines + [cur] if cur else lines


def line_height(size):
    return round(size * 1.3)


def baseline(top, size):
    """Baseline of a line whose line box starts at top."""
    return top + size * 0.95


def _fail(c, word, maxw, size):
    raise ValueError(f"word '{word}' does not fit {maxw:.0f}px at {size}px in variant {c.vname}; shorten it")
