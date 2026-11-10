# Results files

After live research, write a UTF-8 JSON file. The renderer does not browse or verify facts. It refuses malformed or inconsistent reports. Work IDs connect events to the user's list; exact-match classification must already be supported by the programme.

```json
{
  "schema_version": 1,
  "title": "Your concert shortlist",
  "checked_at": "2026-11-10",
  "query": {
    "location": "Kraków, Poland",
    "radius_km": 50,
    "from": "2026-11-10",
    "to": "2026-11-30",
    "mode": "exact",
    "venue_scope": "churches",
    "works": [{"id": "bach-565", "composer": "Johann Sebastian Bach", "title": "Toccata and Fugue in D minor", "catalogue": "BWV 565"}]
  },
  "events": [],
  "sources_checked": [],
  "notes": ["No verified matches found in the sources checked."]
}
```

Each event contains:

- `id`, `title`, `date` (YYYY-MM-DD), `time` (HH:MM or null), `timezone` (IANA), optional `end_time` (same-day HH:MM or null).
- `venue`, `address`, `city`, `venue_type` (`church` or `other`), `event_type` (`concert` or `service`), `performers` (list), `admission` (explicit text, including “Not stated”).
- `match` (`exact`, `composer`, `nearby` or `lead`), `work_ids` (IDs from query; required for exact), `reason` (why it qualifies, or what is missing), `programme` (brief factual summary).
- `sources`: nonempty list of `{title, url, checked_at, evidence}`. Keep quotations short; a concise factual summary is usually better. Never copy a full programme essay or biography.
- Optional `distance_km`: verified straight-line distance; omit when not verified. Optional `notice`: relevant age restrictions, conflicting details or source caveats.

`sources_checked` contains `{title, url, outcome}` where outcome summarises what was checked or could not be accessed. Do not imply that an entire city was exhaustively searched. Dates must fit the query range; matched events need a known time. Service leads must be labelled. The renderer excludes leads/services/missing times from calendar export. Provide the IANA timezone; never guess it.

Run from any directory, replacing the example paths with the actual paths:

```sh
python3 /path/to/concert-finder/scripts/report.py results.json --output /path/to/concert-results
```

This writes `index.html`, `concerts.ics` and `results.json`. Open `index.html` in a browser, without hosting. Filters and source details work offline; source links and directions open external sites when clicked. Calendar entries use UTC converted from the venue timezone and have no invented duration. Printed dates are a saved research snapshot. Use the optional `--as-of YYYY-MM-DD` only to reproduce a historical fixture, never to mislabel current research.
