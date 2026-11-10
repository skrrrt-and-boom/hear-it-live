# Validation

This project is an assistant workflow plus deterministic local output tools. It is not an autonomous crawler or a hosted events database. The host supplies reasoning, live search and page access; the renderer supplies a consistent local report and calendar.

## Automated checks

The test suite covers report invariants, unsafe link/HTML handling, date and timezone conversion, calendar escaping and UTF-8 line folding, missing times, strict-mode exclusions, empty results, safe installation/replacement/removal, and explicit-only configuration in both packages. It does not prove that an event is real or that a musical work was correctly identified.

Release checks: 26 tests passed locally on Python 3.15. The rendered report was inspected in a browser: Matches, Leads and All showed 2, 1 and 3 results respectively; programme/source disclosures expanded correctly. The 390 px mobile layout had no page overflow or browser warnings/errors. The repository's CI additionally runs Python 3.10 and 3.13.

## Real research snapshot — 10 November 2026

Input: Bach BWV 565, BWV 659 and BWV 572; church concerts in Kraków, 10–30 November 2026. The assistant searched and read the organiser's calendar and individual announcements. The evidence-backed output is `examples/krakow-bach.json`. Its generated local report is `examples/report/index.html`; the README screenshots show that report, not a simulated chat interface.

The organiser announced:

- Xaver Varnus, 14 November, 20:00, St Mary's Basilica: BWV 565 and BWV 659, free admission. The source also specifies an age restriction, reproduced in the report.
- Hanna Zalewska, 17 November, 19:00, Divine Mercy Church at pl. Raczyńskiego 1: BWV 572 and BWV 659. Admission is not stated on the inspected event page and stays unknown.
- The Pijarska church's seasonal announcement lists a 15 November recital, but its inspected text does not establish the requested works or start time. It remains a lead and is excluded from calendar export.

The fixture links to each source and records the check date. It is a snapshot; it does not claim current availability after those dates or prove that these events are absent from every other listing service. No personal account, playlist or location history is included.

## Repeatable manual trials

1. **Exact work**: confirm each claimed work in the relevant programme, not a performer biography.
2. **False positive**: request BWV 54 and ensure a page mentioning BWV 544 is not accepted.
3. **Different recording performer**: a requested work performed by another artist should qualify.
4. **Small town**: choose a place outside the examples; discover new primary sources rather than returning only known-city inventory.
5. **Unknown programme**: retain as a lead, never an exact match.
6. **No results**: show the source trail and gaps without claiming no concerts exist.
7. **Unavailable browsing**: explain the missing capability rather than generating events from memory.
8. **Spotify URL only**: explain the missing importer and ask for independently supplied work names; no partial playlist scan.

Before expanding functionality, compare against ordinary assistant search on the same request and record useful extra matches, source accuracy and research time. Public user testing and full cross-client live research are not claimed by the automated suite.
