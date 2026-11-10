# Try it

Install from the repository with `python3 install.py --client codex` or `--client claude-code`. The installer copies the explicit-only skill, without editing assistant settings or installing dependencies. Start a fresh chat with browser controls and web search/page-reading tools available. Tool permissions remain under the host's control.

## Playlist link → live performances

Use [the opening page](https://skrrrt-and-boom.github.io/hear-it-live/) to prepare a request, or ask directly:

```text
$concert-finder Find where and when music from [Spotify playlist link]
is performed within 50 km of Warsaw in the next 90 days.
Prioritise churches; include free and paid concerts. Verify the entire
playlist, keep exact matches separate from leads, and create a programme
and calendar if file tools are available.
```

Replace the bracketed input with a full `https://open.spotify.com/playlist/…` link. In Claude Code use `/concert-finder`.

The opening page only prepares the request. Your assistant reads the visible playlist in the browser, saves overlapping row batches, verifies `1..N` coverage, maps tracks to works, and researches local performances. It can ask about an ambiguous work, but should not ask you to type the whole track list when it is readable.

An initial text fetch with no tracks does not establish that the playlist is inaccessible. An interactive browser trial read all 340 positions in a public playlist; the initial view exposed only 25. Other playlists and host capabilities can differ. If full access fails, the skill reports the gap and asks before using a narrower subset. It does not bypass private access, extract tokens or provide a Spotify API importer. [Platform conditions](../skills/concert-finder/references/inputs.md).

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
