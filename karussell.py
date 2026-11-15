"""Foto-Karussells für TikTok und Instagram: jede Szene eines Vergleichs als Einzelbild.

Ein Karussell zeigt die Szenen eines vorhandenen Vergleichs im Endzustand (ohne Stimme, ohne Animation),
zugeschnitten auf 1080 × 1350 (4:5 – das höchste Format, das Instagram im Feed erlaubt; TikTok zeigt es mit Rand).
Die erste Folie bekommt einen „Wischen 👉“-Hinweis. Gespeichert wird als JPEG, weil TikTok nur JPEG/WebP annimmt.

    python3 karussell.py 22 26        # Karussells aus Vergleich 22 und 26 → output/karussell/
"""

import os
import sys

from PIL import Image, ImageDraw

from audio import geschaetzte_dauer
from renderer import B, DUNKEL, Video, farbe, text
from text import einfuegen

OBEN, HOEHE = 160, 1350  # Ausschnitt aus dem 1080 × 1920-Bild: Marke oben bis Fußzeile unten
ORDNER = "karussell"


def wischen_hinweis():
    beschriftung = text("Wischen 👉", 44, DUNKEL, breite=600)
    ebene = Image.new("RGBA", (beschriftung.width + 64, beschriftung.height + 28), (0, 0, 0, 0))
    ImageDraw.Draw(ebene).rounded_rectangle((0, 0, ebene.width - 1, ebene.height - 1), ebene.height // 2,
                                            fill=farbe("gold") + (255,))
    ebene.alpha_composite(beschriftung, dest=(32, 14))
    return ebene


def folien(eintrag, cfg, hoechstens=10):
    """Die Szenen des Vergleichs als RGB-Bilder (1080 × 1350), höchstens 10 (mehr nimmt die Metricool-CSV nicht).

    Sind es zu viele, fallen Zwischenrechnungen (Szenen vom Typ „zahl“) aus der Mitte weg – Hook, Urteil und
    Kommentar-Frage bleiben immer. Annahmen und Quellen (fuss) stehen nur auf der letzten Folie, groß genug zum Lesen.
    """
    video = Video(eintrag, cfg)
    video.zeitplan([geschaetzte_dauer(s.daten["sprich"]) for s in video.szenen], cfg["video"]["loop"])
    fuss, video.fuss = video.fuss, None
    szenen = list(video.szenen)
    while len(szenen) > hoechstens:
        mitte = [s for s in szenen[1:-2] if s.daten["typ"] == "zahl"] or szenen[1:-2]
        szenen.remove(mitte[0])
    bilder = []
    for i, s in enumerate(szenen):
        bild = video.frame(s.start + s.dauer - 0.3).crop((0, OBEN, B, OBEN + HOEHE))
        if i == 0:
            einfuegen(bild, wischen_hinweis(), (B / 2, HOEHE - 120))
        if s is szenen[-1] and fuss:
            einfuegen(bild, fuss, (B / 2, HOEHE - 40 - fuss.height / 2))
        bilder.append(bild.convert("RGB"))
    return bilder


def speichern(eintrag, cfg, basis, dateiname):
    ziel = os.path.join(basis, cfg["ausgabe"]["ordner"], ORDNER)
    os.makedirs(ziel, exist_ok=True)
    pfade = []
    for i, bild in enumerate(folien(eintrag, cfg), 1):
        pfad = os.path.join(ziel, f"{dateiname}_k{i:02d}.jpg")
        bild.save(pfad, "JPEG", quality=90)
        pfade.append(pfad)
    return pfade


if __name__ == "__main__":
    import generate
    cfg = generate.lade_json(os.path.join(generate.BASIS, "config.json"))
    alle = {v["id"]: v for v in generate.lade_json(os.path.join(generate.BASIS, "vergleiche.json"))}
    for nummer in map(int, sys.argv[1:]):
        pfade = speichern(alle[nummer], cfg, generate.BASIS, generate.dateiname(alle[nummer]))
        print(f"✓ {nummer}: {len(pfade)} Folien → {os.path.relpath(os.path.dirname(pfade[0]), generate.BASIS)}/")
