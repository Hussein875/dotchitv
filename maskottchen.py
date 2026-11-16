"""Dotchi – das Maskottchen des Kanals: eine goldene Münze mit Gesicht.

Die Münze fiebert mit (staunt bei großen Zahlen), fällt das Urteil (Münzwurf → zeigt auf die bessere Wahl)
und winkt am Ende Richtung Kommentare. Alles ist mit Pillow gezeichnet – wie die Figuren in figuren.py:
gleicher Stil in jedem Bild, keine Kosten, keine fremden Bilder.

    bild = zeichne("staunt", t)        # RGBA, die Münzmitte ist die Bildmitte
    bild = wurf(p)                     # Münze im Flug (p = 0…1), landet mit dem Gesicht nach vorn

Stimmungen: normal, denkt, freut, staunt, genervt, zwinkert, traurig.
Posen ergeben sich aus der Stimmung; mit `zeigt="links"/"rechts"` zeigt ein Arm zur Seite, mit `winkt=True`
winkt der rechte Arm.
"""

import math

from PIL import Image, ImageDraw

S = 2                      # alles doppelt zeichnen und verkleinern = glatte Kanten
BREITE, HOEHE = 440, 520   # Zeichenfläche bei Größe 1.0
MX, MY, R = 220, 260, 128  # Münzmitte und Radius

GOLD, GOLD_RAND, GOLD_TIEF = (255, 200, 61), (233, 163, 22), (176, 116, 10)
GLIED = (214, 150, 22)
DUNKEL = (74, 44, 8)
SCHUH = (255, 77, 109)

# Stimmung → (Augen, Blick, Brauen-Neigung, Brauen-Höhe, Mund, Arm links, Arm rechts)
# Arme: Winkel in Grad, 0 = hängt herunter, 90 = waagerecht nach außen, 180 = senkrecht nach oben
STIMMUNGEN = {
    "normal":   ("offen", (0, 0), 0, 0, "laecheln", 24, 24),
    "denkt":    ("offen", (7, -9), -10, 6, "schief", 24, "kinn"),
    "freut":    ("froh", (0, 0), 0, 4, "offen", 150, 150),
    "staunt":   ("weit", (0, 0), 0, 12, "o", 104, 104),
    "genervt":  ("halb", (9, 0), 9, -6, "flach", 12, 12),
    "zwinkert": ("zwinker", (0, 0), 0, 3, "grinsen", 24, 24),
    "traurig":  ("offen", (0, 6), -14, 0, "traurig", 12, 12),
}


def _p(x, y):
    return x * S, y * S


def _kreis(d, x, y, r, **kw):
    d.ellipse((x * S - r * S, y * S - r * S, x * S + r * S, y * S + r * S), **kw)


def _oval(d, x, y, rx, ry, **kw):
    d.ellipse((x * S - rx * S, y * S - ry * S, x * S + rx * S, y * S + ry * S), **kw)


def _linie(d, punkte, farbe, breite):
    d.line([_p(*p) for p in punkte], fill=farbe, width=round(breite * S), joint="curve")
    for x, y in (punkte[0], punkte[-1]):  # runde Enden
        _kreis(d, x, y, breite / 2, fill=farbe)


def _arm(d, seite, winkel, laenge=84):
    """Arm von der Schulter aus; `seite` = -1 (links) oder +1 (rechts). Rückgabe: Handposition."""
    sx, sy = MX + seite * (R - 12), MY + 34
    bogen = math.radians(winkel)
    hx, hy = sx + seite * laenge * math.sin(bogen), sy + laenge * math.cos(bogen)
    _linie(d, [(sx, sy), (hx, hy)], GLIED, 17)
    return hx, hy


def _hand(d, x, y):
    _kreis(d, x, y, 21, fill=GOLD_TIEF)
    _kreis(d, x, y, 18, fill=(255, 255, 255))


def _muenze(d):
    _kreis(d, MX, MY + 10, R, fill=GOLD_TIEF)            # Dicke der Münze
    _kreis(d, MX, MY, R, fill=GOLD_RAND)
    _kreis(d, MX, MY, R - 12, fill=GOLD)
    _kreis(d, MX, MY, R - 24, outline=GOLD_RAND, width=4 * S)


