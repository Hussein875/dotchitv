#!/bin/bash
# Wochen-Routine am Mac (freitags/samstags): neue Inhalte holen und Videos rendern – für beide Kanäle.
# Die Videos landen automatisch im jeweiligen Google-Drive-Ordner; sonntags plant die Cloud die Woche.
#   Aufruf:  ~/Documents/dotchitv/woche.sh
set -e
for ordner in "$HOME/Documents/IQKnacker" "$HOME/Documents/dotchitv"; do
  if [ ! -d "$ordner" ]; then
    echo "– $ordner nicht gefunden, übersprungen"
    continue
  fi
  echo ""
  echo "=== $(basename "$ordner") ==="
  cd "$ordner"
  git pull --quiet
  source .venv/bin/activate
  pip install --quiet -r requirements.txt
  python3 generate.py
  deactivate
done
echo ""
echo "✓ Fertig. Mac anlassen, bis Google Drive alles hochgeladen hat (Symbol in der Menüleiste)."
