# Music inputs

Use composition names and catalogue numbers supplied directly by the user. Accept a list or text file; ask only about ambiguity that affects matching. Do not turn a recording performer into the requested composer. Keep whole works, movements and arrangements distinct.

## Spotify links are not an implemented integration

This release has no Spotify importer, OAuth flow or credentials. A Spotify link alone is insufficient input. Explain this and ask the user to name the works they want to hear; do not quietly substitute artists or analyse only a web preview.

As checked on 2026-11-10, Spotify's [playlist items endpoint](https://developer.spotify.com/documentation/web-api/reference/get-playlists-items) requires user authorisation and restricts access to owned/collaborative playlists. Its documentation also restricts ingesting Spotify Content into AI models. [Development mode](https://developer.spotify.com/documentation/web-api/concepts/quota-modes) is limited to five allowlisted users and requires the app owner to have Premium. These conditions are distinct from whether a playlist is publicly visible.

Do not scrape Spotify pages, extract session credentials, or use copied Spotify API payloads as a workaround. Do not claim permission to feed Spotify metadata to a model. Re-evaluate the official access and content-use conditions before implementing an importer. The work-list workflow is useful independently and does not require Spotify.

Other streaming URLs also need a verified, supported input path. If the complete work list is unavailable, say so. This skill never downloads or analyses audio.
