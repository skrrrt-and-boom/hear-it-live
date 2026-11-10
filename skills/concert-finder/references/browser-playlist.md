# Reading a playlist in the browser

Use the host browser tool's documented UI APIs. This procedure does not provide a browser driver or authorise additional access. It works only when the host has browser controls and the requested playlist is visibly readable.

1. Open the supplied public playlist link. Record its name, displayed song count and check date. Canonicalise the URL to `https://open.spotify.com/playlist/ID`, removing share tracking parameters. Dismiss a cookie notice if it obstructs reading. Do not play tracks or sign in on the user's behalf merely to inspect a public list.
2. Inspect the visible playlist structure. It can be an ARIA **grid**, even when a native accessibility tree calls it a table. Read numbered track rows with title and artist names. A hovered play control can hide the row number visually; move the pointer or inspect the rendered number cell. Never infer track positions from the number of DOM rows.
3. Scroll the playlist's main pane in overlapping windows. Read newly loaded rows after placeholders resolve; previously rendered rows may disappear because the list is virtualised. Save each batch locally immediately. Capture only the minimal row fields below, not page state, cookies, cover images, audio or session data.
4. Merge batches using the helper. Duplicated observations of the same numbered row are fine; the same recording at different positions must remain separate. Conflicting titles/order or a changed total require a fresh capture. Reach the end, then fill every gap until positions `1..N` are accounted for. An inaccessible item is an explicitly unavailable row, never a fabricated title.
5. Run the final check with `--require-complete`. If access stalls, a login wall appears or the total cannot be established, stop claiming whole-playlist coverage. Report the observed count and gaps. Only use a narrower subset if the user explicitly chooses it.

Each JSON batch has this shape (the example is synthetic, not a real playlist):

```json
{
  "schema_version": 1,
  "playlist": {
    "url": "https://open.spotify.com/playlist/0000000000000000000000",
    "name": "Example playlist",
    "total_tracks": 2,
    "checked_at": "2026-11-10",
    "capture_method": "demo"
  },
  "tracks": [
    {"position": 1, "title": "Toccata and Fugue in D minor, BWV 565", "artists": ["Johann Sebastian Bach", "Example organist"]}
  ]
}
```

Real observations use `capture_method: "browser"`. A row you cannot read uses `status: "unavailable"`, a descriptive `title` such as “Unavailable item”, `artists: []` and a factual `reason`.

```sh
python3 /path/to/concert-finder/scripts/playlist.py batch-01.json batch-02.json --output capture.json
# Continue: merge the checkpoint with newly observed batches.
python3 /path/to/concert-finder/scripts/playlist.py capture.json batch-03.json --output capture.json --require-complete
```

The helper recomputes coverage; an input `coverage.complete` claim is not trusted. It makes no network calls. Completeness of positions is a structural check, not proof of title accuracy or stable Spotify access.

After capture, map every position to composition IDs or a reason it is unresolved/excluded. Keep multiple recordings of one work connected to that same work ID, while treating distinct movements/arrangements accurately. Catalogue extraction alone is not sufficient for ambiguous works. Read [results.md](results.md) when saving the final concert report. Capture coverage, work identification and concert research coverage are separate facts.
