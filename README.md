# Jazz in Tübingen & Reutlingen – Kalender (ICS)

Jazzkonzerte in Tübingen und Reutlingen als abonnierbarer Kalender, automatisch aktualisiert.

**Quellen (täglich, per Skript `scrape.py`):**
- Jazzclub Tübingen – https://www.jazzclub-tuebingen.de (inkl. „Jazz im Studio“ im SWR Studio Tübingen)
- Jazz in der Mitte, Reutlingen – https://jazzindermitte.de (offizieller iCal-Feed)
- Jazz im Prinz Karl – https://jipk.net
- Tübinger Jazz- & Klassiktage – https://www.jazzklassiktage.de (komplettes Festivalprogramm)
- Sudhaus Tübingen – https://www.sudhaus-tuebingen.de (nur Konzerte mit Jazz-Genre)

**Wöchentlich (optional):** Claude sucht im Netz nach weiteren Jazzkonzerten → `extra_events.json`
(benötigt Repository-Secret `ANTHROPIC_API_KEY`, Anleitung in `AGENT.md`).

Doppelte Termine (z. B. Prinz-Karl-Konzert im Sudhaus) werden zusammengeführt.

**Abonnieren:** Google Kalender → Weitere Kalender → „Per URL“ → Raw-URL von `jazz-tuebingen-reutlingen.ics`.

Ohne Gewähr – maßgeblich sind die Angaben der Veranstalter.