def _glanz(bild):
    """Lichtkante oben links – auf eigener Ebene, damit sie halb durchsichtig bleibt."""
    glanz = Image.new("RGBA", bild.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glanz)
    r = R - 36
    g.arc((MX * S - r * S, MY * S - r * S, MX * S + r * S, MY * S + r * S), 198, 262,
          fill=(255, 255, 255, 120), width=9 * S)
    bild.alpha_composite(glanz)


def _auge(d, x, y, art, blick, zu=False):
    if zu:
        _linie(d, [(x - 22, y + 4), (x + 22, y + 4)], DUNKEL, 8)
        return
    if art in ("froh", "zwinker_zu"):                      # lachendes Auge: Bogen nach oben
        d.arc((x * S - 26 * S, y * S - 16 * S, x * S + 26 * S, y * S + 36 * S), 205, 335, fill=DUNKEL,
              width=9 * S)
        return
    rx, ry = (34, 44) if art == "weit" else (30, 38)
    _oval(d, x, y, rx + 3, ry + 3, fill=GOLD_RAND)
    _oval(d, x, y, rx, ry, fill=(255, 255, 255))
    px, py = (11, 14) if art == "weit" else (15, 19)
    bx, by = blick
    _oval(d, x + bx, y + by + (6 if art == "halb" else 0), px, py, fill=(30, 26, 22))
    _kreis(d, x + bx - 5, y + by - 6 + (6 if art == "halb" else 0), 5, fill=(255, 255, 255))
    if art == "halb":                                       # schweres Augenlid
        d.chord((x * S - (rx + 3) * S, y * S - (ry + 3) * S, x * S + (rx + 3) * S, y * S + (ry + 3) * S),
                180, 360, fill=GOLD)
        _linie(d, [(x - rx - 2, y), (x + rx + 2, y)], DUNKEL, 7)


def _mund(d, art):
    x, y = MX, MY + 66
    if art == "offen":
        d.chord((x * S - 44 * S, y * S - 42 * S, x * S + 44 * S, y * S + 30 * S), 0, 180, fill=(140, 36, 48))
        d.chord((x * S - 26 * S, y * S + 2 * S, x * S + 26 * S, y * S + 34 * S), 0, 180, fill=(255, 128, 140))
    elif art == "o":
        _oval(d, x, y + 4, 19, 25, fill=(120, 30, 42))
    elif art == "flach":
        _linie(d, [(x - 26, y), (x + 26, y)], DUNKEL, 8)
    elif art == "schief":
        _linie(d, [(x - 4, y + 2), (x + 30, y - 6)], DUNKEL, 8)
    elif art == "traurig":
        d.arc((x * S - 34 * S, y * S - 4 * S, x * S + 34 * S, y * S + 40 * S), 205, 335, fill=DUNKEL, width=8 * S)
    elif art == "grinsen":
        d.arc((x * S - 40 * S, y * S - 40 * S, x * S + 40 * S, y * S + 14 * S), 15, 150, fill=DUNKEL, width=9 * S)
    else:  # laecheln
        d.arc((x * S - 36 * S, y * S - 34 * S, x * S + 36 * S, y * S + 12 * S), 20, 160, fill=DUNKEL, width=8 * S)


