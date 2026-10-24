"""Text, Emojis und Bild-Hilfsfunktionen (übernommen aus dem IQKnacker-Generator)."""

import math
import os
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

EMOJI_RENDER_GROESSE = 109  # Noto Color Emoji ist eine Bitmap-Schrift und gibt es nur in dieser Größe
UNSICHTBAR = {"️", "‍"} | {chr(c) for c in range(0x1F3FB, 0x1F400)}  # inkl. Hautfarben
FEHLENDE_EMOJI = set()


# ---------------------------------------------------------------- Hilfsfunktionen

def hex_zu_rgb(farbe):
    farbe = farbe.lstrip("#")
    return tuple(int(farbe[i:i + 2], 16) for i in (0, 2, 4))


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_out_back(x):
    """Schießt leicht über das Ziel hinaus und federt zurück – für „Pop“-Effekte."""
    x = clamp(x)
    c1 = 1.70158
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def farbmix(a, b, anteil):
    return tuple(round(x + (y - x) * anteil) for x, y in zip(a, b))


def radialer_verlauf(breite, hoehe, farbe, innen, aussen, staerke=1.0):
    """Ebene mit radialem Verlauf von Deckkraft `innen` (Mitte) zu `aussen` (Rand)."""
    klein_b, klein_h = max(8, breite // 10), max(8, hoehe // 10)
    alpha = Image.new("L", (klein_b, klein_h))
    pixel = alpha.load()
    for y in range(klein_h):
        for x in range(klein_b):
            dx = (x + 0.5) / klein_b * 2 - 1
            dy = (y + 0.5) / klein_h * 2 - 1
            d = clamp(math.hypot(dx, dy) / math.sqrt(2) * 1.25)
            pixel[x, y] = round(255 * (innen + (aussen - innen) * d ** staerke))
    ebene = Image.new("RGBA", (breite, hoehe), farbe[:3] + (0,))
    ebene.putalpha(alpha.resize((breite, hoehe), Image.BICUBIC))
    return ebene


def ist_emoji(zeichen):
    cp = ord(zeichen)
    return cp >= 0x1F000 or 0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF or 0x2300 <= cp <= 0x23FF \
        or zeichen in UNSICHTBAR


@lru_cache(maxsize=64)
def schrift(pfad, groesse):
    return ImageFont.truetype(pfad, groesse)


@lru_cache(maxsize=4)
def emoji_schrift(pfad):
    try:
        return ImageFont.truetype(pfad, EMOJI_RENDER_GROESSE)
    except OSError:
        return None


def mit_deckkraft(bild, deckkraft):
    """Gibt eine Kopie des RGBA-Bilds mit reduzierter Deckkraft zurück."""
    if deckkraft >= 0.999:
        return bild
    bild = bild.copy()
    alpha = bild.getchannel("A").point([int(i * deckkraft) for i in range(256)])
    bild.putalpha(alpha)
    return bild


def einfuegen(frame, ebene, mitte, deckkraft=1.0, skalierung=1.0):
    """Setzt eine RGBA-Ebene zentriert auf `mitte` in den Frame."""
    if deckkraft <= 0.001:
        return
    if abs(skalierung - 1.0) > 0.001:
        w = max(1, round(ebene.width * skalierung))
        h = max(1, round(ebene.height * skalierung))
        ebene = ebene.resize((w, h), Image.BICUBIC)
    ebene = mit_deckkraft(ebene, deckkraft)
    x = round(mitte[0] - ebene.width / 2)
    y = round(mitte[1] - ebene.height / 2)
    # Teile außerhalb des Frames abschneiden (alpha_composite erlaubt keine negativen Koordinaten)
    links, oben = max(0, -x), max(0, -y)
    if links or oben:
        ebene = ebene.crop((links, oben, ebene.width, ebene.height))
        x, y = x + links, y + oben
    frame.alpha_composite(ebene, dest=(x, y))


# ---------------------------------------------------------------- Text mit Hervorhebung und Emojis

def zerlege_text(text):
    """Zerlegt Text in Absätze aus Wörtern. *so* markierte Stellen werden in der Akzentfarbe gesetzt.

    Rückgabe: Liste von Absätzen, jeder Absatz ist eine Liste von Wörtern,
    jedes Wort eine Liste von (teiltext, akzent)-Stücken.
    """
    absaetze = []
    akzent = False
    for zeile in text.split("\n"):
        woerter = []
        for roh in zeile.split(" "):
            if roh == "":
                continue
            stuecke, puffer = [], ""
            for z in roh:
                if z == "*":
                    if puffer:
                        stuecke.append((puffer, akzent))
                        puffer = ""
                    akzent = not akzent
                else:
                    puffer += z
            if puffer:
                stuecke.append((puffer, akzent))
            if stuecke:
                woerter.append(stuecke)
        absaetze.append(woerter)
    return absaetze


class TextSetzer:
    def __init__(self, schrift_pfad, emoji_pfad):
        self.schrift_pfad = schrift_pfad
        self.emoji_schrift = emoji_schrift(emoji_pfad) if emoji_pfad and os.path.exists(emoji_pfad) else None
        self._emoji_cache = {}

    def _emoji_bild(self, zeichen, hoehe):
        schluessel = (zeichen, hoehe)
        if schluessel not in self._emoji_cache:
            bild = None
            if self.emoji_schrift is not None:
                roh = Image.new("RGBA", (EMOJI_RENDER_GROESSE * 2, EMOJI_RENDER_GROESSE * 2), (0, 0, 0, 0))
                ImageDraw.Draw(roh).text((0, 0), zeichen, font=self.emoji_schrift, embedded_color=True)
                box = roh.getbbox()
                if box:
                    roh = roh.crop(box)
                    breite = max(1, round(roh.width * hoehe / roh.height))
                    bild = roh.resize((breite, hoehe), Image.LANCZOS)
            if bild is None and zeichen not in FEHLENDE_EMOJI:
                FEHLENDE_EMOJI.add(zeichen)
                print(f"  ⚠ Emoji „{zeichen}“ (U+{ord(zeichen):04X}) kann nicht dargestellt werden und fehlt im Video.")
            self._emoji_cache[schluessel] = bild
        return self._emoji_cache[schluessel]

    def _laeufe(self, teiltext):
        """Teilt Text in Läufe aus normalen Zeichen und Emojis."""
        laeufe, puffer, modus = [], "", None
        for z in teiltext:
            m = ist_emoji(z)
            if modus is not None and m != modus:
                laeufe.append((puffer, modus))
                puffer = ""
            puffer += z
            modus = m
        if puffer:
            laeufe.append((puffer, modus))
        return laeufe

    def _emoji_hoehe(self, groesse):
        return round(groesse * 0.95)

    def wortbreite(self, wort, groesse):
        f = schrift(self.schrift_pfad, groesse)
        breite = 0
        for teiltext, _ in wort:
            for lauf, emoji in self._laeufe(teiltext):
                if emoji:
                    for z in lauf:
                        if z in UNSICHTBAR:
                            continue
                        bild = self._emoji_bild(z, self._emoji_hoehe(groesse))
                        breite += (bild.width if bild else 0) + round(groesse * 0.04)
                else:
                    breite += f.getlength(lauf)
        return breite

    def umbrechen(self, text, groesse, max_breite):
        """Gibt Zeilen (Listen von Wörtern) und ob alles in die Breite passt zurück."""
        f = schrift(self.schrift_pfad, groesse)
        leer = f.getlength(" ")
        zeilen, passt = [], True
        for absatz in zerlege_text(text):
            zeile, breite = [], 0
            for wort in absatz:
                wb = self.wortbreite(wort, groesse)
                if wb > max_breite:
                    passt = False
                neue_breite = wb if not zeile else breite + leer + wb
                if zeile and neue_breite > max_breite:
                    zeilen.append(zeile)
                    zeile, breite = [wort], wb
                else:
                    zeile.append(wort)
                    breite = neue_breite
            zeilen.append(zeile)
        return zeilen, passt

    def passende_groesse(self, text, max_breite, max_hoehe, max_groesse, min_groesse, zeilenabstand):
        """Größte Schriftgröße, bei der der Text in den Kasten passt."""
        for groesse in range(max_groesse, min_groesse - 1, -2):
            zeilen, passt = self.umbrechen(text, groesse, max_breite)
            if passt and len(zeilen) * groesse * zeilenabstand <= max_hoehe:
                return groesse
        return min_groesse

    def block_mit_woertern(self, text, groesse, max_breite, farbe, akzent, zeilenabstand=1.2):
        """Setzt zentrierten, umbrochenen Text auf eine transparente Ebene.

        Rückgabe: (Ebene, Liste der Wort-Rechtecke) – die Rechtecke braucht die Wort-für-Wort-Animation.
        """
        f = schrift(self.schrift_pfad, groesse)
        leer = f.getlength(" ")
        zeilen, _ = self.umbrechen(text, groesse, max_breite)
        zeilenhoehe = round(groesse * zeilenabstand)
        oberlaenge, unterlaenge = f.getmetrics()
        breiten = [sum(self.wortbreite(w, groesse) for w in z) + leer * max(0, len(z) - 1) for z in zeilen]
        ebenen_breite = math.ceil(max(breiten + [1])) + 8
        ebenen_hoehe = zeilenhoehe * (len(zeilen) - 1) + oberlaenge + unterlaenge + 8
        ebene = Image.new("RGBA", (ebenen_breite, ebenen_hoehe), (0, 0, 0, 0))
        zeichnen = ImageDraw.Draw(ebene)
        wortboxen = []

        def zeilengrenze(i):
            unterkante_davor = 4 + oberlaenge + (i - 1) * zeilenhoehe + unterlaenge
            oberkante = 4 + i * zeilenhoehe
            return round((unterkante_davor + oberkante) / 2)

        for i, (zeile, zb) in enumerate(zip(zeilen, breiten)):
            x = (ebenen_breite - zb) / 2
            grundlinie = 4 + oberlaenge + i * zeilenhoehe
            for j, wort in enumerate(zeile):
                if j:
                    x += leer
                wort_start = x
                for teiltext, ist_akzent in wort:
                    fuellung = akzent if ist_akzent else farbe
                    for lauf, emoji in self._laeufe(teiltext):
                        if emoji:
                            for z in lauf:
                                if z in UNSICHTBAR:
                                    continue
                                bild = self._emoji_bild(z, self._emoji_hoehe(groesse))
                                if bild:
                                    y = round(grundlinie - bild.height * 0.85)
                                    ebene.alpha_composite(bild, dest=(round(x), max(0, y)))
                                    x += bild.width + round(groesse * 0.04)
                        else:
                            zeichnen.text((x, grundlinie), lauf, font=f, fill=fuellung, anchor="ls")
                            x += f.getlength(lauf)
                # Rechtecke überlappen sich nicht: Grenzen liegen mittig zwischen Wörtern bzw. Zeilen
                oben = 0 if i == 0 else zeilengrenze(i)
                unten = ebenen_hoehe if i == len(zeilen) - 1 else zeilengrenze(i + 1)
                wortboxen.append((max(0, math.floor(wort_start - leer / 2)), oben,
                                  min(ebenen_breite, math.ceil(x + leer / 2)), unten))
        return ebene, wortboxen

    def block(self, *args, **kwargs):
        """Wie block_mit_woertern, aber nur die fertige Ebene."""
        return self.block_mit_woertern(*args, **kwargs)[0]
