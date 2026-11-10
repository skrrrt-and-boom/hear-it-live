# Read playlist input; create nothing

Prefer complete playlist data already present in the conversation or an existing attachment. Reuse identified compositions when available. State the snapshot date; do not imply a Spotify refresh.

The optional local helper reads existing data and prints text without creating or changing files:

```sh
python3 -B /path/to/concert-finder/scripts/playlist.py 'https://open.spotify.com/playlist/PLAYLIST_ID'
```

It reads the existing private cache at `~/.cache/hear-it-live/playlists/` (or the configured XDG cache directory). Automatic reuse accepts a checking date up to seven calendar days old. `--input /path/to/existing.json` reads a user-selected snapshot instead; disclose its date. Python is optional: a host file reader can read an existing attachment directly. Do not write temporary exports or new caches.

If no complete input exists, try at most two direct public page fetches. Require an independently visible total and full coverage. One tested 340-track playlist exposed only 30 public-page links and 100 embed tracks through HTTP. If access is partial, explain it briefly and ask for existing complete data or an explicitly chosen subset. Do not retype hundreds of titles, guess missing entries or fall back to computer use.

This is not a Spotify-approved integration. Public visibility is not a policy exemption; Spotify's [Developer Policy](https://developer.spotify.com/policy) and [Developer Terms](https://developer.spotify.com/terms) include AI-use restrictions. Never extract session credentials, call private endpoints, download audio or publish personal playlist data.