def zeichne(stimmung="normal", t=0.0, groesse=1.0, zeigt=None, winkt=False, blick=None, quetschen=0.0):
    """Das Maskottchen als RGBA-Bild; die Münzmitte liegt in der Bildmitte.

    `t` (Sekunden) bewegt Arme und lässt die Augen blinzeln, `quetschen` (0…1) staucht die Münze kurz –
    für die Landung nach einem Sprung."""
    augen, blick_std, neigung, brauen_hoch, mund, arm_l, arm_r = STIMMUNGEN.get(stimmung, STIMMUNGEN["normal"])
    blick = blick if blick is not None else blick_std
    bild = Image.new("RGBA", (BREITE * S, HOEHE * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    wippen = math.sin(t * 2.4) * 3
    if stimmung == "freut":                                 # jubelnde Arme
        arm_l, arm_r = 150 + math.sin(t * 9) * 12, 150 - math.sin(t * 9) * 12
    if zeigt == "links":                                    # der andere Arm bleibt, wie die Stimmung ihn hält
        arm_l, arm_r = 96, 24 if arm_r == "kinn" else arm_r
    elif zeigt == "rechts":
        arm_r = 96
    if winkt:
        arm_r = 142 + math.sin(t * 9) * 20

    # Beine und Schuhe (hinter der Münze)
    for seite in (-1, 1):
        x = MX + seite * 44
        _linie(d, [(x, MY + R - 20), (x, MY + R + 56)], GLIED, 17)
        _oval(d, x + seite * 8, MY + R + 62, 30, 15, fill=SCHUH)
        _oval(d, x + seite * 14, MY + R + 56, 9, 4, fill=(255, 170, 185))
    # Arme hinter der Münze
    haende = []
    for seite, winkel in ((-1, arm_l), (1, arm_r)):
        if winkel == "kinn":
            continue
        haende.append(_arm(d, seite, winkel + (wippen if winkel < 60 else 0)))
    _muenze(d)
    _glanz(bild)
    d = ImageDraw.Draw(bild)
    for hx, hy in haende:
        _hand(d, hx, hy)

    # Gesicht
    blinzeln = augen in ("offen", "weit") and ((t + 1.2) % 3.3) < 0.13   # nicht im ersten Bild (= Vorschaubild)
    for seite in (-1, 1):
        x, y = MX + seite * 46, MY - 16
        art = augen
        if augen == "zwinker":
            art = "zwinker_zu" if seite == 1 else "offen"
        _auge(d, x, y, art, blick, zu=blinzeln)
        if art not in ("froh", "zwinker_zu") or augen == "zwinker":
            hoch = y - (64 if augen == "weit" else 56) - brauen_hoch
            kipp = neigung * seite
            if augen == "halb":
                hoch, kipp = y - 34, 7 * seite
            _linie(d, [(x - 24, hoch + kipp), (x + 24, hoch - kipp)], DUNKEL, 9)
    _mund(d, mund)
    if stimmung in ("freut", "zwinkert"):
        for seite in (-1, 1):
            _oval(d, MX + seite * 84, MY + 44, 17, 10, fill=(255, 150, 120))
    if stimmung == "staunt":                                # Schweißtropfen
        tx, ty = MX + 92, MY - 92
        d.polygon([_p(tx, ty - 22), _p(tx - 12, ty + 2), _p(tx + 12, ty + 2)], fill=(140, 215, 255))
        _kreis(d, tx, ty + 4, 12, fill=(140, 215, 255))
    if arm_r == "kinn":                                     # Hand am Kinn – vor der Münze
        _linie(d, [(MX + R - 12, MY + 34), (MX + 126, MY + 122), (MX + 66, MY + 104)], GLIED, 17)
        _hand(d, MX + 62, MY + 102)

    b, h = round(BREITE * groesse), round(HOEHE * groesse)
    bild = bild.resize((b, h), Image.LANCZOS)
    if quetschen > 0:                                       # breiter und flacher, Füße bleiben am Boden
        qb, qh = round(b * (1 + 0.10 * quetschen)), round(h * (1 - 0.14 * quetschen))
        gestaucht = bild.resize((qb, qh), Image.BILINEAR)
        bild = Image.new("RGBA", (qb, h), (0, 0, 0, 0))
        bild.alpha_composite(gestaucht, (0, h - qh))
    return bild


def wurf(p, groesse=1.0, umdrehungen=1.5):
    """Münzwurf: Die Münze dreht sich um die senkrechte Achse und landet (p = 1) mit dem Gesicht nach vorn."""
    p = min(1.0, max(0.0, p))
    winkel = (1 - p) ** 2 * umdrehungen * 2 * math.pi   # dreht anfangs schnell, wird langsamer
    vorn = math.cos(winkel) >= 0
    bild = Image.new("RGBA", (BREITE * S, HOEHE * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    _muenze(d)
    _glanz(bild)
    d = ImageDraw.Draw(bild)
    if vorn:
        for seite in (-1, 1):
            _auge(d, MX + seite * 46, MY - 16, "weit", (0, 0))
        _mund(d, "o")
    else:  # Rückseite: großes Fragezeichen
        from renderer import FETT
        from text import schrift
        d.text(_p(MX, MY + 6), "?", font=schrift(FETT, 150 * S), fill=GOLD_RAND, anchor="mm")
    b, h = round(BREITE * groesse), round(HOEHE * groesse)
    bild = bild.resize((b, h), Image.LANCZOS)
    schmal = max(0.08, abs(math.cos(winkel)))
    if schmal < 0.999:
        gedreht = bild.resize((max(2, round(b * schmal)), h), Image.BILINEAR)
        bild = Image.new("RGBA", (b, h), (0, 0, 0, 0))
        bild.alpha_composite(gedreht, ((b - gedreht.width) // 2, 0))
    return bild
