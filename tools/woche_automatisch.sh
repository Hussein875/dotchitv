#!/bin/bash
# Läuft per launchd freitags und samstags um 21 Uhr (eingerichtet mit tools/automatik_einrichten.sh).
# Rendert die Woche nur einmal: Hat es seit Freitag 17 Uhr schon geklappt, passiert nichts.
LOG="$HOME/Library/Logs/dotchi_woche.log"
MERKER="$HOME/.dotchi_woche_ok"
melde() { osascript -e "display notification \"$1\" with title \"Dotchi & IQKnacker\" sound name \"Glass\"" >/dev/null 2>&1; }

# Beginn der aktuellen Woche = letzter Freitag 17:00 (vorher sind die neuen Texte noch nicht da)
freitag=$(date -v-"$(( ($(date +%u) + 2) % 7 ))"d +%Y-%m-%d)
if [ "$(date +%u)" = "5" ] && [ "$(date +%H)" -lt 17 ]; then freitag=$(date -v-7d +%Y-%m-%d); fi
if [ -f "$MERKER" ] && [ "$(cat "$MERKER")" \> "$freitag 17:00" ]; then
  echo "$(date): schon erledigt ($(cat "$MERKER"))" >> "$LOG"; exit 0
fi

for i in $(seq 1 30); do ping -c1 -t3 github.com >/dev/null 2>&1 && break; sleep 20; done  # auf Internet warten
melde "Rendern startet – Mac bitte anlassen 🎬"
echo "=== $(date) ===" >> "$LOG"
if caffeinate -dimsu "$HOME/Documents/dotchitv/woche.sh" >> "$LOG" 2>&1; then
  date +"%Y-%m-%d %H:%M" > "$MERKER"
  melde "✅ Fertig! Mac anlassen, bis Google Drive hochgeladen hat."
else
  melde "❌ Rendern fehlgeschlagen – Log: ~/Library/Logs/dotchi_woche.log (Screenshot an Claude)"
fi
