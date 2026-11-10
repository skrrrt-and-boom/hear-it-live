#!/usr/bin/env python3
"""Validate researched concert facts and render a portable, offline shortlist.

No network requests, model calls or browser automation. Python 3.10+; stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from playlist import validate_capture


class ReportError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ReportError(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value


def day(value, label):
    try:
        require(isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)), f"{label}: use YYYY-MM-DD")
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ReportError(f"{label}: invalid calendar date") from exc


def url(value, label):
    text(value, label)
    p = urlparse(value)
    require(p.scheme in {"http", "https"} and bool(p.hostname) and not p.username and not p.password,
            f"{label}: use a public HTTP(S) URL without credentials")
    require(not any(c.isspace() or ord(c) < 32 for c in value), f"{label}: whitespace is not allowed")
    return value


def local_datetime(event, clock):
    require(isinstance(clock, str) and bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", clock)), "time: use HH:MM or null")
    zone = ZoneInfo(event["timezone"])
    naive = datetime.fromisoformat(event["date"] + "T" + clock)
    first, second = naive.replace(tzinfo=zone, fold=0), naive.replace(tzinfo=zone, fold=1)
    # Refuse ambiguous/nonexistent wall times rather than choosing the wrong instant.
    require(first.utcoffset() == second.utcoffset(), "ambiguous/nonexistent local time: confirm the event time")
    require(first.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == naive,
            "nonexistent local time")
    return first


def string_list(value, label):
    require(isinstance(value, list), f"{label} must be a list")
    for item in value:
        text(item, label)


def validate(data):
    require(isinstance(data, dict), "report must be an object")
    require(data.get("schema_version") == 1, "schema_version must be 1")
    text(data.get("title"), "title")
    checked = day(data.get("checked_at"), "checked_at")
    q = data.get("query")
    require(isinstance(q, dict), "query must be an object")
    text(q.get("location"), "query.location")
    start, end = day(q.get("from"), "query.from"), day(q.get("to"), "query.to")
    require(start <= end, "query.from must not follow query.to")
    radius = q.get("radius_km")
    require(type(radius) in (int, float) and math.isfinite(radius) and radius > 0, "radius_km must be positive")
    require(q.get("mode") in {"exact", "composer", "nearby"}, "unknown query mode")
    require(q.get("venue_scope") in {"churches", "all"}, "venue_scope must be churches or all")
    works = q.get("works")
    require(isinstance(works, list), "query.works must be a list")
    require(bool(works) or q["mode"] == "nearby", "exact/composer mode needs requested works")
    work_ids = set()
    for w in works:
        require(isinstance(w, dict), "work must be an object")
        for key in ("id", "composer", "title"):
            text(w.get(key), "work." + key)
        require(w["id"] not in work_ids, "duplicate work ID")
        work_ids.add(w["id"])
        if "catalogue" in w:
            text(w["catalogue"], "work.catalogue")
    if 'playlist' in data:
        capture = validate_capture(data['playlist'], require_complete=True)
        require(day(capture['playlist']['checked_at'], 'playlist checked_at') <= checked, 'playlist check is after report check')
        mapping = data.get('track_work_map')
        require(isinstance(mapping, list), 'playlist reports need track_work_map')
        positions, mapped_works = set(), set()
        for item in mapping:
            require(isinstance(item, dict), 'track mapping must be an object')
            position = item.get('position')
            require(type(position) is int and 1 <= position <= capture['playlist']['total_tracks'], 'unknown mapped track position')
            require(position not in positions, 'duplicate mapped track position')
            positions.add(position)
            string_list(item.get('work_ids'), 'mapped work_ids')
            require(set(item['work_ids']) <= work_ids, 'mapping references unknown work')
            require(item.get('status') in {'mapped', 'unresolved', 'excluded'}, 'unknown mapping status')
            require(bool(item['work_ids']) == (item['status'] == 'mapped'), 'only mapped tracks have work IDs')
            if item['status'] != 'mapped':
                text(item.get('reason'), 'unmapped track reason')
            mapped_works.update(item['work_ids'])
        require(positions == set(range(1, capture['playlist']['total_tracks'] + 1)), 'account for every playlist track in track_work_map')
        require(mapped_works == work_ids, 'every requested work must come from a playlist track')
        researched = data.get('researched_work_ids')
        string_list(researched, 'researched_work_ids')
        require(len(researched) == len(set(researched)) and set(researched) <= work_ids, 'unknown/duplicate researched work')
    events = data.get("events")
    require(isinstance(events, list), "events must be a list")
    ids, occurrences = set(), set()
    for e in events:
        require(isinstance(e, dict), "event must be an object")
        for key in ("id", "title", "venue", "address", "city", "timezone", "reason", "programme", "admission"):
            text(e.get(key), "event." + key)
        require(e["id"] not in ids, "duplicate event ID")
        ids.add(e["id"])
        require(start <= day(e.get("date"), "event.date") <= end, "event date is outside the search window")
        require(e.get("match") in {"exact", "composer", "nearby", "lead"}, "unknown match type")
        require(e.get("venue_type") in {"church", "other"}, "unknown venue_type")
        require(e.get("event_type") in {"concert", "service"}, "unknown event_type")
        require(q["venue_scope"] != "churches" or e["venue_type"] == "church", "non-church event in churches-only query")
        require(e["match"] == "lead" or e["event_type"] == "concert", "services must be separate leads")
        require(q["mode"] != "exact" or e["match"] in {"exact", "lead"}, "broader result in strict exact mode")
        require(q["mode"] != "composer" or e["match"] != "nearby", "nearby result in composer mode")
        string_list(e.get("work_ids"), "event.work_ids")
        require(len(e["work_ids"]) == len(set(e["work_ids"])), "duplicate matched work ID")
        require(set(e["work_ids"]) <= work_ids, "event references an unknown work ID")
        require(e["match"] != "exact" or bool(e["work_ids"]), "exact match needs a requested work ID")
        if 'playlist' in data:
            require(set(e['work_ids']) <= set(data['researched_work_ids']), 'matched work is not in researched_work_ids')
        try:
            ZoneInfo(e["timezone"])
        except ZoneInfoNotFoundError as exc:
            raise ReportError("unknown timezone; install tzdata if your system has no IANA database") from exc
        require("time" in e, "time must be HH:MM or null")
        require(e["time"] is not None or e["match"] == "lead", "a matched event needs a confirmed start time")
        if e["time"] is not None:
            begin = local_datetime(e, e["time"])
            if e.get("end_time") is not None:
                require(local_datetime(e, e["end_time"]) > begin, "end_time must follow start on the same day")
        else:
            require(e.get("end_time") is None, "end_time requires a start time")
        occurrence = (e["date"], e["time"], e["venue"].casefold().strip())
        require(occurrence not in occurrences, "duplicate date/time/venue; merge the announcements")
        occurrences.add(occurrence)
        string_list(e.get("performers"), "performers")
        distance = e.get("distance_km")
        if distance is not None:
            require(type(distance) in (int, float) and math.isfinite(distance) and 0 <= distance <= radius,
                    "verified distance must fit the search radius")
        if "notice" in e:
            text(e["notice"], "notice")
        sources = e.get("sources")
        require(isinstance(sources, list) and bool(sources), "every event needs supporting sources")
        for source in sources:
            require(isinstance(source, dict), "source must be an object")
            for key in ("title", "evidence"):
                text(source.get(key), "source." + key)
            url(source.get("url"), "source.url")
            require(day(source.get("checked_at"), "source.checked_at") <= checked, "source check is after report check")
    require(isinstance(data.get("sources_checked"), list), "sources_checked must be a list")
    for source in data["sources_checked"]:
        require(isinstance(source, dict), "checked source must be an object")
        text(source.get("title"), "checked source title")
        text(source.get("outcome"), "checked source outcome")
        url(source.get("url"), "checked source URL")
    string_list(data.get("notes", []), "notes")
    return data


def esc(value):
    return html.escape(str(value), quote=True)


def link(href, label, cls=""):
    return f'<a class="{cls}" href="{esc(url(href, "link"))}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def date_label(value):
    d = date.fromisoformat(value)
    return f"{d.day} {d.strftime('%b %Y')}"


def render(data, as_of=None):
    validate(data)
    q = data["query"]
    works = {w["id"]: w for w in q["works"]}
    rows = []
    for e in sorted(data["events"], key=lambda x: (x["date"], x["time"] or "99:99")):
        exact = e["match"] == "exact"
        badge = {"exact": "Exact work match", "composer": "Composer match", "nearby": "Nearby concert", "lead": "Unconfirmed lead"}[e["match"]]
        matched = ''.join(f'<li><span class="composer">{esc(works[i]["composer"])}</span> {esc(works[i]["title"])} <span class="catalogue">{esc(works[i].get("catalogue", ""))}</span></li>' for i in e["work_ids"])
        evidence = ''.join(f'<div class="source">{link(s["url"], s["title"] + " ↗")}<p>{esc(s["evidence"])}</p><small>Checked {esc(date_label(s["checked_at"]))}</small></div>' for s in e["sources"])
        maps = "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query": e["address"] + ", " + e["city"]})
        distance = f'{e["distance_km"]:g} km straight-line' if e.get("distance_km") is not None else "Distance not verified"
        notice = f'<p class="notice">{esc(e["notice"])}</p>' if e.get("notice") else ""
        d = date.fromisoformat(e["date"])
        rows.append(f'''<article class="event" data-kind="{esc(e['match'])}">
<div class="date"><span>{d.strftime('%b').upper()}</span><strong>{d.day:02d}</strong><span>{esc(e['time'] or 'Time TBA')}</span></div>
<div class="event-main"><div class="eyebrow"><span class="badge {'exact' if exact else 'lead'}">{badge}</span><span>{esc(e['admission'])}</span></div>
<h2>{esc(e['title'])}</h2><p class="performers">{esc(' · '.join(e['performers']) or 'Performers not announced')}</p>
<p class="venue">{esc(e['venue'])} <span>· {esc(e['city'])}</span></p>
<ul class="works">{matched}</ul>{notice}
<div class="actions">{link(e['sources'][0]['url'], 'Announcement ↗', 'primary-link')}{link(maps, 'Directions ↗')}</div>
<details><summary>Programme & details</summary><p class="reason">{esc(e['reason'])}</p><p>{esc(e['programme'])}</p><p>{esc(e['address'])} · {esc(e['timezone'])} · {esc(distance)}</p>{evidence}</details></div></article>''')
    exact_count = sum(e["match"] == "exact" for e in data["events"])
    lead_count = sum(e["match"] == "lead" for e in data["events"])
    matching_count = sum(e["match"] != "lead" for e in data["events"])
    selected = ''.join(f'<li><span>{esc(w["composer"])}</span>{esc(w["title"])} <b>{esc(w.get("catalogue", ""))}</b></li>' for w in q["works"])
    checked_sources = ''.join(f'<li>{link(s["url"], s["title"] + " ↗")}<p>{esc(s["outcome"])}</p></li>' for s in data["sources_checked"])
    notes = ''.join(f'<li>{esc(n)}</li>' for n in data.get("notes", []))
    playlist_context = '<span class="context-label">Your repertoire</span><strong>Personal work list</strong>'
    coverage_detail = ''
    if 'playlist' in data:
        capture = validate_capture(data['playlist'], require_complete=True)
        p = capture['playlist']
        demo = p['capture_method'] == 'demo'
        playlist_name = esc(p['name']) if demo else link(p['url'], p['name'] + ' ↗')
        playlist_context = f'<span class="context-label">{"Sample playlist · demonstration" if demo else "From your Spotify playlist"}</span><strong>{playlist_name}</strong><span>{p["total_tracks"]} of {p["total_tracks"]} tracks read · {len(works)} works</span><span>Playlist snapshot · {esc(date_label(p["checked_at"]))}</span>'
        unresolved = sum(m['status'] == 'unresolved' for m in data['track_work_map'])
        excluded = sum(m['status'] == 'excluded' for m in data['track_work_map'])
        researched_count = len(data['researched_work_ids'])
        coverage_detail = f'<p>{researched_count} of {len(works)} works researched · {unresolved} tracks unresolved · {excluded} excluded.</p>'
        gaps = ''.join(f'<li>Track {m["position"]}: {esc(m["reason"])}</li>' for m in data['track_work_map'] if m['status'] != 'mapped')
        unsearched = ''.join(f'<li>Not researched: {esc(w["composer"])} — {esc(w["title"])}</li>' for w in q['works'] if w['id'] not in data['researched_work_ids'])
        coverage_detail += f'<ul>{gaps}{unsearched}</ul>' if gaps or unsearched else ''
    today = as_of or date.today()
    stale = '<p class="archive">Archived search: these dates have passed. This is a saved example, not a current events feed.</p>' if day(q["to"], "to") < today else ''
    template = (Path(__file__).resolve().parents[1] / "assets" / "report.html").read_text(encoding="utf-8")
    values = {
        "TITLE": esc(data["title"]), "LOCATION": esc(q["location"]), "WINDOW": esc(date_label(q["from"]) + " — " + date_label(q["to"])),
        "RADIUS": f'{q["radius_km"]:g}', "CHECKED": esc(date_label(data["checked_at"])), "MODE": esc(q["mode"]),
        "WORKS": selected or '<li>No repertoire restriction</li>', "ROWS": ''.join(rows), "MATCHES": str(matching_count),
        "EXACT": str(exact_count), "LEADS": str(lead_count), "TOTAL": str(len(data["events"])),
        "SOURCE_COUNT": str(len(data["sources_checked"])), "SOURCES": checked_sources, "NOTES": notes,
        "ARCHIVE": stale, "EMPTY": '' if data["events"] else '<p class="empty">No verified concerts found in the sources checked. Try a wider date range or radius.</p>',
        "SCOPE": "Church concerts" if q["venue_scope"] == "churches" else "All venues",
        "PLAYLIST_CONTEXT": playlist_context, "COVERAGE_DETAIL": coverage_detail,
        "END_DATE": esc(q['to']),
    }
    # One substitution pass: user-provided text can never become a template directive.
    return re.sub(r"\[\[([A-Z_]+)\]\]", lambda m: values[m.group(1)], template)


def ics_escape(value):
    return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '').replace(';', '\\;').replace(',', '\\,')


def fold_ics(line):
    result, part = [], ''
    for char in line:
        if len((part + char).encode('utf-8')) > 75:
            result.append(part)
            part = ' '
        part += char
    result.append(part)
    return '\r\n'.join(result)


def calendar(data):
    validate(data)
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Hear It Live//Concert Finder//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH']
    for e in data['events']:
        if e['match'] == 'lead' or e['event_type'] != 'concert' or e['time'] is None:
            continue
        source = e['sources'][0]['url']
        uid = hashlib.sha256((source + e['date'] + (e['time'] or '')).encode()).hexdigest()[:24]
        stamp = data['checked_at'].replace('-', '') + 'T000000Z'
        start = local_datetime(e, e['time']).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        lines += ['BEGIN:VEVENT', f'UID:{uid}@hear-it-live', f'DTSTAMP:{stamp}', f'DTSTART:{start}']
        if e.get('end_time'):
            end = local_datetime(e, e['end_time']).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            lines.append('DTEND:' + end)
        lines += ['SUMMARY:' + ics_escape(e['title']), 'LOCATION:' + ics_escape(e['venue'] + ', ' + e['address'] + ', ' + e['city']),
                  'DESCRIPTION:' + ics_escape(e['reason'] + '\n' + e['admission'] + '\nChecked: ' + data['checked_at'] + '\n' + source),
                  'URL:' + source, 'END:VEVENT']
    lines.append('END:VCALENDAR')
    return '\r\n'.join(fold_ics(line) for line in lines) + '\r\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path, help='JSON facts produced by live research')
    p.add_argument('--output', type=Path, default=Path('concert-results'))
    p.add_argument('--as-of', help='reproduce an archived example as of YYYY-MM-DD')
    p.add_argument('--check', action='store_true', help='validate without writing output')
    args = p.parse_args()
    try:
        data = validate(json.loads(args.input.read_text(encoding='utf-8')))
        as_of = day(args.as_of, 'as-of') if args.as_of else None
        if args.check:
            print(f'Valid report: {len(data["events"])} events; {len(data["query"]["works"])} requested works')
            return 0
        # Render fully before touching the output directory.
        page, ics = render(data, as_of), calendar(data)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'index.html').write_text(page, encoding='utf-8')
        (args.output / 'concerts.ics').write_bytes(ics.encode('utf-8'))
        (args.output / 'results.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Report: {(args.output / "index.html").resolve()}')
        print(f'Calendar: {(args.output / "concerts.ics").resolve()}')
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Cannot create report: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
