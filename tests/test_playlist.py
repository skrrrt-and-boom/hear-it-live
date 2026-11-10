"""Coverage checks prevent virtualised previews from becoming whole-playlist claims."""
import copy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/concert-finder/scripts'))
import playlist
import report

CAPTURE = json.loads((ROOT / 'examples/playlist-demo.json').read_text(encoding='utf-8'))
REPORT = json.loads((ROOT / 'examples/playlist-concerts.json').read_text(encoding='utf-8'))


class PlaylistTests(unittest.TestCase):
    def setUp(self):
        self.capture = copy.deepcopy(CAPTURE)

    def test_url_normalizes_locale_and_share_tracking(self):
        self.assertEqual(playlist.playlist_url('https://open.spotify.com/intl-pl/playlist/0000000000000000000000?si=tracking'), CAPTURE['playlist']['url'])

    def test_other_origins_and_nonplaylist_links_are_rejected(self):
        for url in ['https://open.spotify.com.evil.test/playlist/0000000000000000000000', 'https://secret@open.spotify.com/playlist/0000000000000000000000', 'https://open.spotify.com/track/0000000000000000000000', 'http://open.spotify.com/playlist/0000000000000000000000', 'javascript:alert(1)']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                playlist.playlist_url(url)

    def test_duplicate_recordings_keep_distinct_positions(self):
        checked = playlist.validate_capture(self.capture, require_complete=True)
        self.assertEqual(checked['coverage']['readable_tracks'], 4)
        self.assertEqual(checked['tracks'][0]['title'], checked['tracks'][3]['title'])

    def test_reaching_last_track_does_not_hide_middle_gap(self):
        self.capture['tracks'] = [self.capture['tracks'][0], self.capture['tracks'][-1]]
        self.capture['coverage'] = {'complete': True}
        result = playlist.validate_capture(self.capture)
        self.assertEqual(result['coverage']['missing_positions'], [2, 3])
        self.assertFalse(result['coverage']['complete'])
        with self.assertRaisesRegex(ValueError, 'Incomplete playlist'):
            playlist.validate_capture(self.capture, require_complete=True)

    def test_overlapping_windows_merge_without_losing_rows(self):
        first, second = copy.deepcopy(self.capture), copy.deepcopy(self.capture)
        first['tracks'] = first['tracks'][:3]
        second['tracks'] = second['tracks'][2:]
        result = playlist.merge([first, second])
        self.assertEqual([t['position'] for t in result['tracks']], [1, 2, 3, 4])
        self.assertTrue(result['coverage']['complete'])

    def test_conflicting_track_order_is_not_silently_overwritten(self):
        changed = copy.deepcopy(self.capture)
        changed['tracks'][0]['title'] = 'Different work'
        with self.assertRaisesRegex(ValueError, 'Conflicting rows'):
            playlist.merge([self.capture, changed])

    def test_changed_total_restarts_capture(self):
        changed = copy.deepcopy(self.capture)
        changed['playlist']['total_tracks'] = 5
        with self.assertRaisesRegex(ValueError, 'start a fresh capture'):
            playlist.merge([self.capture, changed])

    def test_unavailable_item_is_not_a_readable_track(self):
        self.capture['tracks'][1].update(status='unavailable', reason='Title unavailable in the visible row')
        result = playlist.validate_capture(self.capture)
        self.assertEqual(result['coverage']['missing_positions'], [])
        self.assertEqual(result['coverage']['unavailable_positions'], [2])
        self.assertFalse(result['coverage']['complete'])

    def test_duplicate_or_invalid_positions_are_rejected(self):
        for position in [0, 5, True, 1.5, 2]:
            changed = copy.deepcopy(self.capture)
            changed['tracks'][0]['position'] = position
            with self.subTest(position=position), self.assertRaises(ValueError):
                playlist.validate_capture(changed)

    def test_340_positions_merge_in_overlapping_windows(self):
        self.capture['playlist']['total_tracks'] = 340
        tracks = [{'position': n, 'title': 'Independent test work ' + str(n), 'artists': ['Test composer']} for n in range(1, 341)]
        batches = []
        for offset in range(0, 340, 30):
            batch = copy.deepcopy(self.capture)
            batch['tracks'] = tracks[offset:offset + 53]
            batches.append(batch)
        result = playlist.merge(batches)
        self.assertEqual(result['coverage']['captured_tracks'], 340)
        self.assertTrue(result['coverage']['complete'])

    def test_partial_cli_preserves_checkpoint_but_fails_final_check(self):
        self.capture['tracks'] = self.capture['tracks'][:1]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'batch.json').write_text(json.dumps(self.capture), encoding='utf-8')
            result = subprocess.run([sys.executable, playlist.__file__, str(root / 'batch.json'), '--output', str(root / 'checkpoint.json'), '--require-complete'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads((root / 'checkpoint.json').read_text())['coverage']['missing_positions'], [2, 3, 4])


class PlaylistReportTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(REPORT)

    def test_demo_reports_capture_and_research_coverage_separately(self):
        page = report.render(self.data, date(2026, 11, 10))
        self.assertIn('4 of 4 tracks read', page)
        self.assertIn('3 of 3 works researched', page)
        self.assertIn('Sample playlist · demonstration', page)

    def test_partial_playlist_cannot_generate_a_whole_playlist_report(self):
        self.data['playlist']['tracks'].pop()
        with self.assertRaisesRegex(ValueError, 'Incomplete playlist'):
            report.render(self.data)

    def test_every_track_needs_a_mapping_or_explanation(self):
        self.data['track_work_map'].pop()
        with self.assertRaisesRegex(report.ReportError, 'every playlist track'):
            report.validate(self.data)

    def test_manual_work_cannot_be_smuggled_into_playlist_matches(self):
        self.data['query']['works'].append({'id': 'unrelated', 'composer': 'Other composer', 'title': 'Unrelated work'})
        with self.assertRaisesRegex(report.ReportError, 'must come from a playlist track'):
            report.validate(self.data)

    def test_unresearched_match_is_rejected(self):
        self.data['researched_work_ids'] = []
        with self.assertRaisesRegex(report.ReportError, 'not in researched'):
            report.validate(self.data)

    def test_unresolved_and_unresearched_work_gaps_are_visible(self):
        self.data['track_work_map'][3] = {'position': 4, 'work_ids': [], 'status': 'unresolved', 'reason': 'Ambiguous catalogue variant'}
        self.data['events'] = [self.data['events'][0]]
        self.data['researched_work_ids'] = ['bach-565', 'bach-659']
        page = report.render(self.data)
        self.assertIn('2 of 3 works researched', page)
        self.assertIn('1 tracks unresolved', page)
        self.assertIn('Ambiguous catalogue variant', page)
        self.assertIn('Not researched:', page)

    def test_playlist_name_is_html_escaped(self):
        self.data['playlist']['playlist']['name'] = '<script>alert(1)</script>'
        page = report.render(self.data)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertNotIn('<script>alert(1)</script>', page)


if __name__ == '__main__':
    unittest.main()
