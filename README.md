# Dotchi – どっち? Alltags-Vergleiche als Shorts

**Dotchi** (jap. どっち, „welches von beiden?“) vergleicht Dinge aus dem Alltag – Kaffee to go vs. Zuhause,
Auto vs. Fahrrad, Abos, Standby, Bildschirmzeit … – und sagt am Ende klar, was die **bessere Wahl** ist.
Gesichtslos, mit Grafik, hochzählenden Zahlen, Balken, KI-Stimme (ElevenLabs) und leiser Musik.

- **Kanäle:** `@dotchitv` auf TikTok, Instagram und YouTube
- **Format:** 1080 × 1920, 30 fps, H.264 + AAC, Lautheit −14 LUFS, ca. 20–30 Sekunden, nahtloser Loop
- **Ziel:** viral gehen – Hook in der ersten Sekunde, klares Urteil, Kommentar- und Teil-Frage am Ende

---

## Einrichtung am Mac (einmalig)

```bash
cd ~/Documents
git clone https://github.com/Hussein875/dotchitv.git
cd dotchitv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 generate.py --check
```

- **ElevenLabs-Schlüssel:** in ElevenLabs (Entwickler → API-Schlüssel, nur „Text zu Sprache“) kopieren, dann
  `pbpaste > ~/.elevenlabs && chmod 600 ~/.elevenlabs`. Der Schlüssel liegt nur auf dem Mac, nie im Repo.
- **Google Drive:** Ordner **„Dotchi Videos“** in „Meine Ablage“ anlegen und per Link freigeben
  („Jeder mit dem Link“, Betrachter). Mit Google Drive für Desktop kopiert der Generator jedes Video automatisch dorthin.
- **Metricool:** Marke **„Dotchi TV“** mit TikTok, Instagram und YouTube von `@dotchitv`. Die CSV importierst du,
  während oben rechts **Dotchi TV** ausgewählt ist – die Spalte „Brand name“ bleibt leer (`metricool.marke`),
  ein abweichender Name würde die Beiträge nur als Entwurf importieren.

## Wochen-Routine

| Wann | Wer | Was |
|---|---|---|
| jederzeit | du | Ideen in `IDEEN.md` eintragen (auf GitHub → Stift-Symbol) oder Claude schreiben |
| Fr | Cloud | 21 neue Vergleiche (3 pro Tag): zuerst offene Ideen aus `IDEEN.md`, dann nach `REDAKTIONSPLAN.md` |
| Fr–So früh | **du am Mac** | `~/Documents/dotchitv/woche.sh` – holt Inhalte und rendert **IQKnacker und Dotchi** |
| So früh | Cloud | plant die nächste Woche, legt `metricool_dotchi_….csv` und die Übersicht `postingplan_dotchi_….xlsx` in den Drive-Ordner |
| So | **du** | Metricool → Kalender → ⋮ → CSV importieren |

## Befehle

```bash
python3 generate.py                 # alle Vergleiche rendern, die noch kein Video haben
python3 generate.py --id 3 7        # nur diese (auch neu rendern)
python3 generate.py --vorschau      # Kontaktbögen aller Szenen ohne Stimme (keine Credits) → output/*_vorschau.png
python3 generate.py --ohne-stimme   # Video nur mit Musik und Effekten
python3 generate.py --liste         # Status: neu / gerendert / geplant / gepostet
python3 generate.py --doppelte      # ähnliche Vergleiche finden (gleiches Konzept, fast gleicher Titel)
python3 generate.py --uebersicht    # Excel mit allen Vergleichen + Ideen → output/uebersicht_dotchi.xlsx
python3 generate.py --drive         # fertige Videos (noch einmal) nach Google Drive kopieren
python3 generate.py --plan 7        # Posting-Plan + Metricool-CSV (lokal; 12:30, 17:30, 20:30 Uhr)
python3 generate.py --plan 7 --nur-drive   # dasselbe in der Cloud: fertig ist, was in drive_links.json steht
python3 generate.py --check         # Installation prüfen
python3 tools/logo.py               # Marke, Profilbilder (profilbild.png, profilbild_tiktok.png) und YouTube-Banner neu zeichnen
```

Ausgabe pro Vergleich in `output/`: `001_kaffee-to-go-vs-zuhause.mp4`, Vorschaubild `.png` und `_caption.txt`.
Gesprochene Sätze werden in `.stimmen-cache/` zwischengespeichert – neu rendern kostet keine Credits,
nur geänderte Sätze werden neu gesprochen.

## Dateien

