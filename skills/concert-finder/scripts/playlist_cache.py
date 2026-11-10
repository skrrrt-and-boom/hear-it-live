#!/usr/bin/env python3
"""Save/reuse complete playlist snapshots locally. No network, AI or browser calls."""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
import tempfile

from playlist import playlist_url, require, validate_capture


def cache_root():
    base = Path(os.environ['XDG_CACHE_HOME']).expanduser() if os.environ.get('XDG_CACHE_HOME') else Path.home() / '.cache'
    return base / 'hear-it-live' / 'playlists'


def cache_path(url, root=None):
    canonical = playlist_url(url)
    return (Path(root) if root is not None else cache_root()) / (canonical.rsplit('/', 1)[1] + '.json')


def read_capture(path):
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    # A previous report also contains a full capture; do not cache its search history.
    if isinstance(raw, dict) and 'query' in raw and 'playlist' in raw:
        raw = raw['playlist']
    return validate_capture(raw, require_complete=True)


def save(path, root=None, today=None):
    capture = read_capture(path)
    checked = date.fromisoformat(capture['playlist']['checked_at'])
    require(checked <= (today or date.today()), 'playlist check date is in the future')
    destination = cache_path(capture['playlist']['url'], root)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent, prefix='.playlist-', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(capture, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        temporary.chmod(0o600)
        temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return destination


def load(url, root=None, max_age_days=7, today=None):
    require(type(max_age_days) is int and max_age_days >= 0, 'max_age_days must be a nonnegative integer')
    canonical = playlist_url(url)
    path = cache_path(canonical, root)
    if not path.is_file():
        raise ValueError('No complete saved playlist found. Supply a previous capture/report file; computer use is disabled for concert searches.')
    capture = read_capture(path)
    require(capture['playlist']['url'] == canonical, 'cached playlist identity does not match the requested link')
    age = ((today or date.today()) - date.fromisoformat(capture['playlist']['checked_at'])).days
    require(age >= 0, 'cached playlist check date is in the future')
    require(age <= max_age_days, f'Saved playlist is {age} calendar days old; the limit is {max_age_days}. Refresh separately or explicitly choose the older snapshot.')
    return capture, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    save_parser = commands.add_parser('save', help='save a complete capture or previous report')
    save_parser.add_argument('input', type=Path)
    load_parser = commands.add_parser('load', help='find a complete snapshot for a playlist link')
    load_parser.add_argument('url')
    load_parser.add_argument('--max-age-days', type=int, default=7)
    load_parser.add_argument('--output', type=Path, help='copy the validated snapshot to a working file')
    for sub in (save_parser, load_parser):
        sub.add_argument('--root', type=Path, help='custom private cache directory')
    args = parser.parse_args()
    try:
        if args.command == 'save':
            path = save(args.input, args.root)
            capture = read_capture(path)
        else:
            capture, path = load(args.url, args.root, args.max_age_days)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(capture, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                args.output.chmod(0o600)
        meta = capture['playlist']
        print(f"Complete saved playlist: {meta['name']} · {meta['total_tracks']} tracks · checked {meta['checked_at']}")
        print('Snapshot: ' + str(path))
        print('This reuses a dated snapshot; it does not check the current Spotify playlist.')
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Saved playlist unavailable: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
