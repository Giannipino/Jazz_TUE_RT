#!/usr/bin/env python3
"""Sammelt Jazzkonzerte in Tübingen und Reutlingen aus festen Quellen und schreibt events.json.

Quellen (jede mit eigenem Leser, ein Fehler in einer Quelle stoppt die anderen nicht):
  - Jazzclub Tübingen           https://www.jazzclub-tuebingen.de/veranstaltungen-jazzclub
  - Jazz in der Mitte Reutlingen https://jazzindermitte.de/programm/?ical=1  (iCal-Feed)
  - Jazz im Prinz Karl          https://jipk.net/
  - Tübinger Jazz- & Klassiktage https://www.jazzklassiktage.de/<Jahr>/index.html
  - Sudhaus Tübingen (nur Jazz) https://www.sudhaus-tuebingen.de/programm/musik-konzerte.html
Zusätzlich werden Funde der wöchentlichen Claude-Websuche aus extra_events.json übernommen.

Exit-Code 2, wenn mindestens eine Quelle gescheitert ist (die anderen werden trotzdem aktualisiert,
die Termine der gescheiterten Quelle bleiben erhalten).
"""
import datetime as dt, json, re, sys, time, urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (jazz-kalender Tuebingen/Reutlingen; privater Kalender-Abgleich)"}
TODAY = dt.date.today()
WD = {"mo": 0, "di": 1, "mi": 2, "do": 3, "fr": 4, "sa": 5, "so": 6,
      "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3, "freitag": 4, "samstag": 5, "sonntag": 6}
MON = {"jan": 1, "feb": 2, "mär": 3, "mrz": 3, "mar": 3, "apr": 4, "mai": 5, "jun": 6, "jul": 7,
       "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12}
JAZZ_RE = re.compile(r"jazz|swing|big ?band|\bbebop|\bbe-bop|fusion|dixieland|bossa", re.I)
CANCEL_RE = re.compile(r"\b(abgesagt|entfällt|fällt aus|cancelled|canceled)\b", re.I)


def get(url, enc=None):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                raw = r.read()
            if enc:
                return raw.decode(enc, "replace")
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.decode("latin-1")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def mkdate(day, month, year=None, weekday=None):
    """Datum bilden; fehlendes oder offensichtlich falsches Jahr anhand des Wochentags korrigieren."""
    day, month = int(day), int(month)
    wd = WD.get((weekday or "").lower().strip(".,")) if weekday else None
    if year:
        year = int(year); year += 2000 if year < 100 else 0
        cands = [year, year + 1, year - 1]
    else:
        cands = [TODAY.year, TODAY.year + 1]
    valid = []
    for y in cands:
        try:
            valid.append(dt.date(y, month, day))
        except ValueError:
            pass
    if not valid:
        return None
    if wd is not None:
        for d in valid:
            if d.weekday() == wd:
                return d
    if not year:  # ohne Jahresangabe: nächstes Vorkommen (bis 2 Monate rückwirkend)
        for d in valid:
            if d >= TODAY - dt.timedelta(days=60):
                return d
    return valid[0]


def hhmm(h, m):
    return f"{int(h):02d}:{m or '00'}"


WDN = r"Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag|Mo|Di|Mi|Do|Fr|Sa|So"
DATE_RX = re.compile(r"(?:\b(" + WDN + r")\.?\s*,?\s*)?\b(\d{1,2})\.\s*(?:(\d{1,2})\.\s*(\d{4}|\d{2}(?!\d))?|([A-Za-zä]{3})[a-zä]*\.?\s+(\d{4}))")
TIME_RX = re.compile(r"\b(\d{1,2})(?:[:.](\d{2}))?\s*Uhr")


def find_date(text, default_year=None):
    """Erstes Datum in einem Text (\"Sa., 14.11.26\", \"Samstag, 21. Nov 2026\", \"Mi. 14.10.2026\")."""
    for m in DATE_RX.finditer(text):
        if m.group(3):
            month, year = int(m.group(3)), m.group(4) or default_year
        else:
            month, year = MON.get((m.group(5) or "").lower()), m.group(6)
        if not month or not 1 <= month <= 12:
            continue
        d = mkdate(m.group(2), month, year, m.group(1))
        if d:
            return d, m
    return None, None


def ev(source, date, start, title, location, url, note="", uid=None):
    title = clean(title)
    guess = start is None
    start = start or "20:00"
    m = re.search(r"\s*(geänderte Anfangszeit!?|neue Uhrzeit!?)", location or "")
    if m:
        location = location[:m.start()]; note = (note + "; Anfangszeit geändert").strip("; ")
    return {"uid": uid or f"jazz-{source}-{date.isoformat()}-{re.sub(r'[^a-z0-9]+', '-', title.lower())[:40].strip('-')}",
            "source": source, "date": date.isoformat(), "start": start, "title": title,
            "location": clean(location), "url": url, "note": note,
            "cancelled": bool(CANCEL_RE.search(title + " " + note)), "time_guess": guess}


# ---------------------------------------------------------------- Jazzclub Tübingen
def jazzclub():
    base = "https://www.jazzclub-tuebingen.de"
    out = []
    soup = BeautifulSoup(get(base + "/veranstaltungen-jazzclub"), "html.parser")
    for item in soup.select(".blog-item"):
        a = item.select_one("h2 a")
        if not a:
            continue
        intro = item.select_one(".article-introtext") or item
        first = clean(intro.find("p").get_text(" ") if intro.find("p") else intro.get_text(" "))
        d, m = find_date(first)
        if not d:
            continue
        rest = first[m.end():]
        t = TIME_RX.search(rest)
        start = hhmm(t.group(1), t.group(2)) if t else None
        venue = rest[t.end():] if t else rest
        venue = re.split(r"E\s?intritt|Karten|Tickets", venue)[0].strip(" ,")
        text = clean(intro.get_text(" "))
        note = "ausverkauft" if re.search(r"ausverkauft", text, re.I) else ""
        if re.search(r"\b(abgesagt|entfällt|fällt aus)\b", text, re.I):
            note = (note + "; abgesagt").strip("; ")
        out.append(ev("jazzclub", d, start, a.get_text(" "), venue or "Tübingen",
                      urljoin(base, a["href"]), note))
    return out


# ---------------------------------------------------------------- Jazz in der Mitte (iCal)
def jazz_in_der_mitte():
    from icalendar import Calendar
    cal = Calendar.from_ical(get("https://jazzindermitte.de/programm/?ical=1").encode("utf-8"))
    out = []
    for v in cal.walk("VEVENT"):
        s = v.decoded("DTSTART")
        if isinstance(s, dt.datetime):
            if s.tzinfo:
                from zoneinfo import ZoneInfo
                s = s.astimezone(ZoneInfo("Europe/Berlin"))
            d, start = s.date(), s.strftime("%H:%M")
        else:
            d, start = s, "20:00"
        title = str(v.get("SUMMARY", ""))
        loc = str(v.get("LOCATION", "")).replace(", Baden-Württemberg", "").replace(", Germany", "")
        out.append(ev("jidm", d, start, title, loc or "Jazzclub in der Mitte, Gartenstraße 36, Reutlingen",
                      str(v.get("URL", "https://jazzindermitte.de/programm/")),
                      uid="jazz-jidm-" + re.sub(r"[^A-Za-z0-9]+", "-", str(v.get("UID", title)))[:60]))
    return out


# ---------------------------------------------------------------- Jazz im Prinz Karl
def prinz_karl():
    base = "https://jipk.net/"
    home = BeautifulSoup(get(base), "html.parser")
    links = sorted({a["href"] for a in home.find_all("a", href=True)
                    if re.search(r"jipk\.net/20\d\d-[^/]+/?$", a["href"])})
    out = []
    for u in links:
        s = BeautifulSoup(get(u), "html.parser")
        main = s.find("main") or s.body
        h1 = main.find("h1")
        title = clean(h1.get_text(" ")) if h1 else u.rstrip("/").split("/")[-1]
        title = re.sub(r"^20\d\d\s*[–-]?\s*", "", title)
        lines = [clean(l) for l in main.get_text("\n").split("\n") if clean(l)]
        if h1 and lines and clean(h1.get_text(" ")) == lines[0]:
            lines = lines[1:]
        for i, l in enumerate(lines[:8]):
            d, m = find_date(l)
            if d:
                break
        if not d:
            continue
        block = " | ".join(lines[i:i + 4])
        times = TIME_RX.findall(block)
        start = hhmm(*times[0]) if times else None
        note = ("weitere Vorstellung: " + ", ".join(hhmm(*t) for t in times[1:])) if len(times) > 1 else ""
        venue = ""
        for part in re.split(r"\s*[|/]\s*", block[m.end():] if lines[i] in block else block):
            if part and not TIME_RX.search(part) and not DATE_RX.search(part) and len(part) > 3 \
                    and not re.search(r"concert|konzert|foto|vorverkauf", part, re.I):
                venue = part
                break
        if re.search(r"ausverkauft", " ".join(lines), re.I):
            note = (note + "; ausverkauft").strip("; ")
        out.append(ev("jipk", d, start, title, venue or "Tübingen", u, note))
        time.sleep(0.5)
    return out


# ---------------------------------------------------------------- Tübinger Jazz- & Klassiktage
def jazz_klassik_tage():
    out = []
    for year in (TODAY.year, TODAY.year + 1):
        base = f"https://www.jazzklassiktage.de/{year}/"
        try:
            html = get(base + "index.html", enc="latin-1")
        except Exception:
            continue
        soup = BeautifulSoup(html, "html.parser")
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not re.fullmatch(r"p?\d+\.htm", href) or href in seen:
                continue
            seen.add(href)
            title = clean(a.get_text(" "))
            detail = BeautifulSoup(get(base + href, enc="latin-1"), "html.parser")
            txt = clean(detail.body.get_text(" "))
            m = re.search(r"(Mo|Di|Mi|Do|Fr|Sa|So)\.?,?\s*(\d{1,2})\.(\d{1,2})\.,?\s*(?:ab\s*)?(\d{1,2})(?:[:.](\d{2}))?\s*Uhr\s*\|\s*", txt)
            if not m:
                continue
            d = mkdate(m.group(2), m.group(3), year, m.group(1))
            rest = txt[m.end():]
            first_word = (title.split() or [""])[0][:12]
            cut = rest.find(first_word) if first_word else -1
            venue = rest[:cut].strip(" |,") if 0 < cut <= 90 else rest[:60].rsplit(" ", 1)[0]
            out.append(ev("jkt", d, hhmm(m.group(4), m.group(5)), title or "Jazz- & Klassiktage",
                          venue, base + href, "Festival: Tübinger Jazz- & Klassiktage"))
            time.sleep(0.3)
    return out


# ---------------------------------------------------------------- Sudhaus (nur Jazz)
def sudhaus():
    base = "https://www.sudhaus-tuebingen.de/"
    soup = BeautifulSoup(get(base + "programm/musik-konzerte.html"), "html.parser")
    out = []
    rx = re.compile(r"(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s*/\s*(\d{1,2}):(\d{2})\s+(\d{1,2})\.\s*([A-Za-zäÄ]{3})\w*\.?\s+(\d{4})")
    for item in soup.select("section.event__item"):
        a = item.select_one("a.event__link")
        if not a:
            continue
        url = urljoin(base, a["href"])
        teaser = clean(item.select_one(".teaser").get_text(" ")) if item.select_one(".teaser") else ""
        main = BeautifulSoup(get(url), "html.parser")
        main = main.find(id="main") or main.body
        txt = clean(main.get_text(" "))
        g = re.search(r"Musik/Konzert\s*/\s*(.{2,60}?)\s{1}" + re.escape(clean(a.get_text(" "))[:15]), txt)
        genre = g.group(1) if g else ""
        if not (JAZZ_RE.search(genre) or JAZZ_RE.search(a.get_text(" ") + " " + teaser)):
            continue
        m = rx.search(txt)
        if not m:
            continue
        d = mkdate(m.group(4), MON.get(m.group(5).lower()[:3], 0) or 1, m.group(6))
        room = re.search(r"(Sudhaus[\w\s-]{0,30}?)\s+(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)", txt)
        loc = f"{room.group(1).strip() if room else 'Sudhaus'}, Hechinger Str. 203, Tübingen"
        out.append(ev("sudhaus", d, hhmm(m.group(2), m.group(3)), clean(a.get_text(" ")), loc, url,
                      f"Genre: {genre}" if genre else ""))
        time.sleep(0.5)
    return out


SOURCES = {"jazzclub": ("Jazzclub Tübingen", jazzclub),
           "jidm": ("Jazz in der Mitte Reutlingen", jazz_in_der_mitte),
           "jipk": ("Jazz im Prinz Karl", prinz_karl),
           "jkt": ("Tübinger Jazz- & Klassiktage", jazz_klassik_tage),
           "sudhaus": ("Sudhaus Tübingen", sudhaus)}


def norm(t):
    return set(w for w in re.findall(r"[a-zäöüß0-9]{4,}", t.lower()) if w not in {"jazz", "konzert", "tage", "klassik", "trio", "quartett", "quartet", "band"})


def dedupe(events):
    """Gleiches Konzert aus mehreren Quellen (z. B. Prinz Karl im Sudhaus) nur einmal aufnehmen."""
    prio = {k: i for i, k in enumerate(["jipk", "jazzclub", "jidm", "sudhaus", "jkt", "suche"])}
    events = sorted(events, key=lambda e: prio.get(e["source"], 9))
    kept = []
    for e in events:
        dup = next((k for k in kept if k["date"] == e["date"] and (norm(k["title"]) & norm(e["title"]))), None)
        if dup:
            if dup.get("time_guess") and not e.get("time_guess"):
                dup["start"], dup["time_guess"] = e["start"], False
            if re.search(r"ausverkauft", e.get("note", ""), re.I) and "ausverkauft" not in dup.get("note", ""):
                dup["note"] = (dup.get("note", "") + "; ausverkauft").strip("; ")
            names = SOURCES.get(e["source"], ("Websuche",))[0]
            if names not in dup.get("also", []):
                dup.setdefault("also", []).append(names)
        else:
            kept.append(e)
    return kept


def main(out="events.json", extra="extra_events.json"):
    try:
        old = json.load(open(out, encoding="utf-8")).get("events", [])
    except Exception:
        old = []
    new, failed = [], []
    for key, (name, fn) in SOURCES.items():
        try:
            evs = fn()
            old_future = [e for e in old if e["source"] == key and e["date"] >= TODAY.isoformat()]
            if not evs and old_future:
                raise RuntimeError("keine Termine gefunden (vorher %d) – Seite umgebaut?" % len(old_future))
            new += evs
            print(f"{name}: {len(evs)} Termine")
        except Exception as e:
            failed.append(f"{name}: {e}")
            new += [o for o in old if o["source"] == key and o["date"] >= TODAY.isoformat()]  # alte behalten
            print(f"FEHLER {name}: {e}")
    try:
        for x in json.load(open(extra, encoding="utf-8")).get("events", []):
            x.setdefault("source", "suche"); x.setdefault("cancelled", False)
            x.setdefault("uid", f"jazz-suche-{x['date']}-{re.sub(r'[^a-z0-9]+', '-', x['title'].lower())[:40]}")
            new.append(x)
    except FileNotFoundError:
        pass
    new = dedupe(new)
    uids = {e["uid"] for e in new}
    keep = [e for e in old if e["uid"] not in uids and e["date"] < TODAY.isoformat()
            and e["date"] >= (TODAY - dt.timedelta(days=180)).isoformat()]
    events = sorted(keep + new, key=lambda e: (e["date"], e["start"], e["title"]))
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"events": events}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"Gesamt: {len(events)} Termine ({len(keep)} vergangene behalten)")
    if failed:
        print("::warning::Quellen mit Fehlern: " + " | ".join(failed))
        sys.exit(2)


if __name__ == "__main__":
    main()
