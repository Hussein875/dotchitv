"""Erzeugt Marke (Videokopf), Profilbild und YouTube-Banner für Dotchi in assets/logo/.

Braucht eine japanische Schrift für „どっち?“ (z. B. IPAGothic); die fertigen PNGs liegen im Repo,
der Generator selbst braucht keine japanische Schrift.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETT = os.path.join(BASIS, "assets/fonts/Montserrat-ExtraBold.ttf")
NORMAL = os.path.join(BASIS, "assets/fonts/Montserrat-Bold.ttf")
JP = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
ZIEL = os.path.join(BASIS, "assets/logo")
GOLD, DUNKEL, GRUEN, ROT, WEISS = (255, 200, 61), (14, 15, 20), (46, 229, 157), (255, 77, 109), (255, 255, 255)


def waage(groesse, neigung=-12, farbe=GOLD, links=ROT, rechts=GRUEN):
    """Balkenwaage, die zur rechten Seite kippt (rechts = schwerer/Gewinner)."""
    s = groesse
    bild = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    w = max(4, s // 28)
    mx, my = s / 2, s * 0.30
    d.line([(mx, my), (mx, s * 0.86)], fill=farbe, width=w)                       # Säule
    d.rounded_rectangle((mx - s * 0.2, s * 0.85, mx + s * 0.2, s * 0.9), w, fill=farbe)  # Fuß
    a = math.radians(neigung)
    halb = s * 0.3
    p1 = (mx - halb * math.cos(a), my + halb * math.sin(a))
    p2 = (mx + halb * math.cos(a), my - halb * math.sin(a))
    d.line([p1, p2], fill=farbe, width=w)                                          # Balken
    d.ellipse((mx - w * 1.6, my - w * 1.6, mx + w * 1.6, my + w * 1.6), fill=farbe)
    for (px, py), schale in ((p1, links), (p2, rechts)):
        tiefe = s * 0.22
        breite = s * 0.13
        d.line([(px, py), (px - breite, py + tiefe)], fill=farbe, width=max(2, w // 2))
        d.line([(px, py), (px + breite, py + tiefe)], fill=farbe, width=max(2, w // 2))
        d.chord((px - breite * 1.15, py + tiefe - breite * 0.6, px + breite * 1.15, py + tiefe + breite * 0.6),
                0, 180, fill=schale)
    return bild


def glow(bild, farbe, radius):
    maske = bild.getchannel("A").filter(ImageFilter.GaussianBlur(radius))
    ebene = Image.new("RGBA", bild.size, farbe + (0,))
    ebene.putalpha(maske.point(lambda a: int(a * 0.55)))
    return ebene


def marke():
    """Gelbe Pille „DOTCHI · どっち?“ für den Kopf jedes Videos (doppelte Auflösung)."""
    f, jp = ImageFont.truetype(FETT, 100), ImageFont.truetype(JP, 84)
    t1, t2 = "DOTCHI", "どっち?"
    b1, b2 = f.getlength(t1), jp.getlength(t2)
    breite = int(b1 + b2 + 60 + 2 * 70)
    bild = Image.new("RGBA", (breite, 192), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    d.rounded_rectangle((0, 0, breite - 1, 191), 96, fill=GOLD)
    d.text((70, 100), t1, font=f, fill=DUNKEL, anchor="lm")
    d.line([(70 + b1 + 30, 50), (70 + b1 + 30, 142)], fill=DUNKEL + (110,), width=5)
    d.text((70 + b1 + 60, 98), t2, font=jp, fill=DUNKEL, anchor="lm")
    bild.save(os.path.join(ZIEL, "marke.png"))


def hintergrund(b, h):
    bild = Image.new("RGBA", (b, h), DUNKEL + (255,))
    licht = Image.new("RGBA", (b, h), (0, 0, 0, 0))
    ImageDraw.Draw(licht).ellipse((b * 0.15, h * 0.05, b * 0.85, h * 0.95), fill=GOLD + (70,))
    return Image.alpha_composite(bild, licht.filter(ImageFilter.GaussianBlur(min(b, h) // 5)))


def profilbild():
    s = 1080
    bild = hintergrund(s, s)
    w = waage(520)
    bild.alpha_composite(glow(w, GOLD, 18), (280, 120))
    bild.alpha_composite(w, (280, 120))
    d = ImageDraw.Draw(bild)
    d.text((s / 2, 720), "DOTCHI", font=ImageFont.truetype(FETT, 170), fill=GOLD, anchor="mm")
    d.text((s / 2, 850), "どっち?", font=ImageFont.truetype(JP, 96), fill=WEISS, anchor="mm")
    bild.convert("RGB").save(os.path.join(ZIEL, "profilbild.png"))


def profilbild_gross():
    """Variante für kleine Anzeigen (TikTok-Kommentare usw.): große Waage + großer Schriftzug, ohne Japanisch."""
    s = 1080
    bild = hintergrund(s, s)
    w = waage(640)
    bild.alpha_composite(glow(w, GOLD, 22), (220, 70))
    bild.alpha_composite(w, (220, 70))
    ImageDraw.Draw(bild).text((s / 2, 790), "DOTCHI", font=ImageFont.truetype(FETT, 172), fill=GOLD, anchor="mm")
    bild.convert("RGB").save(os.path.join(ZIEL, "profilbild_tiktok.png"))


def banner():
    b, h = 2560, 1440  # sicherer Bereich in der Mitte: 1546 x 423
    bild = hintergrund(b, h)
    w = waage(380)
    bild.alpha_composite(glow(w, GOLD, 14), (b // 2 - 760, h // 2 - 205))
    bild.alpha_composite(w, (b // 2 - 760, h // 2 - 205))
    d = ImageDraw.Draw(bild)
    x = b // 2 - 340
    d.text((x, h // 2 - 70), "DOTCHI", font=ImageFont.truetype(FETT, 150), fill=GOLD, anchor="ls")
    breite = ImageFont.truetype(FETT, 150).getlength("DOTCHI")
    d.text((x + breite + 40, h // 2 - 78), "どっち?", font=ImageFont.truetype(JP, 90), fill=WEISS, anchor="ls")
    d.text((x, h // 2 + 30), "Wir vergleichen den Alltag.", font=ImageFont.truetype(NORMAL, 64), fill=WEISS,
           anchor="ls")
    d.text((x, h // 2 + 120), "Du entscheidest.", font=ImageFont.truetype(NORMAL, 64), fill=(170, 172, 185),
           anchor="ls")
    bild.convert("RGB").save(os.path.join(ZIEL, "youtube_banner.png"))


if __name__ == "__main__":
    os.makedirs(ZIEL, exist_ok=True)
    marke()
    profilbild()
    profilbild_gross()
    banner()
    print("✓ assets/logo/marke.png, profilbild.png, profilbild_tiktok.png, youtube_banner.png")
