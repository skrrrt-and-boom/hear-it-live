# Try it

Install from the repository with `python3 install.py --client codex` or `--client claude-code`. The installer copies the explicit-only skill without editing assistant settings or installing dependencies. Start a fresh chat with web search/page/PDF fetching available. The skill prohibits computer use; host-level tool permissions remain separate.

## Playlist link → live performances

Use [the opening page](https://skrrrt-and-boom.github.io/hear-it-live/) to prepare a request, or ask directly:

```text
$concert-finder Find where and when music from [Spotify playlist link]
is performed within 50 km of Warsaw in the next 90 days.
Prioritise churches; include free and paid concerts. Verify the entire
playlist, keep exact matches separate from leads, and create a programme
and calendar if file tools are available. Use a complete saved snapshot;
do not use computer use or browser automation.
```

Replace the bracketed input with a full `https://open.spotify.com/playlist/…` link. In Claude Code use `/concert-finder`.

The opening page only prepares the request. Your assistant first reuses an attached capture/previous report or looks up a complete saved playlist by link. It verifies `1..N` coverage and discloses the snapshot's checking date, then searches original concert programmes using web tools. It can ask about an ambiguous work without requiring you to type the whole list.

If no complete snapshot exists, the skill tries at most two direct fetches. The tested 340-track playlist exposed only 30 track links on its public page and 100 embed tracks through HTTP. That is not whole-playlist coverage. The skill must stop and explain rather than silently launch UI automation. A separately requested one-time import can supply a complete file for later searches. [Input and platform conditions](../skills/concert-finder/references/inputs.md).

## Save once, search again

```sh
python3 skills/concert-finder/scripts/playlist_cache.py save /path/to/complete-capture-or-report.json
python3 skills/concert-finder/scripts/playlist_cache.py load 'https://open.spotify.com/playlist/PLAYLIST_ID'
```

Replace `PLAYLIST_ID` with the real ID. Captures are stored privately in `~/.cache/hear-it-live/playlists/` (or the configured XDG cache directory). Automatic reuse accepts a checking date up to seven calendar days old. This is an explicitly dated snapshot, not a current Spotify refresh. Personal files are never included in the GitHub repository or skill ZIPs.

In another app/device, attach the complete capture JSON or previous results JSON. A local cache does not travel with the skill. If you edited the Spotify playlist, supply an updated complete capture or explicitly choose the older snapshot. A skill cannot guarantee a hard application-wide tool block; its no-computer-use rule applies to this workflow and does not change your global settings.

## Existing work-list searches

Work names still work without a playlist:

```text
$concert-finder Find church performances of Bach BWV 565 and BWV 659
within 50 km of Kraków between 2026-11-10 and 2026-11-30.
Verify original announcements. Create a programme and calendar.
```

Those dates reproduce the saved research snapshot. Use current dates for a new search. For discovery without a work list, explicitly ask for “nearby-mode organ concerts” around a place and dates.

## Context, ZIPs and removal

Full instructions load only when invoked; supporting references load as needed. Research stays in that conversation. The client may still list the skill's name/description elsewhere. Use a separate concert chat to keep other conversations clear.

For a manual ZIP installation, extract the package's `concert-finder` folder into `~/.agents/skills/` for Codex or `~/.claude/skills/` for Claude Code. Use the correct client package to preserve explicit-only settings. Delete just that extracted folder to remove a manual installation.

For managed copies, preview with `python3 install.py --client codex --dry-run`, update with `--replace`, or remove with `--uninstall`. Substitute `claude-code` as needed. `--scope project` installs in the current project's skill directory. Unrelated folders are never overwritten or deleted.

The packaged settings target Codex and Claude Code. Other clients need their own explicit-only configuration and suitable tools. Existing assistant subscription, search and usage limits apply.
