#!/usr/bin/env python3
"""Dotchi-Generator: macht aus vergleiche.json fertige Shorts (1080x1920, 30 fps, H.264) mit ElevenLabs-Stimme.

    python generate.py                 # alle Vergleiche rendern, die noch kein Video haben
    python generate.py --id 3 7        # nur diese (auch neu rendern)
    python generate.py --vorschau      # Kontaktbögen ohne Stimme (kostet keine Credits)
    python generate.py --plan 7        # Posting-Plan + Metricool-CSV
    python generate.py --check         # Installation prüfen

Inhalte stehen nur in vergleiche.json, geplante Termine in geplant.json, Drive-Links in drive_links.json.
Der Generator verändert keine dieser Dateien beim Rendern – „gerendert“ heißt: Video liegt in output/.
"""

import argparse
import csv
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

BASIS = os.path.dirname(os.path.abspath(__file__))
CONFIG_DATEI = os.path.join(BASIS, "config.json")
VERGLEICHE_DATEI = os.path.join(BASIS, "vergleiche.json")
GEPLANT_DATEI = os.path.join(BASIS, "geplant.json")
LINKS_DATEI = os.path.join(BASIS, "drive_links.json")
CACHE = os.path.join(BASIS, ".stimmen-cache")
SZENEN_TYPEN = {"titel": ["zeilen"], "vs": ["links", "rechts"], "zahl": ["oben", "wert"], "liste": ["zeilen"],
                "urteil": ["links", "rechts", "gewinner"]}
WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def lade_json(pfad, standard=None):
    if standard is not None and not os.path.exists(pfad):
        return standard
    with open(pfad, encoding="utf-8") as f:
        return json.load(f)


def speichere_json(pfad, daten):
    tmp = pfad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, pfad)


def pakete_pruefen():
    try:
        import numpy  # noqa: F401
        import PIL  # noqa: F401
        import imageio_ffmpeg  # noqa: F401
    except ImportError:
        sys.exit("✗ Pakete fehlen. Bitte ausführen:  pip install -r requirements.txt")


def slug(text):
    ersetzt = text.lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]+", "-", ersetzt).strip("-")[:40]


def dateiname(v):
    return f"{v['id']:03d}_{slug(v['titel'])}"


# ---------------------------------------------------------------- Prüfen

def pruefe(vergleiche, cfg):
    fehler, ids = [], set()
    for i, v in enumerate(vergleiche):
        name = f"Vergleich {v.get('id', f'#{i + 1}')}"
        for feld in ("id", "titel", "thema", "szenen"):
            if feld not in v:
                fehler.append(f"{name}: Feld „{feld}“ fehlt")
        if "id" in v:
            if v["id"] in ids:
                fehler.append(f"{name}: ID kommt doppelt vor")
            ids.add(v["id"])
        if v.get("thema") and v["thema"] not in cfg["themen"]:
            fehler.append(f"{name}: unbekanntes Thema „{v['thema']}“ (erlaubt: {', '.join(cfg['themen'])})")
        for j, sz in enumerate(v.get("szenen", []), start=1):
            typ = sz.get("typ")
            if typ not in SZENEN_TYPEN:
                fehler.append(f"{name}, Szene {j}: unbekannter Typ „{typ}“")
                continue
            for feld in ["sprich"] + SZENEN_TYPEN[typ]:
                if feld not in sz:
                    fehler.append(f"{name}, Szene {j} ({typ}): Feld „{feld}“ fehlt")
            if typ == "urteil" and sz.get("gewinner") not in ("links", "rechts"):
                fehler.append(f"{name}, Szene {j}: „gewinner“ muss links oder rechts sein")
            if typ == "vs":
                for seite in ("links", "rechts"):
                    if not isinstance(sz.get(seite, {}).get("wert"), (int, float)):
                        fehler.append(f"{name}, Szene {j}: {seite}.wert muss eine Zahl sein")
            if "*" in sz.get("sprich", ""):
                fehler.append(f"{name}, Szene {j}: im gesprochenen Text („sprich“) keine *Sternchen*")
        if v.get("szenen") and v["szenen"][-1].get("typ") != "liste":
            print(f"⚠ {name}: letzte Szene ist keine Kommentar-Frage (liste) – absichtlich?")
    if fehler:
        sys.exit("✗ Fehler in vergleiche.json:\n  " + "\n  ".join(fehler))


