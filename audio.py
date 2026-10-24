"""Ton für Dotchi-Videos: Stimme (ElevenLabs, zwischengespeichert), synthetische Musik und Effekte.

Die Musik entsteht komplett im Code – keine Musikdateien, keine Lizenzfragen. Jedes Video bekommt
eine eigene Variante (Tonart, Akkordfolge, Tempo), damit die Videos nicht gleich klingen.
"""

import hashlib
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import wave

import numpy as np

SR = 44100
SCHLUESSEL_DATEI = os.path.expanduser("~/.elevenlabs")

AKKORDFOLGEN = [
    [(0, [0, 3, 7, 10]), (-4, [0, 4, 7, 11]), (-9, [0, 4, 7, 11]), (-2, [0, 4, 7, 10])],  # i7 – VImaj7 – IIImaj7 – VII7
    [(0, [0, 3, 7, 10]), (5, [0, 3, 7, 10]), (-4, [0, 4, 7, 11]), (-5, [0, 4, 7, 10])],   # i7 – iv7 – VImaj7 – V7
    [(0, [0, 4, 7, 11]), (-3, [0, 3, 7, 10]), (5, [0, 4, 7, 11]), (7, [0, 4, 7, 10])],    # Imaj7 – vi7 – IVmaj7 – V7
    [(0, [0, 4, 7, 11]), (7, [0, 4, 7, 10]), (-3, [0, 3, 7, 10]), (5, [0, 4, 7, 11])],    # Imaj7 – V7 – vi7 – IVmaj7
]


def zeitachse(dauer):
    return np.arange(max(1, int(round(dauer * SR)))) / SR


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def flaeche(frequenzen, dauer, attack=0.3, release=0.6):
    """Weicher Synthesizer-Teppich aus leicht verstimmten, gedämpften Sägezahn-Stimmen."""
    t = zeitachse(dauer + release)
    signal = np.zeros_like(t)
    for f in frequenzen:
        for d in (-0.08, 0.08):
            phase = 2 * np.pi * f * 2 ** (d / 12) * t
            for k in range(1, 6):
                signal += np.sin(k * phase) / k ** 1.5
    huelle = np.minimum(1, t / attack) * np.clip((dauer + release - t) / release, 0, 1)
    return signal * huelle / (2 * len(frequenzen))


def bass(f, dauer):
    t = zeitachse(dauer)
    signal = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
    huelle = np.minimum(1, t / 0.004) * np.exp(-t * 5) * np.clip((dauer - t) / 0.01, 0, 1)
    return np.tanh(1.5 * signal * huelle) / np.tanh(1.5)


def kick(dauer=0.4):
    t = zeitachse(dauer)
    phase = 2 * np.pi * (45 * t + 75 / 30 * (1 - np.exp(-30 * t)))
    return np.sin(phase) * np.exp(-t * 9) * np.minimum(1, t / 0.002)


def hihat(rng, dauer=0.04):
    t = zeitachse(dauer)
    return np.diff(rng.standard_normal(len(t)), prepend=0.0) * np.exp(-t * 110) * 0.5


def einmischen(spur, start, signal, lautstaerke=1.0):
    i0 = max(0, int(round(start * SR)))
    stueck = signal[: max(0, len(spur) - i0)]
    spur[i0:i0 + len(stueck)] += stueck * lautstaerke


def musik(dauer, saat):
    """Lockerer Beat mit Akkordteppich; Tonart, Akkordfolge und Tempo hängen von `saat` ab."""
    rng = np.random.default_rng(int(hashlib.sha1(str(saat).encode()).hexdigest()[:8], 16))
    grund = int(rng.choice([55, 57, 58, 60, 62]))
    folge = AKKORDFOLGEN[int(rng.integers(len(AKKORDFOLGEN)))]
    bpm = float(rng.choice([96, 100, 104, 110]))
    takt = 60 / bpm * 4
    spur = np.zeros(int(dauer * SR))
    t, i = 0.0, 0
    while t < dauer:
        versatz, stufen = folge[i % len(folge)]
        wurzel = grund + versatz
        einmischen(spur, t, flaeche([hz(wurzel + s) for s in stufen], takt), 0.22)
        einmischen(spur, t, bass(hz(wurzel - 24), takt / 2), 0.35)
        einmischen(spur, t + takt / 2, bass(hz(wurzel - 24), takt / 2), 0.3)
        for schlag in range(4):
            einmischen(spur, t + schlag * takt / 4, kick(), 0.55 if schlag % 2 == 0 else 0.35)
            einmischen(spur, t + (schlag + 0.5) * takt / 4, hihat(rng), 0.18)
        t += takt
        i += 1
    return spur


def whoosh(rng, dauer=0.35):
    x = zeitachse(dauer)
    gefiltert = np.convolve(rng.standard_normal(len(x)), np.ones(12) / 12, mode="same")
    return gefiltert * np.sin(np.pi * x / dauer) ** 2 * 0.5


