#!/usr/bin/env python3
"""Merge browser-observed playlist rows and verify coverage. No network or AI calls."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value, label):
    require(isinstance(value, str) and bool(value.strip()), label + ' must be nonempty text')
    return value


def playlist_url(value):
    nonempty(value, 'playlist URL')
    parsed = urlparse(value)
    require(parsed.scheme == 'https' and parsed.netloc == 'open.spotify.com', 'Use an https://open.spotify.com/playlist/… link')
    match = re.fullmatch(r'/(?:intl-[a-z]{2}/)?playlist/([A-Za-z0-9]{22})/?', parsed.path)
    require(match is not None, 'Expected a Spotify playlist link, not a track, album or shortened URL')
    return 'https://open.spotify.com/playlist/' + match.group(1)


def validate_capture(data, require_complete=False):
    require(isinstance(data, dict) and type(data.get('schema_version')) is int and data['schema_version'] == 1, 'capture schema_version must be 1')
    p = data.get('playlist')
    require(isinstance(p, dict), 'playlist must be an object')
    canonical = playlist_url(p.get('url'))
    nonempty(p.get('name'), 'playlist.name')
    nonempty(p.get('checked_at'), 'playlist.checked_at')
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', p['checked_at']) is not None, 'checked_at must be YYYY-MM-DD')
    date.fromisoformat(p['checked_at'])
    total = p.get('total_tracks')
    require(type(total) is int and 0 <= total <= 100000, 'total_tracks must be an integer between 0 and 100000')
    require(p.get('capture_method') in {'browser', 'web', 'demo'}, 'capture_method must be browser, web or demo')
    tracks = data.get('tracks')
    require(isinstance(tracks, list), 'tracks must be a list')
    found, unavailable, normalized = set(), [], []
    for track in tracks:
        require(isinstance(track, dict), 'track must be an object')
        position = track.get('position')
        require(type(position) is int and 1 <= position <= total, 'track position is outside the playlist')
        require(position not in found, 'duplicate position in a capture; merge overlapping batches instead')
        found.add(position)
        status = track.get('status', 'available')
        require(status in {'available', 'unavailable'}, 'unknown track status')
        title = nonempty(track.get('title'), 'track.title')
        artists = track.get('artists')
        require(isinstance(artists, list) and all(isinstance(a, str) and a.strip() for a in artists), 'track.artists must be a list of names')
        item = {'position': position, 'title': title, 'artists': artists, 'status': status}
        if status == 'unavailable':
            item['reason'] = nonempty(track.get('reason'), 'unavailable reason')
            unavailable.append(position)
        normalized.append(item)
    missing = sorted(set(range(1, total + 1)) - found)
    complete = not missing and not unavailable
    coverage = {'captured_tracks': len(found), 'readable_tracks': len(found) - len(unavailable), 'missing_positions': missing,
                'unavailable_positions': sorted(unavailable), 'complete': complete}
    require(not require_complete or complete, f'Incomplete playlist: {len(found) - len(unavailable)}/{total} readable tracks; missing or unavailable positions remain')
    return {'schema_version': 1, 'playlist': {**p, 'url': canonical}, 'tracks': sorted(normalized, key=lambda t: t['position']), 'coverage': coverage}


def merge(captures):
    require(bool(captures), 'Supply at least one capture')
    first, tracks = None, {}
    for raw in captures:
        capture = validate_capture(raw)
        meta = capture['playlist']
        if first is None:
            first = meta
        require(meta == first, 'Playlist identity, name, count or check date changed; start a fresh capture')
        for track in capture['tracks']:
            position = track['position']
            require(position not in tracks or tracks[position] == track, f'Conflicting rows at position {position}; recheck playlist order')
            tracks[position] = track
    return validate_capture({'schema_version': 1, 'playlist': first, 'tracks': list(tracks.values())})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path, nargs='+', help='JSON batches saved from visible browser rows')
    parser.add_argument('--output', type=Path, help='write a merged checkpoint, including remaining gaps')
    parser.add_argument('--require-complete', action='store_true', help='exit nonzero until every position is readable')
    args = parser.parse_args()
    try:
        result = merge([json.loads(p.read_text(encoding='utf-8')) for p in args.inputs])
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        coverage, total = result['coverage'], result['playlist']['total_tracks']
        print(f"Read {coverage['readable_tracks']}/{total} tracks. Complete: {coverage['complete']}")
        if coverage['missing_positions']:
            print('Missing positions: ' + ', '.join(map(str, coverage['missing_positions'])))
        if coverage['unavailable_positions']:
            print('Unavailable positions: ' + ', '.join(map(str, coverage['unavailable_positions'])))
        if args.require_complete:
            validate_capture(result, require_complete=True)
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Playlist check stopped: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
