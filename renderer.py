"""Zeichnet die Szenen eines Dotchi-Videos (1080x1920) mit Pillow.

Ein Video besteht aus Szenen – eine pro gesprochenem Satz. Typen:
  titel   große Zeilen nacheinander (Hook, Pointe)
  vs      zwei Karten nebeneinander mit Wert darunter; mit "balken": hochzählende Balken
  zahl    Überschrift, große hochzählende Zahl, Unterzeilen
  liste   Zeilen erscheinen nacheinander (Rechenweg, Perspektiven, Kommentar-Frage)
  urteil  „Dotchi?“ – die Gewinnerseite bekommt den Stempel, die andere wird ausgegraut
"""

import math
import os

from PIL import Image, ImageDraw

from text import (TextSetzer, clamp, ease_out, ease_out_back, einfuegen, hex_zu_rgb, radialer_verlauf,
                  schrift)

B, H = 1080, 1920
BASIS = os.path.dirname(os.path.abspath(__file__))
FETT = os.path.join(BASIS, "assets/fonts/Montserrat-ExtraBold.ttf")
NORMAL = os.path.join(BASIS, "assets/fonts/Montserrat-Bold.ttf")
EMOJI = os.path.join(BASIS, "assets/fonts/NotoColorEmoji.ttf")
MARKE = os.path.join(BASIS, "assets/logo/marke.png")

WEISS, GRAU, DUNKEL = (255, 255, 255), (170, 172, 185), (20, 20, 24)
FARBEN = {"rot": "#FF4D6D", "gruen": "#2EE59D", "gold": "#FFC83D", "blau": "#4FC3F7", "lila": "#B388FF",
          "orange": "#FF9F43", "grau": "#AAACB9"}
NBSP = " "

fett = TextSetzer(FETT, EMOJI)
normal = TextSetzer(NORMAL, EMOJI)


def farbe(wert, standard="gold"):
    wert = wert or standard
    return hex_zu_rgb(FARBEN.get(wert, wert))


def zahl_text(wert, einheit="€", dezimalen=None):
    """1234.5 → „1.234,50 €“ (deutsches Format); ganze Zahlen ohne Nachkommastellen."""
    if dezimalen is None:
        dezimalen = 0 if abs(wert - round(wert)) < 1e-9 else 2
    s = f"{wert:,.{dezimalen}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s}{NBSP}{einheit}" if einheit else s


def text(t, groesse, f=WEISS, akzent=None, breite=900, setzer=fett):
    t = t.replace(" €", NBSP + "€").replace(" %", NBSP + "%")  # Einheit nie allein in die nächste Zeile
    return setzer.block(t, groesse, breite, f, akzent or farbe("gold"), 1.15)


# ---------------------------------------------------------------- Szenen

def zeichne_titel(bild, t, sz):
    zeilen = [z if isinstance(z, list) else [z, 100] for z in sz["zeilen"]]
    verzoegerung = sz.get("verzoegerung") or [0.12 * i for i in range(len(zeilen))]
    y = sz.get("y", 640)
    for i, (inhalt, groesse) in enumerate(zeilen):
        p = clamp((t - verzoegerung[i]) / 0.35)
        ebene = text(inhalt, groesse)
        if p > 0:
            einfuegen(bild, ebene, (B / 2, y + ebene.height / 2 + (1 - ease_out(p)) * 40), deckkraft=p,
                      skalierung=0.9 + 0.1 * ease_out_back(p))
        y += ebene.height + 30


def zeichne_zahl(bild, t, sz):
    einfuegen(bild, text(sz["oben"], 64, GRAU), (B / 2, 660), deckkraft=clamp(t / 0.25))
    p = ease_out(clamp((t - 0.25) / 1.1))
    einheit, dez = sz.get("einheit", "€"), sz.get("dezimalen")
    wert = sz["wert"] * p if p < 1 else sz["wert"]
    anzeige = zahl_text(round(wert, dez or 0) if p < 1 else wert, einheit, dez)
    groesse = 190
    while groesse > 90 and fett.wortbreite([(anzeige.replace(NBSP, " "), False)], groesse) > 960:
        groesse -= 10  # lange Zahlen (z. B. 139.838.160) kleiner setzen statt abschneiden
    zahl = text(anzeige, groesse, farbe(sz.get("farbe"), "rot"), breite=1000)
    puls = 1 + 0.08 * math.sin(clamp((t - 1.35) / 0.35) * math.pi)
    einfuegen(bild, zahl, (B / 2, 900), deckkraft=clamp((t - 0.2) / 0.2), skalierung=puls)
    y = 1080
    for i, zeile in enumerate(sz.get("unten", [])):
        q = clamp((t - sz.get("unten_ab", 1.6) - i * 0.9) / 0.3)
        ebene = text(zeile, 70)
        einfuegen(bild, ebene, (B / 2, y + ebene.height / 2 + (1 - ease_out(q)) * 30), deckkraft=q)
        y += ebene.height + 40


