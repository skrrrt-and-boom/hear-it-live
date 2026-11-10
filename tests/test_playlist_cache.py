"""Complete snapshots can be reused without browser access or freshness claims."""
import copy
from datetime import date
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/concert-finder/scripts'))
import playlist_cache

CAPTURE = json.loads((ROOT / 'examples/playlist-demo.json').read_text(encoding='utf-8'))
TODAY = date(2026, 11, 10)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.capture = copy.deepcopy(CAPTURE)
        self.source = self.root / 'input.json'
        self.cache = self.root / 'cache'

    def save(self, data=None):
        self.source.write_text(json.dumps(data if data is not None else self.capture), encoding='utf-8')
        return playlist_cache.save(self.source, self.cache, today=TODAY)

    def test_roundtrip_uses_canonical_playlist_identity(self):
        path = self.save()
        result, loaded = playlist_cache.load(CAPTURE['playlist']['url'] + '?si=tracking', self.cache, today=TODAY)
        self.assertEqual(loaded, path)
        self.assertEqual(result['playlist']['total_tracks'], 4)
        self.assertEqual(result['playlist']['checked_at'], '2026-11-10')
        self.assertTrue(result['coverage']['complete'])

    def test_missing_snapshot_has_no_automatic_fallback(self):
        with self.assertRaisesRegex(ValueError, 'computer use is disabled'):
            playlist_cache.load(CAPTURE['playlist']['url'], self.cache, today=TODAY)
        self.assertFalse(self.cache.exists())

    def test_partial_import_does_not_overwrite_complete_snapshot(self):
        path = self.save()
        original = path.read_bytes()
        self.capture['tracks'].pop()
        with self.assertRaisesRegex(ValueError, 'Incomplete playlist'):
            self.save()
        self.assertEqual(path.read_bytes(), original)

    def test_expiry_uses_check_date_not_file_modification_time(self):
        self.save()
        with self.assertRaisesRegex(ValueError, '8 calendar days old'):
            playlist_cache.load(CAPTURE['playlist']['url'], self.cache, today=date(2026, 11, 18))
        result, _ = playlist_cache.load(CAPTURE['playlist']['url'], self.cache, max_age_days=8, today=date(2026, 11, 18))
        self.assertEqual(result['playlist']['checked_at'], '2026-11-10')

    def test_future_date_is_rejected(self):
        self.capture['playlist']['checked_at'] = '2026-11-11'
        with self.assertRaisesRegex(ValueError, 'future'):
            self.save()

    def test_mismatched_cached_identity_is_rejected(self):
        path = self.save()
        changed = json.loads(path.read_text(encoding='utf-8'))
        changed['playlist']['url'] = 'https://open.spotify.com/playlist/1111111111111111111111'
        path.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'identity does not match'):
            playlist_cache.load(CAPTURE['playlist']['url'], self.cache, today=TODAY)

    def test_tampered_completeness_is_recomputed(self):
        path = self.save()
        changed = json.loads(path.read_text(encoding='utf-8'))
        changed['tracks'].pop()
        changed['coverage']['complete'] = True
        path.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Incomplete playlist'):
            playlist_cache.load(CAPTURE['playlist']['url'], self.cache, today=TODAY)

    def test_previous_report_does_not_cache_concert_history(self):
        report = json.loads((ROOT / 'examples/playlist-concerts.json').read_text(encoding='utf-8'))
        path = self.save(report)
        cached = json.loads(path.read_text(encoding='utf-8'))
        self.assertNotIn('events', cached)
        self.assertNotIn('query', cached)
        self.assertEqual(len(cached['tracks']), 4)

    @unittest.skipIf(sys.platform == 'win32', 'POSIX file permissions')
    def test_snapshot_is_private(self):
        path = self.save()
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == '__main__':
    unittest.main()
