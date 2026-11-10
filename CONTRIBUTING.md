# Contributing

Keep the project small: improve source discovery, musical identity, evidence, accessibility or installation. Open an issue describing the request, source and observed outcome before proposing a new service dependency.

Use Python 3.10+ and the standard library. Run:

```sh
python3 -m unittest discover -s tests -v
python3 skills/concert-finder/scripts/report.py examples/krakow-bach.json --check
python3 tools/package.py
```

For research changes, compare the skill with ordinary assistant search on the same input. Record original URLs, checking date, false positives, omissions, latency and any unsupported tools. Do not treat schema validation as factual verification.

Keep `allow_implicit_invocation: false` and the Claude Code equivalent. Do not add always-loaded instructions, hooks, background tasks, telemetry, API credentials or a compulsory hosted service. Any added provider integration needs its current documented access and usage conditions checked first.

Do not commit personal searches, private playlists, credentials, full third-party webpages or photographs you cannot redistribute. The example contains limited event facts and links to their publishers; the software licence does not relicense the publishers' original content.
