"""Existing playlists can be read without writing files or accepting incomplete data."""
from datetime import date
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/concert-finder/scripts/playlist.py'
spec = importlib.util.spec_from_file_location('playlist', SCRIPT)
playlist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(playlist)
URL = 'https://open.spotify.com/playlist/0000000000000000000000'
TODAY = date(2026, 11, 10)


def snapshot():
    return {'playlist': {'url': URL, 'name': 'Test playlist', 'total_tracks': 2, 'checked_at': '2026-11-10'},
            'tracks': [{'position': 1, 'title': 'Toccata and Fugue, BWV 565', 'artists': ['Johann Sebastian Bach']},
                       {'position': 2, 'title': 'Pièce d’Orgue, BWV 572', 'artists': ['Johann Sebastian Bach']}]}


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / '0000000000000000000000.json'
        self.data = snapshot()
        self.write()

    def write(self):
        self.path.write_text(json.dumps(self.data), encoding='utf-8')

    def test_reads_complete_snapshot_and_strips_tracking(self):
        meta, tracks = playlist.load(URL + '?si=tracking', root=self.root, today=TODAY)
        self.assertEqual(meta['checked_at'], '2026-11-10')
        self.assertEqual([t['position'] for t in tracks], [1, 2])

    def test_missing_positions_reject_forged_complete_flag(self):
        self.data['tracks'].pop()
        self.data['coverage'] = {'complete': True}
        self.write()
        with self.assertRaisesRegex(ValueError, 'Incomplete playlist'):
            playlist.load(URL, root=self.root, today=TODAY)

    def test_duplicate_positions_are_rejected(self):
        self.data['tracks'][1]['position'] = 1
        self.write()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            playlist.load(URL, root=self.root, today=TODAY)

    def test_wrong_playlist_is_rejected(self):
        self.data['playlist']['url'] = 'https://open.spotify.com/playlist/1111111111111111111111'
        self.write()
        with self.assertRaisesRegex(ValueError, 'different playlist'):
            playlist.load(URL, root=self.root, today=TODAY)

    def test_unavailable_item_is_not_silently_ignored(self):
        self.data['tracks'][0]['status'] = 'unavailable'
        self.write()
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            playlist.load(URL, root=self.root, today=TODAY)

    def test_old_cache_requires_explicit_selection(self):
        with self.assertRaisesRegex(ValueError, 'older than seven days'):
            playlist.load(URL, root=self.root, today=date(2026, 11, 18))
        meta, _ = playlist.load(URL, self.path, today=date(2026, 11, 18))
        self.assertEqual(meta['checked_at'], '2026-11-10')

    def test_old_nested_capture_can_be_read(self):
        self.data = {'query': {}, 'playlist': self.data, 'events': [{'title': 'Old event'}]}
        self.write()
        meta, tracks = playlist.load(URL, self.path, today=TODAY)
        self.assertEqual(meta['name'], 'Test playlist')
        self.assertEqual(len(tracks), 2)

    def test_cli_returns_text_and_changes_no_files(self):
        self.data['playlist']['checked_at'] = date.today().isoformat()
        self.write()
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), URL, '--input', str(self.path)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('2 tracks', result.stdout)
        self.assertIn('BWV 565', result.stdout)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(after, before)

    def test_cli_has_no_output_file_option(self):
        target = self.root / 'output.json'
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), URL, '--output', str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(target.exists())

    def test_unsafe_links_are_rejected(self):
        for url in ['http://open.spotify.com/playlist/0000000000000000000000', 'https://open.spotify.com.evil.test/playlist/0000000000000000000000', 'https://secret@open.spotify.com/playlist/0000000000000000000000', 'https://open.spotify.com/track/0000000000000000000000']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                playlist.playlist_url(url)

    def test_no_cache_does_not_initialize_one(self):
        missing = self.root / 'missing-cache'
        with self.assertRaisesRegex(ValueError, 'Browser fallback is disabled'):
            playlist.load(URL, root=missing, today=TODAY)
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
