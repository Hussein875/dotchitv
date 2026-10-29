# Redaktionsplan – welches Thema wann

Leitlinie für die Freitags-Aufgabe (und für dich). **3 Videos pro Tag** (12:30, 17:30, 20:30 Uhr) = **21 pro Woche**.
Geld und Zahlen ziehen am meisten – deshalb liegt der Schwerpunkt dort.

## Phase 1: Start (die ersten 4 Wochen)

**Mischung pro Woche (21 Videos):**

| Bereich | Anteil | pro Woche | Beispiele |
|---|---|---|---|
| 💰 Geld im Alltag | 70 % | ~15 | Kaffee, Döner, Abos, Handyvertrag, Lieferdienst, Markenprodukte vs. Eigenmarke, Zigaretten-/Energy-Drink-Kosten, Fitnessstudio |
| 🚗 Mobilität & Wohnen (auch Geld) | in den 70 % enthalten | | Auto vs. Bahn vs. Rad, Deutschlandticket, Mieten vs. Kaufen, Heizen, Strom |
| ⏱️ Zeit | 10 % | ~2 | Bildschirmzeit, Pendeln, Warteschlangen, Schlaf |
| 🍔 Essen (mit Zahlen) | 10 % | ~2 | Selbst kochen vs. bestellen, Fast Food vs. Meal Prep |
| ⚡ Strom & Technik | 10 % | ~2 | Standby, Wasserkocher vs. Herd, Handy-Laden, Gaming-PC |

**Tagesablauf** (Faustregel, kein Muss):

| Uhrzeit | Was | Warum |
|---|---|---|
| 12:30 | leichter Geld-Klassiker (Kaffee, Snacks, Abos) | Mittagspause: schnell verständlich |
| 17:30 | Abwechslung (Zeit, Essen, Strom/Technik) oder Mobilität | Feierabend, Heimweg |
| 20:30 | stärkster Vergleich des Tages – große Zahlen, polarisierend (Mieten vs. Kaufen, Auto vs. Bahn) | Hauptzeit, meiste Kommentare |

**Formate mischen** (gegen Wiederholung, wichtig für YouTube): ca. 60 % „A vs. B“ (Kaffee-Muster),
25 % „Was kostet dich X im Jahr?“ (Döner-Muster mit Pointe), 15 % „Damals vs. heute“ oder „In Perspektive“
(„So lange arbeitest du dafür“). Gleiche Themen nie zwei Tage hintereinander.

## Qualität: Videos, die wir selbst schauen wollen

Jedes Video muss mindestens eins davon liefern – sonst wird es nicht gemacht:

- **Überraschende Zahl:** Am Ende weiß man etwas, das man vorher falsch geschätzt hätte („780 € im Jahr für Döner?!“).
- **Mehrwert:** ein Tipp oder eine Erkenntnis, die man direkt nutzen kann (Spartipp, bessere Wahl, Rechentrick).
- **Gesprächsstoff:** Man will es jemandem zeigen, markieren oder widersprechen.

**Nicht mehr:** Vergleiche, deren Ergebnis jeder schon kennt, ohne neue Zahl („Wasser ist billiger als Cola“),
reine Aufzählungen ohne Urteil, Themen, die wir schon hatten – auch nicht mit leicht anderem Titel.
Jeder Vergleich hat ein `konzept` (Thema + Blickwinkel, z. B. `doener-jahreskosten` vs. `doener-preis-damals-heute`);
`python3 generate.py --doppelte` meldet gleiche Konzepte und fast gleiche Titel.

## Wow-Faktor: Neues statt Alltags-Spartipps (mindestens 5 von 21 pro Woche)

Die Spar-Klassiker (Kaffee, Abos, Döner, Standby …) haben wir. Jede Woche brauchen wir **mindestens 5 Vergleiche mit einem
Fakt, den die meisten noch nicht kennen** – Typ „Wusstest du?“, belegt mit Quelle. Beispiele: Kino-Popcorn bezahlt das Kino,
eine Tasse Kaffee verbraucht mehr Wasser als zwei Duschen, eine KI-Frage braucht weniger Strom als 9 Sekunden Fernsehen.
Gute Quellen: Studien von Unis und Instituten, Statistikämter, Verbraucherzentralen, Geschäftsberichte, technische Berichte
von Firmen. **Höchstens 4 klassische Spar-Videos pro Woche.**

## Trends: mit der Zeit gehen (mindestens 5 von 21 pro Woche)

Was gerade passiert, bringt Abwechslung und Reichweite. Vor jeder Woche `TRENDS.md` lesen und per Websuche
prüfen, was in der Zielwoche ansteht oder gerade alle bespricht: neue Handys und Konsolen, große Game- und
Kino-Releases, Preiserhöhungen, Shopping-Tage, Feiertage, Wetter. Neue Trends in `TRENDS.md` eintragen.

- **Timing:** Trend-Videos in die Woche *vor* bzw. *um* den Anlass legen, das stärkste auf den Tag selbst um 20:30.
- **Mindestens 5 Trend-Videos pro Woche**, der Rest nach der Mischung oben. Trends zählen zur Geld-Quote, wenn es um Preise geht.
- **Echte Zahlen** (Preise, Termine) immer mit Quelle und Stand im `fuss` – bei Trends ändern sich Zahlen schnell.