def check(cfg):
    import importlib
    print(f"Python:  {sys.version.split()[0]}", "✓" if sys.version_info >= (3, 8) else "✗ (mind. 3.8 nötig)")
    for paket in ("numpy", "PIL", "imageio_ffmpeg", "openpyxl", "certifi"):
        try:
            importlib.import_module(paket)
            print(f"{paket + ':':<9}✓")
        except ImportError:
            print(f"{paket + ':':<9}✗ fehlt → pip install -r requirements.txt")
    from audio import SCHLUESSEL_DATEI
    print(f"Stimme:  {'✓ Schlüssel in ' + SCHLUESSEL_DATEI if os.path.exists(SCHLUESSEL_DATEI) else '✗ kein Schlüssel – pbpaste > ~/.elevenlabs && chmod 600 ~/.elevenlabs'}"
          f" (Voice-ID {cfg['stimme']['voice_id']})")
    drive = drive_ordner(cfg)
    print(f"Drive:   {'✓ ' + drive if drive else '– Ordner „' + cfg['ausgabe']['drive_ordner'] + '“ nicht gefunden (Google Drive für Desktop)'}")
    for name in ("Montserrat-ExtraBold.ttf", "Montserrat-Bold.ttf", "NotoColorEmoji.ttf"):
        print(f"Schrift: {name} {'✓' if os.path.exists(os.path.join(BASIS, 'assets/fonts', name)) else '✗'}")


# ---------------------------------------------------------------- Rendern

