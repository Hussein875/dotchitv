"""Gezeichnete Geschichten-Szenen für Dotchi: flache Figuren, einfache Orte, Emojis als Gegenstände.

Eine Szene vom Typ `bild` zeigt einen Ort (`ort`), eine oder zwei Figuren (`figuren`) und oben den gesprochenen
Satz als Untertitel (`text`). Die Figuren selbst stehen einmal pro Video unter `figuren` im Eintrag:

    "figuren": {"max": {"haut": "#F2C9A0", "haare": "#5A3A22", "frisur": "kurz", "shirt": "#FF9F43",
                        "hose": "#3B4252"}}

und in der Szene: {"wer": "max", "x": 0.3, "stimmung": "freut", "pose": "haelt", "haelt": "☕"}.
Stimmungen: normal, freut, traurig, staunt. Posen: steht, haelt, winkt, jubelt. Alles wird mit Pillow gezeichnet –
gleicher Stil in jedem Bild, keine Kosten, keine fremden Bilder.
"""

import math
from functools import lru_cache

from PIL import Image, ImageDraw

from text import clamp, ease_out, einfuegen, hex_zu_rgb

B, H = 1080, 1920
OBEN, UNTEN = 300, 1420          # Bühne zwischen Marke (oben) und Fußzeile (unten)
BODEN = 1360                     # Fußhöhe der Figuren
S = 2                            # alles doppelt zeichnen und verkleinern = glatte Kanten


def rgb(farbe):
    return hex_zu_rgb(farbe) if isinstance(farbe, str) else tuple(farbe)


def dunkler(farbe, faktor=0.75):
    return tuple(int(c * faktor) for c in rgb(farbe))


# ---------------------------------------------------------------- Orte

def _verlauf(d, box, oben, unten):
    x0, y0, x1, y1 = box
    oben, unten = rgb(oben), rgb(unten)
    for y in range(y0, y1):
        p = (y - y0) / max(1, y1 - y0 - 1)
        d.line((x0, y, x1, y), fill=tuple(int(a + (b - a) * p) for a, b in zip(oben, unten)))


