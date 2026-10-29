"""IDs like PRJ-2026-00042-K: prefix, year, counter and a Luhn mod-N check character.

The Crockford base32 alphabet (no I, L, O, U) avoids confusion when IDs are handwritten or read aloud.
The check character catches all single-character errors and most adjacent transpositions.
"""
import datetime
import html
import json
import os
import re
import secrets

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_N = len(ALPHABET)
_NORMALIZE = str.maketrans({"O": "0", "I": "1", "L": "1", "U": "V"})


def _clean(s):
    return re.sub(r"[^0-9A-Z]", "", s.upper().translate(_NORMALIZE))


def check_char(payload):
    """Luhn mod N check character over the alphanumeric characters of payload."""
    factor, total = 2, 0
    for ch in reversed(_clean(payload)):
        code = ALPHABET.index(ch) * factor
        factor = 1 if factor == 2 else 2
        total += code // _N + code % _N
    return ALPHABET[(_N - total % _N) % _N]


def make_id(prefix, number, year=None, width=5, sep="-"):
    parts = [prefix.upper()] + ([str(year)] if year else []) + [str(number).zfill(width)]
    body = sep.join(parts)
    return body + sep + check_char(body)


def validate_id(sample_id):
    """True if the last character is the correct check character (separators/case ignored)."""
    s = _clean(sample_id)
    if len(s) < 2:
        return False
    return check_char(s[:-1]) == s[-1]


class IdGenerator:
    """Sequential (per prefix and year) or random IDs, with state kept in a JSON file so numbers never repeat."""

    def __init__(self, state_path="sample_ids.json", today=None):
        self.state_path = state_path
        self.today = today or datetime.date.today()
        self.state = {"counters": {}, "issued": []}
        if os.path.exists(state_path):
            with open(state_path, encoding="utf-8") as fh:
                self.state = json.load(fh)

    def _save(self):
        with open(self.state_path, "w", encoding="utf-8") as fh:
            json.dump(self.state, fh, indent=1)

    def sequential(self, prefix, n=1, with_year=True, width=5):
        key = "%s-%s" % (prefix.upper(), self.today.year if with_year else "")
        start = self.state["counters"].get(key, 0)
        ids = [make_id(prefix, start + i + 1, self.today.year if with_year else None, width) for i in range(n)]
        self.state["counters"][key] = start + n
        self.state["issued"] += ids
        self._save()
        return ids

    def random(self, prefix, n=1, length=6):
        """Non-sequential IDs (useful for blinding: the ID reveals nothing about order or group)."""
        issued = set(self.state["issued"])
        out = []
        while len(out) < n:
            body = "%s-%s" % (prefix.upper(), "".join(secrets.choice(ALPHABET) for _ in range(length)))
            sid = body + "-" + check_char(body)
            if sid not in issued:
                issued.add(sid)
                out.append(sid)
        self.state["issued"] += out
        self._save()
        return out


def label_sheet_html(ids, columns=4, extra=None, title="Sample labels"):
    """Printable HTML grid of labels (e.g. for adhesive label sheets); extra: dict id -> second line."""
    cells = []
    for sid in ids:
        sub = html.escape((extra or {}).get(sid, ""))
        cells.append("<div class='l'><b>%s</b>%s</div>" % (html.escape(sid), "<br><small>%s</small>" % sub if sub else ""))
    return ("<!doctype html><html><head><meta charset='utf-8'><title>%s</title><style>"
            "@page{margin:10mm}body{font-family:monospace;margin:0}.g{display:grid;grid-template-columns:repeat(%d,1fr);"
            "gap:2mm}.l{border:1px dashed #999;padding:3mm;font-size:11pt;text-align:center;height:16mm;"
            "break-inside:avoid}</style></head><body><div class='g'>%s</div></body></html>\n") % (
        html.escape(title), columns, "".join(cells))
