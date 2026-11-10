# Validation

This project is an assistant workflow plus deterministic local tools. It is not an autonomous crawler or a hosted events database. Concert searches use web search/direct page and PDF fetching, with computer use prohibited by the workflow instructions. The static opening page prepares a request; local helpers validate and reuse complete playlist snapshots; the renderer creates a programme and calendar.

## Automated checks

The suite covers overlapping capture batches, missing middle positions, changed totals, conflicting rows, unavailable items, repeated recordings, forged completeness flags, track-to-work provenance and research gaps. It also covers report invariants, unsafe links/HTML, timezone/calendar export, safe installation/replacement/removal and explicit-only configuration. It does not prove source truth or musical identity.

The updated suite has 54 passing tests locally on Python 3.15. CI runs Python 3.10 and 3.13. Cache tests cover canonical URL lookup, missing/partial snapshots, expiry by checking date, future dates, identity mismatch, tampered coverage, private file permissions and exclusion of previous concert history. A report test distinguishes the playlist snapshot date from the concert-announcement checking date. These tests do not prove that a host enforces skill instructions as a technical tool restriction.

The v0.2 opening page and programme were checked at a 390 px mobile viewport: neither had horizontal page overflow. Both browser views reported no console warnings or errors. Request generation, invalid links/dates, client switching/copying, programme filters and source disclosures were checked. The README images show that interface; the synthetic playlist is visibly labelled. The subsequent no-computer-use update changes workflow/request instructions, not the visual layout.

## Faster repeat searches

Noninteractive HTTP checks of the previously tested 340-track public playlist completed in approximately 0.6 seconds for the public page and 0.5 seconds for its embed in one trial. They exposed only 30 public-page track links and 100 embed items respectively. They are not complete imports and do not establish a universal limit or a guaranteed latency.

The complete 340-track capture from the earlier browser trial can be reused locally, avoiding a new UI pass. The cache retains and reports the original checking date rather than pretending to refresh Spotify. No browser or desktop interaction is needed to load that file or research concert announcements. A missing complete snapshot must produce an input gap rather than an automatic computer-use fallback.

## Public playlist access trial — 10 November 2026

The interactive browser opened a user-supplied public playlist without signing in. Its header reported 340 songs, about 23 hours. The initial view exposed 25 numbered rows. Scrolling produced virtualised windows; a set of observed positions was compared with `1..340`. The first pass left seven positions missing, which were filled by scrolling back. The final set had 340 positions and no gaps, including the final track.

That trial establishes full numbered-row access for that playlist at that time. It does not establish universal Spotify access, a supported API, platform approval, musical work identification for every track, or a completed concert search across all 340 tracks. No personal playlist capture is included in the repository.

The v0.2 implementation was also checked against a fresh real capture: visible titles and artist names were saved in overlapping local batches, gaps were filled on a return pass, and `playlist.py --require-complete` verified 340/340 readable tracks. Those personal batches remain outside the repository. The separate automated 340-position fixture is synthetic.

## Real research snapshot — 10 November 2026

Input: Bach BWV 565, BWV 659 and BWV 572; church concerts in Kraków, 10–30 November 2026. The assistant searched original organiser/venue announcements. The evidence-backed work-list fixture is `examples/krakow-bach.json`. The updated `examples/playlist-concerts.json` combines those facts with a clearly labelled synthetic four-track playlist and track-to-work mapping. Its generated programme is `examples/report/index.html`. Screenshots show the actual UI, not a simulated assistant conversation.

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
8. **Spotify URL**: load a complete saved snapshot or verify direct-fetch completeness. If unavailable, report the gap; do not launch browser automation.
9. **Read versus researched**: a fully captured playlist with only some works researched must display both counts accurately.

Before expanding functionality, compare against ordinary assistant search on the same request and record useful extra matches, source accuracy and research time. Public user testing and full cross-client live research are not claimed by the automated suite.
