# Playlist input

The main input is a public Spotify playlist URL plus a location. Use the browser-assisted procedure in [browser-playlist.md](browser-playlist.md). Do not ask the user to type track titles when the visible playlist can be read in full.

A real browser trial on 10 November 2026 verified every position in a 340-track public playlist without signing in. A plain page fetch returned no readable text; the interactive browser initially exposed only 25 rows and loaded more while scrolling. This proves that route worked for that playlist, not that all playlists or clients will work.

Only read the requested visible playlist. Private playlists, unavailable tracks, login walls and changing playlist order need an explicit explanation. Do not collect passwords, session cookies or hidden API tokens. Do not download audio, modify playlists or use recommendations as if they belonged to the user's list. Do not publish personal playlist captures in this project.

## Platform limits

This is an experimental browser-assisted workflow, not an official or Spotify-approved integration. It uses the host's existing browser tools; there is no Spotify API client, hosted scraper or OAuth flow. The local form prepares a request; it does not retrieve Spotify tracks itself.

Browser visibility establishes technical access, not permission for every downstream use. Spotify's [Developer Policy](https://developer.spotify.com/policy) and [Developer Terms](https://developer.spotify.com/terms) include restrictions on AI ingestion of Spotify content, including metadata. Reading a public page does not establish an exemption. Recheck the applicable conditions before distributing a Spotify-dependent service or claiming approval. No approval or policy exemption is claimed here.

The [playlist API endpoint](https://developer.spotify.com/documentation/web-api/reference/get-playlists-items) separately restricts playlist access to owned/collaborative playlists for current development integrations. Do not confuse API access rules with what the browser visibly exposes, or substitute private API calls for the documented browser procedure.

## Other inputs

A user-supplied work list or text file remains supported. For another streaming service, establish a complete, supported input path first. If only a preview is available, state its coverage. Never silently search a partial playlist.
