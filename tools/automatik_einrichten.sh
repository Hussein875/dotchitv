#!/bin/bash
# Einmalig am Mac ausführen:  ~/Documents/dotchitv/tools/automatik_einrichten.sh
# Danach rendert der Mac jeden Freitag um 21 Uhr von selbst (Samstag 21 Uhr als zweiter Versuch).
# War der Mac zu dem Zeitpunkt aus oder zugeklappt, holt er es beim nächsten Aufwachen nach.
set -e
PLIST="$HOME/Library/LaunchAgents/de.dotchitv.woche.plist"
SKRIPT="$HOME/Documents/dotchitv/tools/woche_automatisch.sh"
chmod +x "$SKRIPT" "$HOME/Documents/dotchitv/woche.sh"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>de.dotchitv.woche</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$SKRIPT</string></array>
  <key>StartCalendarInterval</key><array>
    <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>6</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "✓ Automatik eingerichtet: freitags 21 Uhr (samstags 21 Uhr als Nachholtermin)."
echo "Damit der Mac dafür auch aus dem Ruhezustand aufwacht (Passwort nötig):"
sudo pmset repeat wakeorpoweron FS 20:55:00 && echo "✓ Mac wacht freitags und samstags um 20:55 auf (am Netzteil, Deckel offen)."