| Datei | Inhalt | Wer ändert sie |
|---|---|---|
| `IDEEN.md` | deine Ideen für neue Vergleiche – werden freitags zuerst umgesetzt | du (auf GitHub) |
| `REDAKTIONSPLAN.md` | welches Thema wann: Mischung (70 % Geld), Tagesablauf, Trends, Saison, Qualitätsregeln | du / Claude |
| `TRENDS.md` | anstehende Trends und Anlässe – gemeinsam für Dotchi und IQKnacker | du / Cloud-Aufgaben |
| `vergleiche.json` | alle Videos (Szenen, Texte, Zahlen) | Cloud-Aufgabe / Hand |
| `config.json` | Stimme, Lautstärken, Themen-Farben, Hashtags, Uhrzeiten, Metricool | Hand |
| `geplant.json` | geplante Termine je ID – vergangene gelten als gepostet | `--plan` (Cloud) |
| `drive_links.json` | Dateiname → Google-Drive-Datei-ID | Cloud-Aufgabe |

Der Mac verändert beim Rendern keine dieser Dateien – `git pull` klappt deshalb immer ohne Konflikte.

## Aufbau eines Vergleichs (`vergleiche.json`)

```json
{
  "id": 11,
  "titel": "Kaffee to go vs. Zuhause",          // auch YouTube-Titel (+ #shorts), max. ~90 Zeichen
  "thema": "geld",                               // geld | zeit | essen | strom | technik | alltag
  "konzept": "kaffee-to-go-vs-zuhause",          // Thema + Blickwinkel – zweimal dasselbe gilt als doppelt
  "caption": "Kaffee to go oder Zuhause – was kostet dich wirklich mehr? ☕🏠",
  "hashtags": ["#kaffee"],                       // 1–2 eigene; Themen- und Kanal-Hashtags kommen dazu
  "fuss": "Beispielrechnung · 3,50 € vs. 0,30 € · 220 Arbeitstage",   // Annahmen bzw. Quelle, immer sichtbar
  "quellen": ["https://…"],                      // optional, für echte Zahlen Pflicht
  "szenen": [ … ]                                // eine Szene pro gesprochenem Satz
}
```

Jede Szene hat `typ` und `sprich` (der gesprochene Satz – ohne `*`). Die Szene dauert so lange wie der Satz.
Im Bildtext markiert `*so*` die Akzentfarbe. Szenentypen:

| Typ | Felder | Wirkung |
|---|---|---|
| `titel` | `zeilen`: `["Text", Größe]` oder `"Text"`, optional `verzoegerung`, `y` | große Zeilen nacheinander (Hook, Pointe) |
| `vs` | `kopf`, `links`/`rechts`: `emoji`, `name`, `farbe`, `wert`, optional `einheit` (Standard €), `dezimalen`, `unter`; optional `balken: true` | zwei Karten; mit `balken` zählen Balken und Zahlen hoch |
| `zahl` | `oben`, `wert`, optional `einheit`, `dezimalen`, `farbe`, `unten` (Zeilen), `unten_ab` | große hochzählende Zahl mit „Ching“ |
| `liste` | `zeilen`, optional `kopf`, `abstand`, `letzte_gross` | Rechenweg, Perspektiven, Kommentar-Frage |
| `urteil` | `links`/`rechts` (`emoji`, `name`), `gewinner`: `links`/`rechts`, optional `spruch`, `kopf`, `stempel` | „Dotchi? 🤔“ – Gewinner bekommt den Stempel **BESSERE WAHL**, Verlierer ❌ |

Für alle: `min` (Mindestdauer in s), `ching` (Zeitpunkt des Kassen-Sounds in s). Farben: `rot`, `gruen`, `gold`,
`blau`, `lila`, `orange`, `grau` oder Hex. Bewährter Ablauf: **Hook → Preis pro Stück (vs) → pro Jahr (vs mit
Balken) → Unterschied (zahl) → Urteil → Kommentar-Frage (liste)**. Einfache Emojis nutzen (keine
zusammengesetzten wie 👨‍🍳).

## Regeln für Inhalte

- **Zahlen stimmen immer.** Jede Rechnung wird nachgerechnet. Echte Daten nur mit Quelle und Stand
  (`fuss` + `quellen`), sonst klar als **Beispielrechnung** mit den Annahmen im `fuss`.
- **Keine Finanz- oder Anlageberatung**, keine Werbung, keine Markennamen schlechtmachen.
- **Tabu:** Politik, Wahlen, Kriege, Katastrophen, Kriminalität, Krankheiten, reale Personen.
- **Klares Urteil** – „kommt drauf an“ geht nicht viral. Auch positive Pointen sind okay („Lohnt sich absolut 😋“).
- **Gesprochener Text:** kurz, frech, natürlich. Kommazahlen ausschreiben („drei Euro fünfzig“), ganze Zahlen
  als Ziffern sind okay („770 Euro“). Am Ende immer eine Kommentar-Frage.
- In TikTok, YouTube und Instagram ist „KI-generiert“ aktiviert (KI-Stimme) – im CSV-Import automatisch.
