"""Zeichnet die Szenen eines Dotchi-Videos (1080x1920) mit Pillow.

Ein Video besteht aus Szenen – eine pro gesprochenem Satz. Typen:
  titel   große Zeilen nacheinander (Hook, Pointe)
  vs      zwei Karten nebeneinander mit Wert darunter; mit "balken": hochzählende Balken
  zahl    Überschrift, große hochzählende Zahl, Unterzeilen
  liste   Zeilen erscheinen nacheinander (Rechenweg, Perspektiven, Kommentar-Frage)
  urteil  „Dotchi?“ – die Gewinnerseite bekommt den Stempel, die andere wird ausgegraut
  bild    gezeichnete Geschichten-Szene: Ort, Figuren mit Gegenständen, Untertitel (siehe figuren.py)
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


def text_passend(t, groesse, breite, f=WEISS, setzer=fett, kleinste=28):
    """Wie text(), aber so viel kleiner, bis auch das längste Wort in die Breite passt (z. B. „Mindestlohn-Job“)."""
    geschuetzt = t.replace(" €", NBSP + "€").replace(" %", NBSP + "%")
    while groesse > kleinste and not setzer.umbrechen(geschuetzt, groesse, breite)[1]:
        groesse -= 4
    return text(t, groesse, f, breite=breite, setzer=setzer)


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
    sz["_unten"] = y


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
    n = text_passend(seite["name"], 52, breite - 40)
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
            einfuegen(bild, text_passend(anzeige, 76, 400, f), (x, 1300 - hoehe - 60), deckkraft=clamp(p * 4))
        else:
            q = clamp((t - 0.5 - 0.2 * i) / 0.4)
            einfuegen(bild, text_passend(zahl_text(seite["wert"], einheit, dez), 96, 440, f), (x, 900),
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
    sz["_unten"] = y
    # Kommentar-Frage am Ende: Dotchi winkt darunter – wenn genug Platz ist ("dotchi": false schaltet es ab)
    frei = 1405 - y
    if sz.get("_letzte") and sz.get("dotchi", True) is True and frei >= 290:
        import maskottchen
        groesse = min(0.72, frei / (maskottchen.HOEHE - 50))
        p = clamp((t - 0.55) / 0.4)
        if p > 0:
            figur = maskottchen.zeichne("zwinkert", t, groesse, winkt=True)
            einfuegen(bild, figur, (B / 2, y + frei / 2 + 12 + (1 - ease_out_back(p)) * 70), deckkraft=clamp(p * 3))


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


def schiedsrichter(bild, t, seite, mitte=(B / 2, 760), groesse=0.62, start=0.12, landung=1.0):
    """Dotchi entscheidet: Die Münze fliegt als Münzwurf herein, landet zur Entscheidung und zeigt auf die
    Gewinnerseite (`seite` = "links"/"rechts")."""
    import maskottchen
    x, y = mitte
    if t < start:
        return
    if t < landung:
        p = (t - start) / (landung - start)
        einfuegen(bild, maskottchen.wurf(p, groesse), (x, y - 150 * math.sin(math.pi * p)), deckkraft=clamp(p * 6))
        return
    nach = t - landung
    huepfen = abs(math.sin(nach * 7.5)) * 24 * math.exp(-nach * 1.7)
    figur = maskottchen.zeichne("freut", t, groesse, zeigt=seite, quetschen=clamp(1 - nach / 0.16))
    einfuegen(bild, figur, (x, y - huepfen))


def zeichne_dotchi(bild, t, sz):
    """Optionales Feld "dotchi" in titel-, zahl- und liste-Szenen: Das Maskottchen reagiert auf den Inhalt.

    "dotchi": "staunt"  oder  {"stimmung": "staunt", "ab": 1.35, "x": 0.5, "y": 452, "groesse": 0.46,
                                "zeigt": "links", "winkt": true}
    Bis `ab` schaut Dotchi neugierig zu, danach wechselt es mit einem Hüpfer in die Stimmung."""
    import maskottchen
    angabe = sz["dotchi"] if isinstance(sz["dotchi"], dict) else \
        {"stimmung": sz["dotchi"] if isinstance(sz["dotchi"], str) else "staunt"}
    if sz["typ"] == "zahl":                                  # über der Überschrift
        x, y, groesse = 0.5, 446, 0.5
    else:                                                     # im freien Platz unter dem Text
        frei = 1405 - sz.get("_unten", 1000)
        if frei < 230 and "y" not in angabe:
            return
        x, y, groesse = 0.5, sz.get("_unten", 1000) + frei / 2 + 10, min(0.66, frei / (maskottchen.HOEHE - 60))
    x, y, groesse = angabe.get("x", x) * B, angabe.get("y", y), angabe.get("groesse", groesse)
    ab = angabe.get("ab", 1.35 if sz["typ"] == "zahl" else 0.0)
    rein = clamp((t - 0.15) / 0.35)
    if rein <= 0:
        return
    if t < ab:  # schaut zur Zahl bzw. zum Text
        figur = maskottchen.zeichne("normal", t, groesse, blick=(0, 10) if y < 800 else (0, -10))
        einfuegen(bild, figur, (x, y + (1 - ease_out_back(rein)) * 50), deckkraft=clamp(rein * 3))
        return
    nach = t - ab
    huepfen = abs(math.sin(nach * 7.5)) * 20 * math.exp(-nach * 2.0) if ab > 0 else 0
    figur = maskottchen.zeichne(angabe.get("stimmung", "staunt"), t, groesse, zeigt=angabe.get("zeigt"),
                                winkt=bool(angabe.get("winkt")))
    einfuegen(bild, figur, (x, y - huepfen + (1 - ease_out_back(rein)) * 50), deckkraft=clamp(rein * 3))


def zeichne_urteil(bild, t, sz):
    einfuegen(bild, text(sz.get("kopf", "Dotchi?"), 96), (B / 2, 400), deckkraft=clamp(t / 0.25),
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
    if sz.get("dotchi", True):  # das Maskottchen fällt das Urteil ("dotchi": false schaltet es ab)
        schiedsrichter(bild, t, sz["gewinner"])


def einzeilig(t, groesse, breite, f=WEISS, kleinste=30):
    """Text so klein wie nötig setzen, damit er in eine Zeile passt."""
    geschuetzt = t.replace(" €", NBSP + "€").replace(" %", NBSP + "%")
    while groesse > kleinste and len(fett.umbrechen(geschuetzt, groesse, breite)[0]) > 1:
        groesse -= 4
    return text(t, groesse, f, breite=breite)


def ring_ebene(rest, durchmesser, f, staerke=16):
    """Kreis-Timer: doppelt so groß gezeichnet und verkleinert für glatte Kanten."""
    d = durchmesser * 2
    ebene = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    z = ImageDraw.Draw(ebene)
    z.ellipse((0, 0, d - 1, d - 1), outline=(58, 60, 76, 255), width=staerke * 2)
    if rest > 0.002:
        z.arc((0, 0, d - 1, d - 1), -90, -90 + 360 * rest, fill=f + (255,), width=staerke * 2)
    return ebene.resize((durchmesser, durchmesser), Image.LANCZOS)


def antwort_karte(buchstabe, antwort, richtig=False, breite=740, hoehe=118):
    """Antwort-Zeile A/B/C fürs Preis-Raten; die richtige wird bei der Auflösung grün."""
    ebene = Image.new("RGBA", (breite, hoehe), (0, 0, 0, 0))
    d = ImageDraw.Draw(ebene)
    f = farbe("gruen") if richtig else farbe("gold")
    d.rounded_rectangle((0, 0, breite - 1, hoehe - 1), 36, fill=(18, 58, 44, 245) if richtig else (26, 28, 38, 235),
                        outline=(f if richtig else (92, 96, 112)) + (255,), width=7 if richtig else 3)
    k = hoehe - 28
    d.ellipse((14, 14, 14 + k, 14 + k), fill=f + (255,))
    d.text((14 + k / 2, 14 + k / 2 + 2), buchstabe, font=schrift(FETT, 58), fill=DUNKEL, anchor="mm")
    platz = breite - k - 70
    inhalt = einzeilig(antwort, 62, platz)
    ebene.alpha_composite(inhalt, (14 + k + 20 + (platz - inhalt.width) // 2, (hoehe - inhalt.height) // 2 + 2))
    return ebene


def raten_zeiten(sz):
    """(Countdown-Start, Auflösung) in Sekunden ab Szenenbeginn – erst wird die Frage gesprochen."""
    start = max(sz.get("_sprechdauer", 2.0) + 0.2, 1.4)
    return start, start + int(sz.get("sekunden", 5))


def zeichne_raten(bild, t, sz):
    """Preis-Raten: Frage, Antworten A/B/C und ein Countdown – dann stempelt Dotchi die richtige Antwort ab."""
    vor = t + (HOOK_VORLAUF if sz.get("_hook") else 0)       # beim Hook sind die Einblendungen schon „gelaufen“
    start, aufloesung = raten_zeiten(sz)
    sekunden = aufloesung - start
    geloest = clamp((t - aufloesung) / 0.3)
    groesse = sz.get("groesse", 88)
    while groesse > 56 and len(fett.umbrechen(sz["frage"], groesse, 960)[0]) > 2:   # höchstens zwei Zeilen
        groesse -= 4
    einfuegen(bild, text(sz["frage"], groesse, breite=960), (B / 2, 400), deckkraft=clamp(vor / 0.25),
              skalierung=0.9 + 0.1 * ease_out_back(clamp(vor / 0.35)))
    oben = 660
    if sz.get("emoji"):
        p = clamp((vor - 0.1) / 0.35)
        einfuegen(bild, text(sz["emoji"], 180), (B / 2, 620), deckkraft=p, skalierung=0.6 + 0.4 * ease_out_back(p))
        oben = 810
    richtig = "ABCD".index(str(sz["richtig"]).upper())
    for i, antwort in enumerate(sz["optionen"]):
        p = clamp((vor - 0.3 - 0.2 * i) / 0.35)
        if p <= 0:
            continue
        y = oben + i * 138 + (1 - ease_out(p)) * 40
        if i == richtig and geloest > 0:
            einfuegen(bild, antwort_karte("ABCD"[i], antwort, True), (B / 2, y),
                      skalierung=1 + 0.07 * ease_out_back(geloest))
        else:
            einfuegen(bild, antwort_karte("ABCD"[i], antwort), (B / 2, y), deckkraft=p * (1 - 0.68 * geloest))
    import maskottchen
    c = t - start
    if geloest < 1:                                           # Countdown-Ring; vor dem Start steht er voll da
        rest = clamp(1 - max(c, 0) / sekunden)
        n = int(clamp(math.ceil(sekunden - max(c, 0)), 1, sekunden))
        puls = 1 + 0.16 * (1 - ease_out(clamp((c % 1) / 0.3))) if c >= 0 else 1
        sichtbar = clamp((vor - 0.5) / 0.3) * (1 - geloest)
        einfuegen(bild, ring_ebene(rest, 190, farbe("gold")), (B / 2, 1285), deckkraft=sichtbar)
        einfuegen(bild, text(str(n), 104, farbe("gold")), (B / 2, 1285), deckkraft=sichtbar, skalierung=puls)
    if geloest > 0:                                           # Stempel auf die richtige Antwort
        st = stempel_ebene(sz.get("stempel", f"{'ABCD'[richtig]} IST RICHTIG"), farbe("gruen"))
        einfuegen(bild, st, (min(B / 2 + 70, B - st.width / 2 - 30), 1285), deckkraft=geloest,
                  skalierung=1.6 - 0.6 * ease_out(geloest))
    if sz.get("dotchi", True):
        rein = clamp((vor - 0.6) / 0.35)
        if rein > 0:
            if t < aufloesung:
                figur = maskottchen.zeichne("denkt", t, 0.5)
                huepfen = 0
            else:
                nach = t - aufloesung
                huepfen = abs(math.sin(nach * 7.5)) * 20 * math.exp(-nach * 2.0)
                stimmung = sz["dotchi"] if isinstance(sz.get("dotchi"), str) else "staunt"
                figur = maskottchen.zeichne(stimmung, t, 0.5)
            einfuegen(bild, figur, (185, 1290 - huepfen + (1 - ease_out_back(rein)) * 50), deckkraft=clamp(rein * 3))


def reihen_abstand(sz):
    """Sekunden zwischen zwei Zeilen: so verteilt, dass die letzte Zeile mit dem gesprochenen Satz endet."""
    if sz.get("abstand"):
        return sz["abstand"]
    return clamp((sz.get("_sprechdauer", 3.0) - 0.8) / max(1, len(sz["reihen"])), 0.45, 1.3)


def zeichne_reihen(bild, t, sz):
    """Zeilen mit Balken, die nacheinander hochzählen – für Altersstufen („Seit deiner Geburt …“) und Ranglisten."""
    reihen = sz["reihen"]
    n = len(reihen)
    einfuegen(bild, text(sz.get("kopf", ""), 58, GRAU), (B / 2, 350), deckkraft=clamp(t / 0.25))
    abstand = reihen_abstand(sz)
    platz_unten = 130 if sz.get("unten") else 0
    hoehe = min(172, (850 - platz_unten) / n)
    oben = 450 + (850 - platz_unten - hoehe * n) / 2
    maximal = max(r["wert"] for r in reihen) or 1
    links, rechts = 80, 930
    folge = list(range(n))[::-1] if sz.get("umgekehrt") else list(range(n))
    for platz, i in enumerate(folge):
        r = reihen[i]
        lokal = t - 0.25 - platz * abstand
        p = clamp(lokal / 0.3)
        if p <= 0:
            continue
        hervor = i + 1 == sz.get("hervor")
        f = farbe(r.get("farbe") or ("gold" if hervor else sz.get("farbe")), "blau")
        z = ease_out(clamp(lokal / 0.8))
        einheit, dez = r.get("einheit", sz.get("einheit", "€")), r.get("dezimalen", sz.get("dezimalen"))
        y = oben + i * hoehe + (1 - ease_out(p)) * 30
        name = einzeilig(r["name"], 66 if hervor else 58, 430)
        einfuegen(bild, name, (links + name.width / 2, y + 36), deckkraft=p)
        anzeige = zahl_text(round(r["wert"] * z, dez or 0) if z < 1 else r["wert"], einheit, dez)
        zahl = einzeilig(anzeige, 74 if hervor else 66, 500, f)
        einfuegen(bild, zahl, (rechts - zahl.width / 2, y + 36), deckkraft=p)
        if sz.get("balken", True) is False:                  # nur Zahlen, z. B. wenn die Werte weit auseinanderliegen
            continue
        spur = Image.new("RGBA", (rechts - links, 22), (0, 0, 0, 0))
        d = ImageDraw.Draw(spur)
        d.rounded_rectangle((0, 0, spur.width - 1, 21), 11, fill=(44, 46, 60, 255))
        breite = round(spur.width * r["wert"] / maximal * z)
        if breite >= 22:
            d.rounded_rectangle((0, 0, breite - 1, 21), 11, fill=f + (255,))
        einfuegen(bild, spur, (B / 2 + (links + rechts - B) / 2, y + 96), deckkraft=p)
    if sz.get("unten"):
        q = clamp((t - 0.25 - (n - 1) * abstand - 0.9) / 0.3)
        einfuegen(bild, text(sz["unten"], 66), (B / 2, oben + n * hoehe + 60 + (1 - ease_out(q)) * 30), deckkraft=q)


def zeichne_bild(bild, t, sz):
    import figuren
    figuren.zeichne_bild(bild, t, sz, fett._emoji_bild,
                         lambda satz: text(satz, sz.get("groesse", 64), WEISS, breite=940),
                         lambda satz, groesse, breite: text(satz, groesse, DUNKEL, akzent=farbe("rot"), breite=breite))


ZEICHNER = {"titel": zeichne_titel, "zahl": zeichne_zahl, "vs": zeichne_vs, "liste": zeichne_liste,
            "urteil": zeichne_urteil, "bild": zeichne_bild, "raten": zeichne_raten, "reihen": zeichne_reihen}
HOOK_VORLAUF = 1.5  # Sekunden: so weit sind die Einblend-Animationen der ersten Szene schon „gelaufen“
EIGENER_VORLAUF = {"raten"}  # Szenen mit Countdown rechnen den Vorlauf selbst ein (der Countdown läuft in Echtzeit)
EFFEKTE = {"zahl": {"ching": 1.35}, "urteil": {"stempel": 1.0}}  # Standard-Zeitpunkte der Soundeffekte


# ---------------------------------------------------------------- Video

class Szene:
    def __init__(self, daten):
        self.daten = daten
        standard = EFFEKTE.get(daten["typ"], {})
        self.ching = daten.get("ching", standard.get("ching"))
        self.stempel = daten.get("stempel_zeit", standard.get("stempel"))
        self.ticks = []  # Zeitpunkte der Countdown-Ticks (Sekunden ab Szenenbeginn)
        self.start = self.dauer = 0.0

    def planen(self, sprechdauer):
        """Dauer der Szene: so lang wie der gesprochene Satz – plus Countdown bzw. Aufbau, wo es einen gibt."""
        d = self.daten
        d["_sprechdauer"] = sprechdauer
        dauer = max(d.get("min", 2.4), sprechdauer + 0.55)
        if d["typ"] == "raten":
            start, aufloesung = raten_zeiten(d)
            self.ticks = [start + i for i in range(round(aufloesung - start))]
            self.stempel = aufloesung
            dauer = aufloesung + d.get("nachlauf", 1.5)
        elif d["typ"] == "reihen":
            fertig = 0.25 + (len(d["reihen"]) - 1) * reihen_abstand(d) + 0.8
            if d.get("ching", True) is True:
                self.ching = fertig
            dauer = max(dauer, fertig + (1.6 if d.get("unten") else 1.0))
        return dauer


class Video:
    def __init__(self, eintrag, cfg):
        self.eintrag = eintrag
        # Geschichten-Szenen brauchen die Figuren des Eintrags (Aussehen einmal pro Video festgelegt)
        self.szenen = [Szene(dict(s, _figuren=eintrag.get("figuren", {})) if s["typ"] == "bild" else dict(s))
                       for s in eintrag["szenen"]]
        self.szenen[0].daten["_hook"] = True      # erste Szene: alles steht ab dem ersten Bild da
        self.szenen[-1].daten["_letzte"] = True   # letzte Szene: Dotchi winkt unter der Kommentar-Frage
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
            s.dauer = s.planen(sd)
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
                # Der Hook steht ab dem allerersten Bild komplett da: Wer in der ersten Sekunde nichts sieht,
                # wischt weiter – und der erste Frame ist auch das Vorschaubild im Profil
                vorlauf = HOOK_VORLAUF if s is self.szenen[0] and s.daten["typ"] not in EIGENER_VORLAUF else 0
                ZEICHNER[s.daten["typ"]](ebene, lokal + vorlauf, s.daten)
                if s.daten.get("dotchi") and s.daten["typ"] in ("titel", "zahl", "liste") \
                        and not (s.daten.get("_letzte") and s.daten["dotchi"] is True):
                    zeichne_dotchi(ebene, lokal + vorlauf, s.daten)
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