def ching(dauer=0.6):
    """Heller Kassen-Klang für große Zahlen."""
    x = zeitachse(dauer)
    ton = sum(np.sin(2 * np.pi * f * x) * a for f, a in ((1568, 0.5), (2093, 0.35), (3136, 0.2)))
    return ton * np.exp(-x * 7) * 0.45


def stempel(rng, dauer=0.45):
    """Dumpfer Stempel-Schlag mit kurzem Glanz für das Urteil."""
    x = zeitachse(dauer)
    schlag = np.sin(2 * np.pi * (70 * x + 60 / 25 * (1 - np.exp(-25 * x)))) * np.exp(-x * 14)
    klick = np.convolve(rng.standard_normal(len(x)), np.ones(6) / 6, mode="same") * np.exp(-x * 60)
    return (schlag + klick * 0.6) * 0.8 + ching(dauer) * 0.5


# ---------------------------------------------------------------- Stimme

def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def ssl_kontext():
    """Zertifikate aus certifi – das python.org-Python auf dem Mac bringt keine eigenen mit."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def elevenlabs(satz, cfg, cache):
    """Satz bei ElevenLabs sprechen lassen (MP3, zwischengespeichert) und als 44,1-kHz-Mono-Array zurückgeben."""
    st = cfg["stimme"]
    kennung = json.dumps([st["voice_id"], st["modell"], st["einstellungen"], satz], sort_keys=True)
    os.makedirs(cache, exist_ok=True)
    mp3 = os.path.join(cache, hashlib.sha1(kennung.encode()).hexdigest() + ".mp3")
    if not os.path.exists(mp3):
        if not os.path.exists(SCHLUESSEL_DATEI):
            sys.exit(f"✗ Kein ElevenLabs-Schlüssel in {SCHLUESSEL_DATEI}. Schlüssel kopieren, dann:\n"
                     "  pbpaste > ~/.elevenlabs && chmod 600 ~/.elevenlabs")
        with open(SCHLUESSEL_DATEI, encoding="utf-8") as f:
            schluessel = f.read().strip()
        anfrage = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{st['voice_id']}?output_format=mp3_44100_128",
            data=json.dumps({"text": satz, "model_id": st["modell"],
                             "voice_settings": st["einstellungen"]}).encode(),
            headers={"xi-api-key": schluessel, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(anfrage, timeout=60, context=ssl_kontext()) as antwort:
                daten = antwort.read()
        except urllib.error.HTTPError as fehler:
            sys.exit(f"✗ ElevenLabs meldet Fehler {fehler.code}: {fehler.read().decode(errors='replace')[:400]}\n"
                     "  401 = Schlüssel falsch · 402/429 = Kontingent/Tarif · 404/400 = Voice-ID prüfen")
        except urllib.error.URLError as fehler:
            sys.exit(f"✗ Keine Verbindung zu ElevenLabs: {fehler.reason}\n"
                     "  Bei CERTIFICATE_VERIFY_FAILED: pip install -r requirements.txt")
        with open(mp3 + ".tmp", "wb") as f:
            f.write(daten)
        os.replace(mp3 + ".tmp", mp3)
        print(f"    🎙️ {satz[:70]}")
    roh = subprocess.run([ffmpeg(), "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(roh, dtype=np.int16).astype(np.float32) / 32768


def geschaetzte_dauer(satz):
    """Sprechdauer ohne Stimme schätzen (für Vorschauen): ca. 14 Zeichen pro Sekunde."""
    return max(1.2, len(satz) / 14)


# ---------------------------------------------------------------- Mischen

def mischen(video, stimmen, cfg, ziel, saat):
    """Stimme + Musik (unter der Stimme abgesenkt) + Effekte → Stereo-WAV."""
    rng = np.random.default_rng(7)
    n = int(video.dauer * SR)
    sprache, effekte = np.zeros(n), np.zeros(n)
    for s, st in zip(video.szenen, stimmen):
        if st is not None:
            einmischen(sprache, s.start + 0.15, st)
        einmischen(effekte, s.start, whoosh(rng), 0.8)
        if s.ching is not None:
            einmischen(effekte, s.start + s.ching, ching())
        if s.stempel is not None:
            einmischen(effekte, s.start + s.stempel, stempel(rng))
    m = musik(video.dauer + 1, saat)[:n]
    if any(st is not None for st in stimmen):
        huelle = np.convolve(np.abs(sprache), np.ones(SR // 10) / (SR // 10), mode="same")
        m = m * (1 - 0.75 * np.clip(huelle * 12, 0, 1)) * cfg["audio"]["musik_unter_stimme"]
    else:
        m = m * cfg["audio"]["musik_ohne_stimme"]
    mix = m + sprache + effekte * cfg["audio"]["effekte"]
    # Loop: Ende sanft ausblenden, damit der Übergang zum Anfang nicht knackt
    ausblenden = int(0.3 * SR)
    mix[-ausblenden:] *= np.linspace(1, 0, ausblenden)
    mix = mix / max(1e-6, np.max(np.abs(mix))) * 0.9
    stereo = (np.repeat(mix[:, None], 2, axis=1) * 32767).astype(np.int16)
    with wave.open(ziel, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())
