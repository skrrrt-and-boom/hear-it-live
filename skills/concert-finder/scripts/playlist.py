#!/usr/bin/env python3
"""Read a complete existing playlist snapshot and print it. No writes or network calls."""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlparse


def require(condition, message):
    if not condition:
        raise ValueError(message)


def playlist_url(value):
    require(isinstance(value, str), 'Expected a Spotify playlist URL')
    parsed = urlparse(value)
    match = re.fullmatch(r'/(?:intl-[a-z]{2}/)?playlist/([A-Za-z0-9]{22})/?', parsed.path)
    require(parsed.scheme == 'https' and parsed.netloc == 'open.spotify.com' and match is not None,
            'Use an https://open.spotify.com/playlist/… link')
    return 'https://open.spotify.com/playlist/' + match.group(1)


def load(url, snapshot=None, root=None, today=None):
    canonical, selected = playlist_url(url), snapshot is not None
    if snapshot is None:
        base = Path(root) if root is not None else Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'hear-it-live' / 'playlists'
        snapshot = base / (canonical.rsplit('/', 1)[1] + '.json')
    path = Path(snapshot)
    require(path.is_file(), 'No complete saved playlist available; provide existing complete data. Browser fallback is disabled.')
    data = json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(data, dict), 'Snapshot must be an object')
    if 'query' in data:  # Read old captures without recreating their generated files.
        data = data.get('playlist')
    require(isinstance(data, dict) and isinstance(data.get('playlist'), dict), 'Missing playlist metadata')
    meta, tracks = data['playlist'], data.get('tracks')
    require(playlist_url(meta.get('url')) == canonical, 'Snapshot belongs to a different playlist')
    require(isinstance(meta.get('name'), str) and meta['name'].strip(), 'Missing playlist name')
    total = meta.get('total_tracks')
    require(type(total) is int and 0 <= total <= 100000 and isinstance(tracks, list), 'Invalid track count')
    checked = date.fromisoformat(meta['checked_at'])
    age = ((today or date.today()) - checked).days
    require(age >= 0, 'Snapshot checking date is in the future')
    require(selected or age <= 7, 'Saved snapshot is older than seven days; choose it explicitly or provide updated input')
    positions = set()
    for track in tracks:
        require(isinstance(track, dict), 'Invalid track row')
        position = track.get('position')
        require(type(position) is int and 1 <= position <= total and position not in positions, 'Invalid or duplicate track position')
        positions.add(position)
        require(track.get('status', 'available') == 'available', 'Some playlist items are unavailable')
        require(isinstance(track.get('title'), str) and track['title'].strip(), 'Missing track title')
        require(isinstance(track.get('artists'), list) and all(isinstance(a, str) and a.strip() for a in track['artists']), 'Invalid artist names')
    require(positions == set(range(1, total + 1)), 'Incomplete playlist; missing numbered positions')
    return meta, sorted(tracks, key=lambda track: track['position'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--input', type=Path, help='read an existing snapshot instead of the private cache')
    args = parser.parse_args()
    try:
        meta, tracks = load(args.url, args.input)
        print(f"{meta['name']} | {len(tracks)} tracks | snapshot checked {meta['checked_at']} (not a live refresh)")
        for track in tracks:
            title = ' '.join(track['title'].split())
            artists = '; '.join(' '.join(a.split()) for a in track['artists'])
            print(f"{track['position']}\t{title}\t{artists}")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print('Playlist unavailable: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