## Serien (1 Serie pro Woche, 2–4 Teile)

Serien bringen Follower: Wer Teil 1 sieht, folgt, um Teil 2 nicht zu verpassen. Pro Woche **eine** Serie mit
2–4 Teilen, an **aufeinanderfolgenden Tagen um 20:30** (in vergleiche.json einfach an die passenden Stellen legen –
die Reihenfolge dort ist die Posting-Reihenfolge).

- Titel und Hook mit Teil-Nummer: `"titel": "Lebenskosten Teil 1/3: Kaffee"`, erste Szene z. B. `["*TEIL 1/3*", 60]`.
- Letzte Szene: Cliffhanger statt nur Frage – „Teil 2 morgen: das Handy. Folgen, sonst verpasst du's 👀“.
- Caption beginnt mit „Teil 1/3 –“. Jeder Teil hat ein eigenes `konzept` (z. B. `lebenskosten-kaffee`).

| Serie | Teile (Beispiele) |
|---|---|
| 💸 **Was dich ein Leben lang kostet** | Kaffee, Handy, Auto, Streaming – jeweils „ab 18 bis 67“ hochgerechnet (Beispielrechnung) |
| 🏙️ **Städte-Turnier** | München vs. Leipzig ✅ → Sieger gegen Hamburg → gegen Berlin … Kommentar-Frage: „Welche Stadt als Nächstes?“ |
| 💼 **Gehaltscheck** | Pflege ✅, Handwerk, Büro, Lehramt – immer Median brutto mit Quelle |
| 📆 **Damals vs. heute** | Döner ✅, Kino ✅, dann Benzin, Pizza, Miete – mit Jahr und Quelle |
| 🎯 **30-Tage-Spar-Challenge** | Woche 1–4: was ein kleiner Verzicht pro Woche bringt |

## Viral-Formate (bevorzugen – mindestens 7 von 21 pro Woche)

Ziel: Themen, die **jeder auf sich bezieht** und zu denen **jeder eine Meinung hat**.

| Format | Beispiele | Daten |
|---|---|---|
| 💼 Gehalts-Duelle | „Pflegekraft vs. Polizist – wer verdient mehr?“, „Azubi Bank vs. Azubi Handwerk“, „Lehrer vs. Ingenieur“ | Entgeltatlas der Bundesagentur für Arbeit (Median brutto, Stand angeben), Tarifverträge |
| 🏙️ Städte-Duelle | „Miete München vs. Leipzig“, „Döner Berlin vs. Hamburg“, „Deutschlandticket vs. Monatskarte früher in Stadt X“ | Mietspiegel/Statistik mit Quelle, sonst Beispielrechnung |
| 📆 Damals vs. heute | „Döner 2005 vs. heute“, „Kino, Benzin, Miete: 2000 vs. 2026“ | Destatis/Verbraucherpreise, seriöse Quellen – Jahr und Quelle in den Fuß |
| 🌍 Deutschland vs. Ausland | „Gehalt Deutschland vs. Schweiz“, „Benzin Deutschland vs. Polen“, „Döner Berlin vs. Istanbul“ | offizielle Statistiken, Wechselkurs mit Datum |
| ⏱️ Arbeitszeit-Rechner | „So lange arbeitest du mit Mindestlohn für ein iPhone / eine PS5 / eine Monatsmiete“ | Mindestlohn (aktueller Stand mit Quelle), Preise als Beispiel |

Regeln dafür: Gehälter immer als **Median brutto** mit Quelle und Stand, keine Einzelpersonen, kein Berufs-Bashing.
In der Urteils-Szene den Stempel anpassen: `"stempel": "VERDIENT MEHR"`, `"GÜNSTIGER"`, `"TEURER"` statt „BESSERE WAHL“. Nichts Politisches (Bürgergeld, Steuern-Debatten, Parteien).
Kommentar-Frage passend zum Identitäts-Thema: „Was verdienst du in deinem Job?“, „Aus welcher Stadt kommst du?“,
„Was hat dein erster Döner gekostet?“.

## Saison & Anlässe

| Zeitraum | Themen |
|---|---|
| November | Heizkosten (Heizung vs. Heizlüfter vs. Pulli 😏), **Black Friday (27.11.)**: „Rabatt oder Falle?“, Adventskalender |
| Dezember | Weihnachtsgeschenke-Budget, Glühwein auf dem Markt vs. selbst gemacht, Silvester-Feuerwerk vs. Party |
| Januar | Vorsätze: Fitnessstudio vs. zu Hause, Sparen vs. Konsum, „Dry January“ – was Verzicht spart |
| Frühling | Fahrrad statt Auto, Grillen: Fertig vs. selbst gemacht, Urlaubsplanung früh vs. last minute |
| Sommer | Klimaanlage vs. Ventilator, Freibad vs. Baggersee, Urlaub: Flug vs. Zug |
| Herbst | Herbstmode, Halloween-Kostüm kaufen vs. selbst gemacht, Heizperiode |

## Phase 2: nach 4 Wochen

Zahlen in Metricool/TikTok auswerten (Aufrufe, Zuschauzeit, Kommentare, Shares pro Thema und Format) –
die besten Themen ausbauen, schwache reduzieren. Diesen Plan dann anpassen.
