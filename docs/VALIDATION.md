# Validation

This project is an assistant workflow plus deterministic local tools. It is not an autonomous crawler or a hosted events database. The host supplies browser controls, reasoning and web research. The static opening page prepares a request; the playlist helper verifies recorded row coverage; the renderer creates a programme and calendar.

## Automated checks

The suite covers overlapping capture batches, missing middle positions, changed totals, conflicting rows, unavailable items, repeated recordings, forged completeness flags, track-to-work provenance and research gaps. It also covers report invariants, unsafe links/HTML, timezone/calendar export, safe installation/replacement/removal and explicit-only configuration. It does not prove source truth or musical identity.

The updated suite has 44 passing tests locally on Python 3.15. CI runs Python 3.10 and 3.13. Browser checks cover request generation, invalid playlist links, reversed dates, client switching and copying, plus programme filters and source disclosures.

The opening page and programme were checked at a 390 px mobile viewport: neither had horizontal page overflow. Both browser views reported no console warnings or errors. The README images are screenshots of these working local pages; the synthetic playlist is visibly labelled.

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
8. **Spotify URL**: read visible browser rows, verify every position, retain the gaps, and avoid mistaking recommendations for playlist members.
9. **Read versus researched**: a fully captured playlist with only some works researched must display both counts accurately.

Before expanding functionality, compare against ordinary assistant search on the same request and record useful extra matches, source accuracy and research time. Public user testing and full cross-client live research are not claimed by the automated suite.
