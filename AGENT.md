# Anleitung für die wöchentliche Websuche (Claude)

Die festen Quellen (Jazzclub Tübingen, Jazz in der Mitte Reutlingen, Jazz im Prinz Karl, Tübinger
Jazz- & Klassiktage, Sudhaus) liest `scrape.py` täglich selbst. Deine Aufgabe: **zusätzliche** Jazzkonzerte
in Tübingen und Reutlingen (und direkter Umgebung) für die nächsten 6 Monate finden.

1. **Suchen** (WebSearch/WebFetch), z. B.:
   - „Jazz Konzert Tübingen <Monat Jahr>“, „Jazz Reutlingen <Monat Jahr>“, „Jazzfestival Tübingen/Reutlingen“
   - SWR Studio Tübingen (öffentliche Konzerte), Franz.K Reutlingen, Kulturzentrum franz.K, LTT, Westspitze,
     Club Voltaire, C. Bechstein Centrum Tübingen, Musikschulen, Kirchen (Jazz-Gottesdienste), Open-Air-Reihen.
   - Veranstaltungskalender: tuebingen.de, reutlingen.de, tagblatt.de, gea.de, regioactive.de, mvp.de.
   Nur Jazz und eng Verwandtes (Swing, Big Band, Fusion, Latin Jazz, Jazz-Jam). Kein Pop/Rock/Klassik.

2. **Prüfen:** Jeder Termin braucht Datum, Uhrzeit (falls bekannt), Ort und eine Quell-URL, die Du selbst
   geöffnet hast. Nichts erfinden oder raten. Termine, die schon in `events.json` stehen (gleiches Datum,
   ähnlicher Titel) oder von den festen Quellen stammen, NICHT erneut eintragen.

3. **`extra_events.json` pflegen** – Format:
   `{"events": [{"date": "YYYY-MM-DD", "start": "HH:MM", "title": "...", "location": "...", "url": "...", "note": "..."}]}`
   - Vergangene Einträge entfernen; bestehende Einträge behalten, wenn sie noch stimmen, sonst korrigieren.
   - Abgesagte Konzerte: `"cancelled": true` setzen.

4. **Nicht selbst committen.** Bericht in `LETZTER_LAUF.md`: neue/geänderte/entfernte Einträge mit Quelle,
   sowie Funde, bei denen Du unsicher warst (nicht eingetragen).
