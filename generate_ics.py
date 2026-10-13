#!/usr/bin/env python3
"""Erzeugt jazz-tuebingen-reutlingen.ics aus events.json (RFC 5545)."""
import json, sys, datetime as dt

VTZ = """BEGIN:VTIMEZONE
TZID:Europe/Berlin
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""


def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    b = line.encode("utf-8"); out = []
    while len(b) > 75:
        cut = 75 if not out else 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1  # nicht mitten im UTF-8-Zeichen trennen
        out.append(b[:cut].decode()); b = b[cut:]
    out.append(b.decode())
    return "\r\n ".join(out)


NAMES = {"jazzclub": "Jazzclub Tübingen", "jidm": "Jazz in der Mitte Reutlingen", "jipk": "Jazz im Prinz Karl",
         "jkt": "Tübinger Jazz- & Klassiktage", "sudhaus": "Sudhaus Tübingen", "suche": "Websuche"}


def main(src="events.json", dst="jazz-tuebingen-reutlingen.ics"):
    with open(src, encoding="utf-8") as f:
        d = json.load(f)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//jazz-ics//Jazz Tuebingen Reutlingen//DE",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:Jazz Tübingen & Reutlingen", "X-WR-TIMEZONE:Europe/Berlin",
         "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"] + VTZ.split("\n")
    for e in d["events"]:
        day = dt.date.fromisoformat(e["date"])
        h, m = map(int, e["start"].split(":"))
        start = dt.datetime(day.year, day.month, day.day, h, m)
        end = start + dt.timedelta(minutes=150)
        src_name = NAMES.get(e["source"], e["source"])
        title = ("ABGESAGT: " if e.get("cancelled") else "") + e["title"]
        desc = [f"Quelle: {src_name}"]
        if e.get("also"): desc.append("Auch gelistet bei: " + ", ".join(e["also"]))
        if e.get("note"): desc.append(f"Hinweis: {e['note']}")
        if e.get("time_guess"): desc.append("Uhrzeit nicht angegeben – bitte auf der Webseite prüfen.")
        if e["source"] == "suche": desc.append("Per Websuche gefunden – Angaben bitte prüfen.")
        desc.append(f"Details: {e['url']}")
        L += ["BEGIN:VEVENT",
              f"UID:{e['uid']}@jazz-ics",
              f"DTSTAMP:{now}",
              f"DTSTART;TZID=Europe/Berlin:{start:%Y%m%dT%H%M%S}",
              f"DTEND;TZID=Europe/Berlin:{end:%Y%m%dT%H%M%S}",
              fold("SUMMARY:" + esc(title)),
              fold("LOCATION:" + esc(e.get("location") or "")),
              fold("DESCRIPTION:" + esc("\n".join(desc))),
              fold("CATEGORIES:" + esc(src_name)),
              fold(f"URL:{e['url']}"),
              "STATUS:" + ("CANCELLED" if e.get("cancelled") else "CONFIRMED"),
              "TRANSP:OPAQUE", "END:VEVENT"]
    L.append("END:VCALENDAR")
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(L) + "\r\n")
    print(f"{len(d['events'])} Termine -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:])