def karte(seite, breite=390, hoehe=330, umrandung=None):
    ebene = Image.new("RGBA", (breite, hoehe), (0, 0, 0, 0))
    ImageDraw.Draw(ebene).rounded_rectangle((0, 0, breite - 1, hoehe - 1), 40, fill=(26, 28, 38, 235),
                                            outline=(umrandung or farbe(seite.get("farbe"))) + (255,), width=5)
    e = text(seite["emoji"], 140)
    ebene.alpha_composite(e, ((breite - e.width) // 2, 30))
    n = text(seite["name"], 52, breite=breite - 40)
    ebene.alpha_composite(n, ((breite - n.width) // 2, min(200, hoehe - n.height - 20)))
    return ebene


XS = (275, 805)


def zeichne_vs(bild, t, sz):
    links, rechts = sz["links"], sz["rechts"]
    einfuegen(bild, text(sz.get("kopf", ""), 58, GRAU), (B / 2, 330), deckkraft=clamp(t / 0.25))
    for i, (seite, x) in enumerate(zip((links, rechts), XS)):
        p = clamp((t - 0.1 * i) / 0.35)
        einfuegen(bild, karte(seite), (x, 590 + (1 - ease_out(p)) * 60), deckkraft=p)
    einfuegen(bild, text("vs.", 70), (B / 2, 590), deckkraft=clamp((t - 0.2) / 0.3),
              skalierung=ease_out_back(clamp((t - 0.2) / 0.4)))
    maximal = max(links["wert"], rechts["wert"]) or 1
    for i, (seite, x) in enumerate(zip((links, rechts), XS)):
        f = farbe(seite.get("farbe"))
        einheit, dez = seite.get("einheit", "€"), seite.get("dezimalen")
        if sz.get("balken"):
            p = ease_out(clamp((t - 0.45 - 0.15 * i) / 1.2))
            wert = seite["wert"] * p
            hoehe = max(8, round(430 * wert / maximal))
            einfuegen(bild, Image.new("RGBA", (220, hoehe), f + (255,)), (x, 1300 - hoehe / 2))
            anzeige = zahl_text(round(wert, dez or 0), einheit, dez) if p < 1 else zahl_text(seite["wert"], einheit, dez)
            einfuegen(bild, text(anzeige, 76, f, breite=500), (x, 1300 - hoehe - 60), deckkraft=clamp(p * 4))
        else:
            q = clamp((t - 0.5 - 0.2 * i) / 0.4)
            einfuegen(bild, text(zahl_text(seite["wert"], einheit, dez), 96, f, breite=500), (x, 900),
                      deckkraft=clamp(q * 1.4), skalierung=ease_out_back(q))
            if seite.get("unter"):
                einfuegen(bild, text(seite["unter"], 46, GRAU, breite=480), (x, 990),
                          deckkraft=clamp((t - 0.6 - 0.2 * i) / 0.3))


def zeichne_liste(bild, t, sz):
    if sz.get("kopf"):
        einfuegen(bild, text(sz["kopf"], 60, GRAU), (B / 2, 480), deckkraft=clamp(t / 0.25))
    zeilen = sz["zeilen"]
    y = sz.get("y", 620)
    for i, zeile in enumerate(zeilen):
        p = clamp((t - 0.15 - i * sz.get("abstand", 0.8)) / 0.3)
        groesse = 96 if i == len(zeilen) - 1 and sz.get("letzte_gross") else 78
        ebene = text(zeile, groesse)
        einfuegen(bild, ebene, (B / 2 + (1 - ease_out(p)) * 80, y + ebene.height / 2), deckkraft=p)
        y += ebene.height + 46


def stempel_ebene(inhalt, f):
    """Schräger Stempel mit gezeichnetem Häkchen (Montserrat hat kein ✓)."""
    schrift_ = schrift(FETT, 56)
    breite = int(schrift_.getlength(inhalt)) + 150
    ebene = Image.new("RGBA", (breite, 112), (0, 0, 0, 0))
    d = ImageDraw.Draw(ebene)
    d.rounded_rectangle((4, 4, breite - 5, 107), 22, fill=(12, 13, 18, 235), outline=f + (255,), width=8)
    d.line([(36, 58), (54, 76), (86, 38)], fill=f + (255,), width=11, joint="curve")
    d.text((106, 58), inhalt, font=schrift_, fill=f, anchor="lm")
    return ebene.rotate(-7, expand=True, resample=Image.BICUBIC)


def zeichne_urteil(bild, t, sz):
    einfuegen(bild, text(sz.get("kopf", "Dotchi? 🤔"), 96), (B / 2, 400), deckkraft=clamp(t / 0.25),
              skalierung=0.9 + 0.1 * ease_out_back(clamp(t / 0.35)))
    gewinner = 0 if sz["gewinner"] == "links" else 1
    entscheidung = clamp((t - 1.0) / 0.35)
    for i, (seite, x) in enumerate(zip((sz["links"], sz["rechts"]), XS)):
        sieger = i == gewinner
        k = karte(seite, umrandung=farbe("gruen") if sieger and entscheidung > 0 else farbe("grau"))
        deckkraft = clamp(t / 0.3) * (1 - 0.65 * entscheidung if not sieger else 1)
        skalierung = 1 + (0.08 * ease_out_back(entscheidung) if sieger else -0.06 * entscheidung)
        einfuegen(bild, k, (x, 760), deckkraft=deckkraft, skalierung=skalierung)
        if not sieger and entscheidung > 0:
            einfuegen(bild, text("❌", 120), (x, 760), deckkraft=entscheidung)
    if t >= 1.0:
        p = clamp((t - 1.0) / 0.25)
        st = stempel_ebene(sz.get("stempel", "BESSERE WAHL"), farbe("gruen"))
        x = min(max(XS[gewinner], st.width / 2 + 30), B - st.width / 2 - 30)  # ganz im Bild halten
        einfuegen(bild, st, (x, 970), deckkraft=p, skalierung=1.6 - 0.6 * ease_out(p))
    if sz.get("spruch"):
        q = clamp((t - 1.5) / 0.3)
        einfuegen(bild, text(sz["spruch"], 76), (B / 2, 1180 + (1 - ease_out(q)) * 30), deckkraft=q)


ZEICHNER = {"titel": zeichne_titel, "zahl": zeichne_zahl, "vs": zeichne_vs, "liste": zeichne_liste,
            "urteil": zeichne_urteil}
EFFEKTE = {"zahl": {"ching": 1.35}, "urteil": {"stempel": 1.0}}  # Standard-Zeitpunkte der Soundeffekte


# ---------------------------------------------------------------- Video

class Szene:
    def __init__(self, daten):
        self.daten = daten
        standard = EFFEKTE.get(daten["typ"], {})
        self.ching = daten.get("ching", standard.get("ching"))
        self.stempel = daten.get("stempel_zeit", standard.get("stempel"))
        self.start = self.dauer = 0.0


class Video:
    def __init__(self, eintrag, cfg):
        self.eintrag = eintrag
        self.szenen = [Szene(s) for s in eintrag["szenen"]]
        thema = cfg["themen"].get(eintrag.get("thema"), {})
        hintergrund = farbe(eintrag.get("farbe") or thema.get("farbe"), "gold")
        self.hintergrund = Image.new("RGBA", (B, H), (12, 13, 18, 255))
        self.hintergrund.alpha_composite(radialer_verlauf(B, H, hintergrund, 0.28, 0.0, 1.6))
        if os.path.exists(MARKE):
            marke = Image.open(MARKE).convert("RGBA")
            self.marke = marke.resize((round(marke.width * 96 / marke.height), 96), Image.LANCZOS)
        else:
            self.marke = Image.new("RGBA", (360, 96), (0, 0, 0, 0))
            d = ImageDraw.Draw(self.marke)
            d.rounded_rectangle((0, 0, 359, 95), 48, fill=farbe("gold") + (255,))
            d.text((180, 50), "DOTCHI", font=schrift(FETT, 50), fill=DUNKEL, anchor="mm")
        self.fuss = text(eintrag["fuss"], 34, GRAU, setzer=normal) if eintrag.get("fuss") else None
        self.dauer = 0.0

    def zeitplan(self, sprechdauern, loop=0.3):
        t = 0.0
        for s, sd in zip(self.szenen, sprechdauern):
            s.start = t
            s.dauer = max(s.daten.get("min", 2.4), sd + 0.55)
            t += s.dauer
        self.dauer = t + loop
        return self.dauer

    def frame(self, t):
        bild = self.hintergrund.copy()
        einfuegen(bild, self.marke, (B / 2, 215))
        for s in self.szenen:
            if s.start <= t < s.start + s.dauer or (s is self.szenen[-1] and t >= s.start):
                lokal = t - s.start
                ebene = Image.new("RGBA", (B, H), (0, 0, 0, 0))
                ZEICHNER[s.daten["typ"]](ebene, lokal, s.daten)
                raus = clamp((lokal - (s.dauer - 0.22)) / 0.22) if s is not self.szenen[-1] else 0
                if raus > 0:
                    ebene.putalpha(ebene.getchannel("A").point(lambda a: int(a * (1 - raus))))
                bild.alpha_composite(ebene)
        if self.fuss:
            einfuegen(bild, self.fuss, (B / 2, 1470))
        return bild

    def vorschau(self):
        """Kontaktbogen: je Szene das Bild kurz vor ihrem Ende."""
        bilder = [self.frame(s.start + s.dauer - 0.3).convert("RGB").resize((360, 640)) for s in self.szenen]
        bogen = Image.new("RGB", (360 * len(bilder), 640), (0, 0, 0))
        for i, b in enumerate(bilder):
            bogen.paste(b, (i * 360, 0))
        return bogen