def erzeuge(v, cfg, mit_stimme=True):
    from PIL import Image
    from audio import SR, elevenlabs, ffmpeg, geschaetzte_dauer, mischen
    from renderer import B, H, Video
    from text import clamp

    ausgabe = os.path.join(BASIS, cfg["ausgabe"]["ordner"])
    os.makedirs(ausgabe, exist_ok=True)
    name = dateiname(v)
    video = Video(v, cfg)
    stimmen = [elevenlabs(s.daten["sprich"], cfg, CACHE) if mit_stimme else None for s in video.szenen]
    video.zeitplan([len(st) / SR if st is not None else geschaetzte_dauer(s.daten["sprich"])
                    for s, st in zip(video.szenen, stimmen)], cfg["video"]["loop"])
    fps = cfg["video"]["fps"]
    erster = video.frame(0).convert("RGB")
    erster.save(os.path.join(ausgabe, f"{name}.png"))
    start = time.time()
    roh = os.path.join(ausgabe, f".{name}.bild.mp4")
    prozess = subprocess.Popen([ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{B}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                                "-crf", "18", "-pix_fmt", "yuv420p", roh], stdin=subprocess.PIPE)
    for i in range(int(video.dauer * fps)):
        t = i / fps
        bild = video.frame(t).convert("RGB")
        ueber = clamp((t - (video.dauer - cfg["video"]["loop"])) / cfg["video"]["loop"])
        if ueber > 0:  # Loop: die letzten Frames gehen in den ersten über
            bild = Image.blend(bild, erster, ueber)
        prozess.stdin.write(bild.tobytes())
    prozess.stdin.close()
    if prozess.wait() != 0:
        sys.exit("✗ FFmpeg ist beim Bild abgebrochen.")
    wav = os.path.join(ausgabe, f".{name}.wav")
    mischen(video, stimmen, cfg, wav, saat=v["id"])
    ziel = os.path.join(ausgabe, f"{name}.mp4")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", roh, "-i", wav,
                    "-af", f"loudnorm=I={cfg['audio']['lautheit_lufs']}:TP=-1.5:LRA=11", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", ziel],
                   check=True)
    os.remove(roh)
    os.remove(wav)
    with open(os.path.join(ausgabe, f"{name}_caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption_text(v, cfg) + "\n")
    drive = drive_ordner(cfg)
    if drive:
        nach_drive(ziel, drive)
    print(f"  ✓ {os.path.relpath(ziel, BASIS)}  ({video.dauer:.1f} s, {'mit' if mit_stimme else 'ohne'} Stimme, "
          f"{time.time() - start:.0f} s Renderzeit{', in Google Drive kopiert' if drive else ''})")


def vorschau(v, cfg):
    from audio import geschaetzte_dauer
    from renderer import Video
    ausgabe = os.path.join(BASIS, cfg["ausgabe"]["ordner"])
    os.makedirs(ausgabe, exist_ok=True)
    video = Video(v, cfg)
    video.zeitplan([geschaetzte_dauer(s.daten["sprich"]) for s in video.szenen], cfg["video"]["loop"])
    pfad = os.path.join(ausgabe, f"{dateiname(v)}_vorschau.png")
    video.vorschau().save(pfad)
    print(f"  ✓ {os.path.relpath(pfad, BASIS)}  (~{video.dauer:.0f} s)")


# ---------------------------------------------------------------- Texte

def caption_text(v, cfg):
    tags = [t for t in cfg["themen"][v["thema"]].get("hashtags", [])[:2]] + v.get("hashtags", []) \
        + cfg["hashtags_allgemein"]
    eindeutig = list(dict.fromkeys(tags))
    hinten = cfg["hashtags_allgemein"]
    vorne = [t for t in eindeutig if t not in hinten][:max(0, cfg["hashtags_anzahl"] - len(hinten))]
    return f"{v.get('caption', v['titel'])}\n\n{' '.join(vorne + hinten)}"


def youtube_titel(v):
    titel = v["titel"].replace("<", "").replace(">", "").strip()
    return titel + " #shorts" if len(titel) + 8 < 100 else titel[:99]


# ---------------------------------------------------------------- Google Drive

def drive_ordner(cfg):
    wert = cfg["ausgabe"].get("drive_ordner")
    if not wert:
        return None
    pfad = os.path.expanduser(wert)
    if os.path.isabs(pfad):
        return pfad if os.path.isdir(pfad) else None
    muster = [os.path.expanduser(f"~/Library/CloudStorage/GoogleDrive-*/*/{wert}"),
              os.path.expanduser(f"~/Google Drive/{wert}"), os.path.expanduser(f"~/Google Drive/*/{wert}")]
    treffer = [t for m in muster for t in glob.glob(m) if os.path.isdir(t)]
    return treffer[0] if treffer else None


def nach_drive(video, ziel):
    kopie = os.path.join(ziel, os.path.basename(video))
    if os.path.exists(kopie) and os.path.getsize(kopie) == os.path.getsize(video) \
            and os.path.getmtime(kopie) >= os.path.getmtime(video):
        return False
    shutil.copy2(video, kopie)
    return True


def drive_link(cfg, v):
    """Öffentlicher Drive-Link: Datei-ID über Google Drive für Desktop (macOS) oder aus drive_links.json."""
    datei = dateiname(v) + ".mp4"
    datei_id = None
    drive = drive_ordner(cfg)
    if drive and os.path.exists(os.path.join(drive, datei)) and shutil.which("xattr"):
        try:
            datei_id = subprocess.run(["xattr", "-p", "com.google.drivefs.item-id#S", os.path.join(drive, datei)],
                                      capture_output=True, text=True, timeout=10).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            pass
    datei_id = datei_id or lade_json(LINKS_DATEI, {}).get(datei)
    return f"https://drive.google.com/file/d/{datei_id}/view?usp=sharing" if datei_id else None


# ---------------------------------------------------------------- Posting-Plan

def termine_laden(vergleiche):
    termine = lade_json(GEPLANT_DATEI, {})
    for v in vergleiche:
        v["termin"] = termine.get(str(v["id"]))


def posting_plan(vergleiche, cfg, tage, uhrzeiten, start, nur_drive):
    """Verteilt fertige, noch nicht verplante Videos auf Tage und Uhrzeiten; Termine landen in geplant.json."""
    ausgabe = os.path.join(BASIS, cfg["ausgabe"]["ordner"])
    os.makedirs(ausgabe, exist_ok=True)
    links = lade_json(LINKS_DATEI, {})
    if not nur_drive:  # lokal darf ein Plan für denselben Zeitraum neu vergeben werden
        for v in vergleiche:
            if v.get("termin") and v["termin"][:10] >= start.isoformat() \
                    and v["termin"] > f"{datetime.datetime.now():%Y-%m-%d %H:%M}":
                v["termin"] = None
    fertig = [v for v in vergleiche if not v.get("termin")
              and (dateiname(v) + ".mp4" in links if nur_drive
                   else os.path.exists(os.path.join(ausgabe, dateiname(v) + ".mp4")))]
    jetzt = datetime.datetime.now()
    posts, zeilen, letztes_thema = [], [f"POSTING-PLAN Dotchi – {len(uhrzeiten)} Videos pro Tag", "=" * 44, ""], None
    for tag in range(tage):
        datum = start + datetime.timedelta(days=tag)
        for uhrzeit in uhrzeiten:
            if f"{datum.isoformat()} {uhrzeit}" <= f"{jetzt:%Y-%m-%d %H:%M}" or not fertig:
                continue
            # Abwechslung: möglichst nicht zweimal hintereinander dasselbe Thema
            v = next((x for x in fertig if x["thema"] != letztes_thema), fertig[0])
            fertig.remove(v)
            letztes_thema = v["thema"]
            v["termin"] = f"{datum.isoformat()} {uhrzeit}"
            posts.append((v, datum, uhrzeit))
            zeilen += [f"{WOCHENTAGE[datum.weekday()]}, {datum:%d.%m.} um {uhrzeit} Uhr  →  {dateiname(v)}.mp4",
                       "", "Caption:", caption_text(v, cfg), "", "YouTube-Titel:", youtube_titel(v), "", "-" * 44, ""]
    if len(posts) < tage * len(uhrzeiten):
        zeilen.append(f"Hinweis: Nur {len(posts)} fertige, unverplante Videos – neue Vergleiche rendern.")
    with open(os.path.join(ausgabe, "postingplan.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")
    speichere_json(GEPLANT_DATEI, {str(v["id"]): v["termin"] for v in sorted(vergleiche, key=lambda x: x["id"])
                                   if v.get("termin")})
    ende = start + datetime.timedelta(days=tage - 1)
    dateien, ohne_link = metricool_csv(ausgabe, cfg, posts, start, ende)
    print(f"✓ {len(posts)} Videos auf {start:%d.%m.}–{ende:%d.%m.} verteilt ({', '.join(uhrzeiten)} Uhr) "
          f"→ output/postingplan.txt")
    for d in dateien:
        print(f"✓ {os.path.relpath(d, BASIS)} – in Metricool: Kalender → ⋮ → CSV importieren")
    if ohne_link:
        print(f"⚠ Kein Drive-Link für {len(ohne_link)} Video(s), fehlen in der CSV: {', '.join(ohne_link)}")
    if len(posts) < tage * len(uhrzeiten):
        print(f"⚠ Nur {len(posts)} von {tage * len(uhrzeiten)} Plätzen belegt – es fehlen fertige Videos.")


# Spalten exakt wie in Metricools Vorlage (Kalender → ⋮ → CSV importieren → Vorlage herunterladen)
METRICOOL_SPALTEN = (
    "Text,Date,Time,Draft,Facebook,Twitter/X,LinkedIn,GBP,Instagram,Pinterest,TikTok,Youtube,Threads,Bluesky,"
    + ",".join(f"Picture Url {n}" for n in range(1, 11)) + ","
    + ",".join(f"Alt text picture {n}" for n in range(1, 11)) + ","
    "Document title,Shortener,Video Thumbnail Url,Video Cover Frame,Twitter/X Can reply,Twitter/X Type,"
    "Twitter/X Poll Duration minutes,Twitter/X Poll Option 1,Twitter/X Poll Option 2,Twitter/X Poll Option 3,"
    "Twitter/X Poll Option 4,Pinterest Board,Pinterest Pin Title,Pinterest Pin Link,Pinterest Pin New Format,"
    "Instagram Post Type,Instagram Show Reel On Feed,Instagram Trial Reel Share Automatically,Youtube Video Title,"
    "Youtube Video Type,Youtube Video Privacy,Youtube video for kids,Youtube AI generated content,"
    "Youtube notify subscribers,Youtube Video Category,Youtube Video Tags,Youtube playlist,GBP Post Type,"
    "Facebook Post Type,Facebook Title,First Comment Text,TikTok Title,TikTok disable comments,TikTok disable duet,"
    "TikTok disable stitch,TikTok Post Privacy,TikTok Branded Content,TikTok Your Brand,TikTok Auto Add Music,"
    "TikTok Photo Cover Index,TikTok musicId,TikTok music title,TikTok music author,TikTok music previewUrl,"
    "TikTok music thumbnailUrl,TikTok music soundVolume,TikTok music originalVolume,TikTok music startMillis,"
    "TikTok music endMillis,TikTok Ai generated content,LinkedIn Type,LinkedIn Poll Question,LinkedIn Poll Option 1,"
    "LinkedIn Poll Option 2,LinkedIn Poll Option 3,LinkedIn Poll Option 4,LinkedIn Poll Duration,"
    "LinkedIn Show link preview,LinkedIn Images as Carousel,Threads Reply Control,Threads Is Spoiler,"
    "Threads Post Type,Brand name").split(",")


def metricool_csv(ausgabe, cfg, posts, von, bis):
    mc = cfg["metricool"]
    ki = "true" if mc.get("ki_stimme") else "false"
    zeilen, ohne_link = [], []
    for v, datum, uhrzeit in posts:
        link = drive_link(cfg, v)
        if not link:
            ohne_link.append(dateiname(v) + ".mp4")
            continue
        werte = dict.fromkeys(METRICOOL_SPALTEN, "")
        werte.update({
            "Text": caption_text(v, cfg), "Date": datum.isoformat(), "Time": f"{uhrzeit}:00", "Draft": "false",
            "Facebook": "false", "Twitter/X": "false", "LinkedIn": "false", "GBP": "false", "Pinterest": "false",
            "Threads": "false", "Bluesky": "false", "Shortener": "false",
            "Instagram": "true", "TikTok": "true", "Youtube": "true", "Picture Url 1": link,
            "Instagram Post Type": "REEL", "Instagram Show Reel On Feed": "true",
            "Youtube Video Title": youtube_titel(v), "Youtube Video Type": "SHORT", "Youtube Video Privacy": "PUBLIC",
            "Youtube video for kids": "false", "Youtube AI generated content": ki,
            "Youtube notify subscribers": "true", "Youtube Video Category": mc.get("youtube_kategorie", "EDUCATION"),
            "Youtube Video Tags": ",".join(mc.get("youtube_tags", [])),
            "TikTok disable comments": "false", "TikTok disable duet": "false", "TikTok disable stitch": "false",
            "TikTok Post Privacy": "PUBLIC_TO_EVERYONE", "TikTok Branded Content": "false",
            "TikTok Your Brand": "false", "TikTok Auto Add Music": "false", "TikTok Ai generated content": ki,
            "Brand name": mc.get("marke", ""),
        })
        zeilen.append([werte[s] for s in METRICOOL_SPALTEN])
    for alt in glob.glob(os.path.join(ausgabe, "metricool*.csv")):
        os.remove(alt)
    dateien = []
    for teil in range(0, len(zeilen), 50):  # Metricool empfiehlt höchstens 50 Beiträge pro Datei
        nummer = f"_{teil // 50 + 1}" if len(zeilen) > 50 else ""
        pfad = os.path.join(ausgabe, f"metricool_dotchi_{von:%d.%m}-{bis:%d.%m}{nummer}.csv")
        with open(pfad, "w", encoding="utf-8-sig", newline="") as f:
            schreiber = csv.writer(f)
            schreiber.writerow(METRICOOL_SPALTEN)
            schreiber.writerows(zeilen[teil:teil + 50])
        dateien.append(pfad)
    return dateien, ohne_link


# ---------------------------------------------------------------- Kommandozeile

def main():
    parser = argparse.ArgumentParser(description="Dotchi: erzeugt Vergleichs-Shorts aus vergleiche.json")
    parser.add_argument("--id", type=int, nargs="+", help="nur diese Vergleiche (auch wenn schon gerendert)")
    parser.add_argument("--alle", action="store_true", help="alle Vergleiche neu rendern")
    parser.add_argument("--vorschau", action="store_true", help="nur Kontaktbögen ohne Stimme (keine Credits)")
    parser.add_argument("--ohne-stimme", action="store_true", help="Video ohne Stimme (nur Musik und Effekte)")
    parser.add_argument("--liste", action="store_true", help="alle Vergleiche mit Status anzeigen")
    parser.add_argument("--check", action="store_true", help="Installation prüfen")
    parser.add_argument("--drive", action="store_true", help="fertige Videos in den Google-Drive-Ordner kopieren")
    parser.add_argument("--plan", type=int, metavar="TAGE", help="Posting-Plan + Metricool-CSV für so viele Tage")
    parser.add_argument("--start", help="erster Tag für --plan (JJJJ-MM-TT); Standard: heute bzw. nach dem letzten Termin")
    parser.add_argument("--uhrzeiten", help="für --plan, z. B. 17:30,20:30 (Standard aus config.json)")
    parser.add_argument("--nur-drive", action="store_true",
                        help="für --plan ohne lokale Videos (Cloud): fertig ist, was in drive_links.json steht")
    args = parser.parse_args()

    cfg = lade_json(CONFIG_DATEI)
    if args.check:
        check(cfg)
        return
    vergleiche = lade_json(VERGLEICHE_DATEI)
    pruefe(vergleiche, cfg)
    termine_laden(vergleiche)
    ausgabe = os.path.join(BASIS, cfg["ausgabe"]["ordner"])
    jetzt = f"{datetime.datetime.now():%Y-%m-%d %H:%M}"

    if args.liste:
        for v in vergleiche:
            gerendert = os.path.exists(os.path.join(ausgabe, dateiname(v) + ".mp4"))
            status = ("gepostet" if v["termin"] <= jetzt else f"geplant {v['termin']}") if v.get("termin") else \
                ("gerendert" if gerendert else "neu")
            print(f"{v['id']:>4}  {status:<24} {v['thema']:<8} {v['titel']}")
        return

    if args.drive:
        drive = drive_ordner(cfg)
        if not drive:
            sys.exit(f"✗ Drive-Ordner „{cfg['ausgabe']['drive_ordner']}“ nicht gefunden (Google Drive für Desktop?).")
        videos = [p for p in (os.path.join(ausgabe, dateiname(v) + ".mp4") for v in vergleiche) if os.path.exists(p)]
        neu = sum(nach_drive(p, drive) for p in videos)
        print(f"✓ {neu} von {len(videos)} Videos nach {drive} kopiert")
        return

    if args.plan:
        try:
            uhrzeiten = sorted(f"{datetime.datetime.strptime(u.strip(), '%H:%M'):%H:%M}"
                               for u in (args.uhrzeiten.split(",") if args.uhrzeiten else cfg["plan"]["uhrzeiten"])
                               if u.strip())
        except ValueError:
            sys.exit("✗ --uhrzeiten bitte so angeben: 17:30,20:30")
        if args.start:
            start = datetime.date.fromisoformat(args.start)
        else:
            letzter = max((v["termin"][:10] for v in vergleiche if v.get("termin")), default=None)
            start = datetime.date.today()
            if args.nur_drive and letzter:  # Cloud: nahtlos nach dem letzten verplanten Tag
                start = max(start + datetime.timedelta(days=1),
                            datetime.date.fromisoformat(letzter) + datetime.timedelta(days=1))
        posting_plan(vergleiche, cfg, args.plan, uhrzeiten, start, args.nur_drive)
        return

    pakete_pruefen()
    if args.id:
        auswahl = [v for v in vergleiche if v["id"] in args.id]
        fehlend = set(args.id) - {v["id"] for v in auswahl}
        if fehlend:
            sys.exit(f"✗ Vergleich(e) nicht gefunden: {', '.join(map(str, sorted(fehlend)))}")
    elif args.alle or args.vorschau:
        auswahl = vergleiche
    else:
        auswahl = [v for v in vergleiche if not os.path.exists(os.path.join(ausgabe, dateiname(v) + ".mp4"))]
    if not auswahl:
        print("Alles schon gerendert. Neue Vergleiche in vergleiche.json eintragen oder --id / --alle nutzen.")
        return
    print(f"{'Vorschau für' if args.vorschau else 'Erzeuge'} {len(auswahl)} Video(s) …")
    for v in auswahl:
        print(f"• {v['id']}: {v['titel']}")
        if args.vorschau:
            vorschau(v, cfg)
        else:
            erzeuge(v, cfg, mit_stimme=not args.ohne_stimme)
    print("Fertig.")


if __name__ == "__main__":
    main()
