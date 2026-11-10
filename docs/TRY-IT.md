# Try it

Install from the repository using `python3 install.py --client codex` or `--client claude-code`. The installer copies a small skill folder into your personal skills directory. It does not edit your assistant settings, install packages, start services or request credentials. Python is only needed for installation and optional HTML/calendar generation.

Start a fresh chat, enable the host's available web research tools, and explicitly invoke the command. Invocation does not grant additional tool permissions. Model/search usage follows the host account's plan and settings.

For a manual ZIP installation, download the package for your client from the latest GitHub release. Extract its `concert-finder` folder into `~/.agents/skills/` for Codex or `~/.claude/skills/` for Claude Code. Keep the client-specific package's settings intact. To remove a manual installation, remove just that extracted folder; the installer only manages copies it installed itself.

## Example requests

**Specific works**

```text
$concert-finder Find church performances of Bach BWV 565 and BWV 659
within 50 km of Kraków between 2026-11-10 and 2026-11-30.
Verify the original announcements. Keep exact matches separate from leads.
Create a local HTML report and calendar if file tools are available.
```

These dates reproduce the saved demo. For a new search, give current dates or say “the next 90 days.”

**An unfamiliar place**

```text
$concert-finder I want to hear Fauré's Requiem within 80 km of a place
I choose, over the next three months. Ask me for that place, then search
local church and organiser websites, including small recitals and PDFs.
```

**Discovery without a work list**

```text
$concert-finder Find nearby-mode organ concerts in churches around
Leiden, within 30 km, this weekend. Include paid and free events.
Show the programme, original source and any missing details.
```

In Claude Code replace `$concert-finder` with `/concert-finder`. Its generated skill sets `disable-model-invocation: true`. A plain ChatGPT/Claude chat can use the copyable instructions below, but the chat interface may not have file execution or the same web tools. The packaged invocation settings specifically target Codex and Claude Code; other clients need their own manual-use settings.

## No-install trial

Copy this into a new AI chat with web search enabled, then replace the bracketed inputs yourself:

> Find verified upcoming classical performances of [composer and work names] around [place], within [distance], during [dates]. Prioritise churches and small organisers. Discover local-language venue sites, bulletins and PDFs as well as existing calendars. Read original announcements, checking the year, date, local time, venue, admission and programme. Match compositions rather than recording artists. Keep exact matches separate from uncertain leads; do not broaden to the same composer unless I request it. Give each result's original URL and explain the work match. Report sources checked and access gaps. If you cannot browse, say so. A Spotify URL alone is not supported input.

## Context and removal

The installed workflow is explicit-only. Its full instructions are loaded when you invoke it; supporting references are read as needed. Loaded instructions and research remain in that conversation, so use a separate chat for concert research. The host controls any residual UI/discovery metadata.

Preview installation with `python3 install.py --client codex --dry-run`. For a project-local installation use `--scope project` from that project. Remove a managed installation with `python3 install.py --client codex --uninstall`, substituting `claude-code` as needed. Existing unrelated skill folders are never overwritten or deleted. Reinstall a managed copy with `--replace` after updating the repository.