def _fenster(d, box, himmel=("#8FD3FF", "#CDEFFF"), mond=False):
    x0, y0, x1, y1 = box
    _verlauf(d, box, *himmel)
    if mond:
        d.ellipse((x1 - 150, y0 + 50, x1 - 70, y0 + 130), fill=(245, 240, 210))
    d.rectangle(box, outline=(240, 235, 225), width=18)
    d.line(((x0 + x1) // 2, y0, (x0 + x1) // 2, y1), fill=(240, 235, 225), width=12)
    d.line((x0, (y0 + y1) // 2, x1, (y0 + y1) // 2), fill=(240, 235, 225), width=12)


def zeichne_ort(ort):
    """Hintergrund der Bühne (B x Bühnenhöhe), einmal pro Ort gezeichnet."""
    h = UNTEN - OBEN
    bild = Image.new("RGB", (B, h))
    d = ImageDraw.Draw(bild)
    boden = BODEN - OBEN - 40
    if ort == "strasse":
        _verlauf(d, (0, 0, B, boden), "#6EC6FF", "#BDE8FF")
        for i, (x, w, hh, f) in enumerate([(-40, 300, 520, "#E07A5F"), (250, 260, 640, "#F2CC8F"),
                                           (500, 320, 470, "#81B29A"), (810, 300, 600, "#3D5A80")]):
            d.rectangle((x, boden - hh, x + w, boden), fill=f)
            for fy in range(boden - hh + 50, boden - 90, 110):
                for fx in range(x + 40, x + w - 60, 90):
                    d.rectangle((fx, fy, fx + 50, fy + 60), fill=(255, 244, 214) if (fx + fy + i) % 3 else (70, 80, 100))
        d.rectangle((0, boden, B, h), fill=(150, 150, 160))
        d.rectangle((0, boden, B, boden + 18), fill=(190, 190, 198))
    elif ort == "cafe":
        _verlauf(d, (0, 0, B, boden), "#8C5A3C", "#6B4029")
        d.rounded_rectangle((330, 330, 750, 460), 30, fill=(40, 26, 18))
        d.text((540, 395), "CAFÉ", fill=(255, 200, 61), anchor="mm", font=_schrift(90))
        for x in range(60, B, 240):
            d.rectangle((x, 560, x + 150, 575), fill=(60, 38, 26))
        d.rectangle((0, boden - 330, B, boden - 300), fill=(210, 180, 140))
        d.rectangle((0, boden - 300, B, boden), fill=(120, 72, 44))
        d.rectangle((0, boden, B, h), fill=(70, 44, 30))
    elif ort == "zimmer":
        _verlauf(d, (0, 0, B, boden), "#F4E3C1", "#E9CFA0")
        _fenster(d, (640, 300, 960, 640))
        d.rounded_rectangle((60, boden - 260, 460, boden - 40), 40, fill=(129, 178, 154))
        d.rounded_rectangle((40, boden - 330, 480, boden - 210), 40, fill=(100, 150, 128))
        d.rectangle((0, boden, B, h), fill=(176, 122, 80))
        for x in range(0, B, 180):
            d.line((x, boden, x, h), fill=(150, 100, 64), width=6)
    elif ort == "abend":
        _verlauf(d, (0, 0, B, boden), "#2B2D5C", "#3E3A6E")
        _fenster(d, (640, 300, 960, 640), himmel=("#0B1030", "#232A5C"), mond=True)
        d.line((200, 0, 200, 340), fill=(30, 30, 40), width=6)  # Hängelampe
        d.chord((110, 320, 290, 460), 180, 360, fill=(255, 214, 120))
        d.rectangle((0, boden, B, h), fill=(60, 50, 90))
    elif ort == "kueche":
        _verlauf(d, (0, 0, B, boden), "#E8F1F2", "#D3E4E6")
        for y in range(0, boden - 300, 90):
            for x in range(0 if (y // 90) % 2 else 45, B, 90):
                d.rectangle((x, y, x + 84, y + 84), outline=(200, 214, 218), width=4)
        d.rectangle((0, boden - 300, B, boden - 270), fill=(90, 96, 110))
        d.rectangle((0, boden - 270, B, boden), fill=(240, 240, 244))
        d.rectangle((0, boden, B, h), fill=(150, 160, 170))
    else:  # neutral
        _verlauf(d, (0, 0, B, boden), "#2A2C38", "#1C1D26")
        d.rectangle((0, boden, B, h), fill=(40, 42, 54))
    # oben abdunkeln, damit der Untertitel immer lesbar ist
    dunkel = Image.new("RGBA", (B, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dunkel)
    for y in range(0, 360):
        dd.line((0, y, B, y), fill=(10, 10, 14, int(200 * (1 - y / 360) ** 1.4)))
    bild = Image.alpha_composite(bild.convert("RGBA"), dunkel)
    maske = Image.new("L", (B, h), 0)
    ImageDraw.Draw(maske).rounded_rectangle((24, 0, B - 25, h - 1), 48, fill=255)
    bild.putalpha(maske)
    return bild


@lru_cache(maxsize=None)
def _schrift(groesse):
    from renderer import FETT
    from text import schrift
    return schrift(FETT, groesse)


@lru_cache(maxsize=None)
def ort_ebene(ort):
    return zeichne_ort(ort)


# ---------------------------------------------------------------- Figuren

def _arm(d, schulter, winkel, laenge, farbe, dicke):
    x, y = schulter
    hx = x + laenge * math.sin(math.radians(winkel))
    hy = y + laenge * math.cos(math.radians(winkel))
    d.line((x, y, hx, hy), fill=farbe, width=dicke)
    d.ellipse((hx - dicke / 2, hy - dicke / 2, hx + dicke / 2, hy + dicke / 2), fill=farbe)
    return hx, hy


def zeichne_figur(f, stimmung="normal", pose="steht", t=0.0, blinzeln=False):
    """Eine Figur als RGBA-Bild (Füße unten mittig). Rückgabe: (Bild, Handposition für Gegenstände)."""
    w, h = 360 * S, 640 * S
    bild = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    haut, haare = rgb(f.get("haut", "#F2C9A0")), rgb(f.get("haare", "#3B2A1E"))
    shirt, hose = rgb(f.get("shirt", "#4FC3F7")), rgb(f.get("hose", "#3B4252"))
    mx = w // 2
    # Beine und Schuhe
    for dx in (-38, 38):
        d.rounded_rectangle((mx + dx * S - 26 * S, 430 * S, mx + dx * S + 26 * S, 610 * S), 20 * S, fill=hose)
        d.ellipse((mx + dx * S - 40 * S, 592 * S, mx + dx * S + 44 * S, 632 * S), fill=(40, 40, 48))
    # Körper
    d.rounded_rectangle((mx - 92 * S, 250 * S, mx + 92 * S, 470 * S), 60 * S, fill=shirt)
    d.rounded_rectangle((mx - 92 * S, 250 * S, mx + 92 * S, 300 * S), 40 * S, fill=dunkler(shirt, 0.9))
    # Arme
    dicke = 44 * S
    wippen = math.sin(t * 2.2) * 4
    links, rechts = (mx - 86 * S, 290 * S), (mx + 86 * S, 290 * S)
    if pose == "jubelt":
        wl, wr = 155 + math.sin(t * 8) * 8, -155 - math.sin(t * 8) * 8
    elif pose == "winkt":
        wl, wr = 12 + wippen, -150 + math.sin(t * 9) * 18
    elif pose == "haelt":  # Gegenstand vor dem Bauch, nicht vor dem Gesicht
        wl, wr = 12 + wippen, -52
    else:
        wl, wr = 12 + wippen, -12 - wippen
    _arm(d, links, wl, 150 * S, shirt, dicke)
    hand = _arm(d, rechts, wr, 150 * S if pose != "haelt" else 120 * S, shirt, dicke)
    for (hx, hy) in [_arm(d, links, wl, 150 * S, shirt, dicke), hand]:
        d.ellipse((hx - 22 * S, hy - 22 * S, hx + 22 * S, hy + 22 * S), fill=haut)
    # Kopf
    kx, ky, r = mx, 150 * S, 112 * S
    d.rectangle((mx - 24 * S, 230 * S, mx + 24 * S, 265 * S), fill=dunkler(haut, 0.9))
    d.ellipse((kx - r, ky - r, kx + r, ky + r), fill=haut)
    frisur = f.get("frisur", "kurz")
    if frisur == "kurz":
        d.chord((kx - r - 4 * S, ky - r - 10 * S, kx + r + 4 * S, ky + r - 40 * S), 180, 360, fill=haare)
    elif frisur == "locken":
        for a in range(200, 345, 22):
            ax = kx + (r - 6 * S) * math.cos(math.radians(a))
            ay = ky - 6 * S + (r - 6 * S) * math.sin(math.radians(a))
            d.ellipse((ax - 40 * S, ay - 40 * S, ax + 40 * S, ay + 40 * S), fill=haare)
    elif frisur == "seite":
        d.chord((kx - r - 4 * S, ky - r - 10 * S, kx + r + 4 * S, ky + r - 50 * S), 180, 360, fill=haare)
        d.polygon([(kx - r, ky - 20 * S), (kx - 10 * S, ky - r + 10 * S), (kx + r, ky - 40 * S),
                   (kx + r, ky - 70 * S), (kx - r, ky - 80 * S)], fill=haare)
    elif frisur == "zopf":
        d.chord((kx - r - 4 * S, ky - r - 10 * S, kx + r + 4 * S, ky + r - 30 * S), 180, 360, fill=haare)
        d.ellipse((kx + r - 30 * S, ky - 40 * S, kx + r + 50 * S, ky + 60 * S), fill=haare)
    # Gesicht
    augen_y = ky + 10 * S
    for ax in (kx - 40 * S, kx + 40 * S):
        if blinzeln:
            d.line((ax - 14 * S, augen_y, ax + 14 * S, augen_y), fill=(30, 30, 36), width=6 * S)
        else:
            d.ellipse((ax - 12 * S, augen_y - 14 * S, ax + 12 * S, augen_y + 14 * S), fill=(30, 30, 36))
            d.ellipse((ax - 4 * S, augen_y - 9 * S, ax + 3 * S, augen_y - 2 * S), fill=(255, 255, 255))
        # Augenbrauen
        neigung = {"traurig": 10, "staunt": -2}.get(stimmung, 0) * S * (1 if ax < kx else -1)
        d.line((ax - 18 * S, augen_y - 36 * S - neigung, ax + 18 * S, augen_y - 36 * S + neigung),
               fill=dunkler(haare, 0.8), width=7 * S)
    if f.get("brille"):
        for ax in (kx - 40 * S, kx + 40 * S):
            d.ellipse((ax - 30 * S, augen_y - 28 * S, ax + 30 * S, augen_y + 28 * S), outline=(30, 30, 36), width=6 * S)
        d.line((kx - 10 * S, augen_y, kx + 10 * S, augen_y), fill=(30, 30, 36), width=6 * S)
    mund_y = ky + 62 * S
    if stimmung == "freut":
        d.chord((kx - 40 * S, mund_y - 30 * S, kx + 40 * S, mund_y + 26 * S), 0, 180, fill=(150, 40, 50))
        for ax in (kx - 70 * S, kx + 70 * S):
            d.ellipse((ax - 18 * S, ky + 30 * S, ax + 18 * S, ky + 50 * S), fill=(245, 150, 150))
    elif stimmung == "traurig":
        d.arc((kx - 30 * S, mund_y, kx + 30 * S, mund_y + 36 * S), 200, 340, fill=(90, 40, 40), width=7 * S)
    elif stimmung == "staunt":
        d.ellipse((kx - 16 * S, mund_y - 12 * S, kx + 16 * S, mund_y + 22 * S), fill=(110, 30, 40))
    else:
        d.arc((kx - 30 * S, mund_y - 24 * S, kx + 30 * S, mund_y + 12 * S), 20, 160, fill=(90, 40, 40), width=7 * S)
    bild = bild.resize((w // S, h // S), Image.LANCZOS)
    return bild, (hand[0] / S, hand[1] / S)


# ---------------------------------------------------------------- Szene

def zeichne_bild(ebene, t, sz, emoji_bild, untertitel):
    """Ort + Figuren (+ Gegenstände) + Untertitel. `t` = Sekunden seit Szenenbeginn."""
    ort = ort_ebene(sz.get("ort", "neutral"))
    zoom = 1 + 0.012 * t                                   # langsame Kamerafahrt
    if zoom != 1:
        ow, oh = ort.size
        ort = ort.resize((round(ow * zoom), round(oh * zoom)), Image.BILINEAR)
        links, oben = (ort.width - ow) // 2, (ort.height - oh) // 2
        ort = ort.crop((links, oben, links + ow, oben + oh))
    ebene.alpha_composite(ort, (0, OBEN))
    figuren = sz.get("_figuren", {})
    for i, fz in enumerate(sz.get("figuren", [])):
        f = figuren.get(fz["wer"], {})
        p = ease_out(clamp((t - 0.1 * i) / 0.45))
        blinzeln = (t + i * 1.3) % 3.4 < 0.12
        figur, hand = zeichne_figur(f, fz.get("stimmung", "normal"), fz.get("pose", "steht"), t, blinzeln)
        groesse = fz.get("groesse", 1.0)
        if groesse != 1.0:
            figur = figur.resize((round(figur.width * groesse), round(figur.height * groesse)), Image.LANCZOS)
            hand = (hand[0] * groesse, hand[1] * groesse)
        if fz.get("spiegeln"):
            figur = figur.transpose(Image.FLIP_LEFT_RIGHT)
            hand = (figur.width - hand[0], hand[1])
        x = fz.get("x", 0.5) * B + (1 - p) * (-160 if fz.get("x", 0.5) < 0.5 else 160)
        wippen = math.sin(t * 2.2 + i) * 4
        links_oben = (round(x - figur.width / 2), round(BODEN - figur.height + wippen))
        ebene.alpha_composite(_deckkraft(figur, p), links_oben)
        if fz.get("haelt"):
            gegenstand = emoji_bild(fz["haelt"], 110)
            if gegenstand is not None:
                einfuegen(ebene, gegenstand, (links_oben[0] + hand[0], links_oben[1] + hand[1] - 10), p)
        if fz.get("blase"):  # Gedanken-/Sprechblase mit Emoji über dem Kopf
            blase = emoji_bild(fz["blase"], 120)
            q = ease_out(clamp((t - 0.5) / 0.35))
            mitte = (x + 120, BODEN - figur.height - 40)
            kreis = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
            ImageDraw.Draw(kreis).ellipse((0, 0, 219, 219), fill=(255, 255, 255, 235))
            einfuegen(ebene, kreis, mitte, q, 0.6 + 0.4 * q)
            if blase is not None:
                einfuegen(ebene, blase, mitte, q, 0.6 + 0.4 * q)
    for gz in sz.get("gegenstaende", []):  # frei stehende Emojis, z. B. Geldscheine, die herunterfallen
        q = ease_out(clamp((t - gz.get("ab", 0.3)) / 0.4))
        bild = emoji_bild(gz["emoji"], gz.get("groesse", 120))
        if bild is not None:
            einfuegen(ebene, bild, (gz.get("x", 0.5) * B, gz.get("y", 1100) - 60 * (1 - q)), q)
    if sz.get("text"):
        q = ease_out(clamp(t / 0.3))
        einfuegen(ebene, untertitel(sz["text"]), (B / 2, OBEN + 150), q, 0.94 + 0.06 * q)


def _deckkraft(bild, p):
    if p >= 1:
        return bild
    kopie = bild.copy()
    kopie.putalpha(kopie.getchannel("A").point(lambda a: int(a * p)))
    return kopie
