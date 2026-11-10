# Playlist input without computer use

Use a playlist link and a location, with a complete saved playlist whenever possible. Concert-finder searches must not use UI automation. Do not load the legacy browser-import procedure as a fallback.

## Fast input order

1. Use an attached complete capture or the nested capture in a previous results JSON. Validate it with `playlist.py --require-complete`. A supplied file is a dated snapshot, not a live refresh. Reuse an existing validated work list/track mapping when it belongs to that same snapshot.
2. Look for a complete local snapshot by canonical playlist URL:

   ```sh
   python3 /path/to/concert-finder/scripts/playlist_cache.py load 'https://open.spotify.com/playlist/PLAYLIST_ID' --output /path/to/working-playlist.json
   ```

   This accepts snapshots checked within seven calendar days. Print the checking date and track count. If the user requests the current playlist rather than a saved snapshot, explain that this does not refresh Spotify. Do not silently increase the age limit; an older snapshot needs the user's explicit choice.
3. If no complete snapshot exists, try at most two direct public page fetches. Require a visible, independently established total and every numbered position. A list of 100 items is not proof that the playlist has only 100 tracks. If coverage remains incomplete, stop and explain the gap; request a complete capture/report file or an explicitly chosen subset. Do not ask the user to retype hundreds of titles. Do not open a browser UI or launch a headless browser.

Save a complete capture for future searches:

```sh
python3 /path/to/concert-finder/scripts/playlist_cache.py save /path/to/complete-capture-or-report.json
```

The private cache defaults to `~/.cache/hear-it-live/playlists/`, or `$XDG_CACHE_HOME/hear-it-live/playlists/` when configured. The helper makes no network calls and revalidates completeness on every load. A failed partial save leaves a previous complete snapshot intact. If the host has no persistent local filesystem, reuse the complete JSON as an attachment; a cache is not automatically shared between applications or devices.

## Why the limit matters

A browser trial read all 340 positions of one public playlist. A later noninteractive HTTP check of the same playlist returned 30 track links from the public page and 100 tracks from the embed, in under a second per request. Those were incomplete previews. This does not establish a universal Spotify limit or promise the same timing for other requests. Computer use was the available complete-import route in that trial, not a requirement for concert research.

A separate one-time import may create a reusable file, but is outside this no-computer-use concert-search workflow. No automatic import or refresh is performed. Private playlists, unavailable tracks, access barriers and unknown totals must be disclosed. Never collect passwords, cookies or hidden tokens, reverse-engineer private endpoints, download audio, or treat recommendations as playlist members. Keep personal captures out of the public repository.

## Platform conditions

This is not an official or Spotify-approved integration. No Spotify API client or OAuth flow is supplied. Public visibility does not establish permission for every downstream use: Spotify's [Developer Policy](https://developer.spotify.com/policy) and [Developer Terms](https://developer.spotify.com/terms) include AI-ingestion restrictions covering metadata. No exemption is claimed. The [playlist API endpoint](https://developer.spotify.com/documentation/web-api/reference/get-playlists-items) has separate access restrictions; it is not an unrestricted replacement for browser reading.

A direct work list or text file remains supported. For other services, verify complete input access first. Never silently substitute a preview for the full list.
