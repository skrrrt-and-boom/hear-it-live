"""Behavioral checks for local output, installation and release packages."""
import copy
from datetime import date
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/concert-finder/scripts'))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


report = module('report', ROOT / 'skills/concert-finder/scripts/report.py')
installer = module('installer', ROOT / 'install.py')
packager = module('packager', ROOT / 'tools/package.py')
FIXTURE = json.loads((ROOT / 'examples/krakow-bach.json').read_text(encoding='utf-8'))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(FIXTURE)

    def test_real_fixture_renders_and_separates_leads(self):
        page = report.render(self.data, date(2026, 11, 10))
        self.assertIn('Xaver Varnus', page)
        self.assertIn('Admission not stated', page)
        self.assertIn('Unconfirmed lead', page)
        self.assertNotIn('[[TITLE]]', page)
        self.assertEqual(page.count('data-kind="exact"'), 2)
        self.assertEqual(page.count('data-kind="lead"'), 1)

    def test_exact_mode_rejects_composer_only_result(self):
        self.data['events'][0]['match'] = 'composer'
        with self.assertRaisesRegex(report.ReportError, 'strict exact mode'):
            report.validate(self.data)

    def test_exact_result_needs_requested_work(self):
        self.data['events'][0]['work_ids'] = []
        with self.assertRaisesRegex(report.ReportError, 'requested work ID'):
            report.validate(self.data)

    def test_unknown_work_cannot_be_claimed(self):
        self.data['events'][0]['work_ids'] = ['bach-544']
        with self.assertRaisesRegex(report.ReportError, 'unknown work ID'):
            report.validate(self.data)

    def test_service_cannot_be_presented_as_concert_match(self):
        self.data['events'][0]['event_type'] = 'service'
        with self.assertRaisesRegex(report.ReportError, 'services'):
            report.validate(self.data)

    def test_church_filter_is_enforced(self):
        self.data['events'][0]['venue_type'] = 'other'
        with self.assertRaisesRegex(report.ReportError, 'non-church'):
            report.validate(self.data)

    def test_dates_duplicates_and_radius_are_checked(self):
        changes = [('date', '2027-01-01'), ('distance_km', 51), ('distance_km', float('nan'))]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(self.data)
                changed['events'][0][field] = value
                with self.assertRaises(report.ReportError):
                    report.validate(changed)
        duplicate = copy.deepcopy(self.data['events'][0])
        duplicate['id'] = 'another-announcement'
        self.data['events'].append(duplicate)
        with self.assertRaisesRegex(report.ReportError, 'merge the announcements'):
            report.validate(self.data)

    def test_missing_time_is_a_lead_only(self):
        self.data['events'][0]['time'] = None
        with self.assertRaisesRegex(report.ReportError, 'confirmed start time'):
            report.validate(self.data)

    def test_no_sources_is_invalid(self):
        self.data['events'][0]['sources'] = []
        with self.assertRaisesRegex(report.ReportError, 'supporting sources'):
            report.validate(self.data)

    def test_unsafe_source_links_are_rejected(self):
        for value in ['javascript:alert(1)', 'https://user:secret@example.com/', 'https://example.com/\nBEGIN:VEVENT']:
            with self.subTest(url=value):
                self.data['events'][0]['sources'][0]['url'] = value
                with self.assertRaises(report.ReportError):
                    report.render(self.data)

    def test_html_and_template_text_are_inert(self):
        self.data['events'][0]['title'] = '<img src=x onerror=alert(1)> [[ROWS]]'
        page = report.render(self.data)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt; [[ROWS]]', page)
        self.assertNotIn('<img src=x', page)
        self.assertEqual(page.count('<article class="event"'), 3)

    def test_old_snapshot_is_labelled(self):
        self.assertIn('<p class="archive">Archived search:', report.render(self.data, date(2026, 12, 1)))
        self.assertNotIn('<p class="archive">Archived search:', report.render(self.data, date(2026, 11, 10)))

    def test_empty_result_is_valid(self):
        self.data['events'] = []
        self.assertIn('No verified concerts found', report.render(self.data))
        self.assertNotIn('BEGIN:VEVENT', report.calendar(self.data))

    def test_calendar_has_only_timed_matches_and_utc_conversion(self):
        value = report.calendar(self.data)
        self.assertEqual(value.count('BEGIN:VEVENT'), 2)
        self.assertIn('DTSTART:20261114T190000Z\r\n', value)
        self.assertIn('DTEND:20261114T200000Z\r\n', value)
        self.assertNotIn('Pociask', value)
        self.assertEqual(value.count('\n'), value.count('\r\n'))

    def test_no_end_time_does_not_invent_duration(self):
        self.data['events'] = [self.data['events'][0]]
        self.data['events'][0].pop('end_time')
        self.assertNotIn('DTEND', report.calendar(self.data))

    def test_calendar_escapes_and_folds_utf8_without_injection(self):
        self.data['events'][0]['title'] = 'Łódź, organ; recital\\solo\nBEGIN:VEVENT ' * 10
        value = report.calendar(self.data)
        self.assertEqual(value.count('\r\nBEGIN:VEVENT\r\n'), 2)
        self.assertTrue(all(len(line.encode('utf-8')) <= 75 for line in value.split('\r\n')))
        unfolded = value.replace('\r\n ', '')
        self.assertIn(r'Łódź\, organ\; recital\\solo\nBEGIN:VEVENT', unfolded)

    def test_dst_ambiguity_and_nonexistent_time_are_refused(self):
        for event_date in ['2026-10-25', '2026-03-29']:
            with self.subTest(date=event_date):
                e = {'date': event_date, 'timezone': 'Europe/Warsaw'}
                with self.assertRaisesRegex(report.ReportError, 'local time'):
                    report.local_datetime(e, '02:30')

    def test_cli_invalid_input_does_not_write_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'bad.json').write_text('{broken', encoding='utf-8')
            result = subprocess.run([sys.executable, str(Path(report.__file__)), str(root / 'bad.json'), '--output', str(root / 'out')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / 'out').exists())

    def test_cli_produces_portable_files(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, str(Path(report.__file__)), str(ROOT / 'examples/krakow-bach.json'), '--output', temp, '--as-of', '2026-11-10'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({p.name for p in Path(temp).iterdir()}, {'index.html', 'concerts.ics', 'results.json'})
            self.assertEqual(json.loads((Path(temp) / 'results.json').read_text(encoding='utf-8')), FIXTURE)


class InstallerTests(unittest.TestCase):
    def test_correct_client_and_project_destinations(self):
        self.assertEqual(installer.destination('codex', base='/tmp/demo'), Path('/tmp/demo/.agents/skills/concert-finder'))
        self.assertEqual(installer.destination('claude-code', base='/tmp/demo'), Path('/tmp/demo/.claude/skills/concert-finder'))

    def test_codex_install_replace_and_uninstall(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'concert-finder'
            installer.install(target, 'codex')
            self.assertTrue(installer.owned(target))
            policy = (target / 'agents/openai.yaml').read_text(encoding='utf-8')
            self.assertIn('allow_implicit_invocation: false', policy)
            with self.assertRaises(ValueError):
                installer.install(target, 'codex')
            installer.install(target, 'codex', replace=True)
            self.assertTrue((target / 'assets/report.html').is_file())
            installer.uninstall(target)
            self.assertFalse(target.exists())

    def test_claude_install_disables_model_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'concert-finder'
            installer.install(target, 'claude-code')
            self.assertTrue((target / 'SKILL.md').read_text(encoding='utf-8').startswith('---\ndisable-model-invocation: true\n'))
            self.assertFalse((target / 'agents').exists())

    def test_unowned_folder_and_malformed_marker_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / 'keep.txt').write_text('user content', encoding='utf-8')
            for marker in ['[]', '{broken', '{"project":"other"}']:
                (target / installer.MARKER).write_text(marker, encoding='utf-8')
                with self.assertRaises(ValueError):
                    installer.install(target, 'codex', replace=True)
                with self.assertRaises(ValueError):
                    installer.uninstall(target)
                self.assertEqual((target / 'keep.txt').read_text(encoding='utf-8'), 'user content')

    def test_symlink_target_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / 'original'
            installer.install(original, 'codex')
            alias = root / 'alias'
            alias.symlink_to(original, target_is_directory=True)
            with self.assertRaises(ValueError):
                installer.install(alias, 'codex', replace=True)
            with self.assertRaises(ValueError):
                installer.uninstall(alias)
            self.assertTrue(original.exists())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'skill'
            result = subprocess.run([sys.executable, str(ROOT / 'install.py'), '--client', 'codex', '--destination', str(target), '--dry-run'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(target.exists())

    def test_packages_include_only_installable_skill_and_license(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = packager.package(temp)
            self.assertEqual(len(paths), 2)
            for path in paths:
                with zipfile.ZipFile(path) as z:
                    names = z.namelist()
                    self.assertTrue(all(n.startswith('concert-finder/') for n in names))
                    self.assertIn('concert-finder/LICENSE', names)
                    self.assertIn('concert-finder/scripts/report.py', names)
                    self.assertIn('concert-finder/scripts/playlist.py', names)
                    self.assertIn('concert-finder/scripts/playlist_cache.py', names)
                    self.assertFalse(any('__pycache__' in n for n in names))
                    if 'claude-code' in path.name:
                        self.assertIn('disable-model-invocation: true', z.read('concert-finder/SKILL.md').decode())
                        self.assertFalse(any('/agents/' in n for n in names))
                    else:
                        self.assertIn('allow_implicit_invocation: false', z.read('concert-finder/agents/openai.yaml').decode())
                self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), (Path(temp) / 'SHA256SUMS').read_text())


if __name__ == '__main__':
    unittest.main()
