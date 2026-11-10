"""The distributable skill stays small, explicit-only and safe to install."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


installer = module('installer', ROOT / 'install.py')
packager = module('packager', ROOT / 'tools/package.py')


class InstallerTests(unittest.TestCase):
    def test_client_destinations(self):
        self.assertEqual(installer.destination('codex', base='/tmp/demo'), Path('/tmp/demo/.agents/skills/concert-finder'))
        self.assertEqual(installer.destination('claude-code', base='/tmp/demo'), Path('/tmp/demo/.claude/skills/concert-finder'))

    def test_update_removes_old_generators_and_preserves_explicit_only(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'concert-finder'
            installer.install(target, 'codex')
            old = target / 'assets/report.html'
            old.parent.mkdir()
            old.write_text('legacy report')
            with self.assertRaises(ValueError):
                installer.install(target, 'codex')
            installer.install(target, 'codex', replace=True)
            self.assertFalse(old.exists())
            self.assertTrue((target / 'scripts/playlist.py').is_file())
            self.assertIn('allow_implicit_invocation: false', (target / 'agents/openai.yaml').read_text())
            installer.uninstall(target)
            self.assertFalse(target.exists())

    def test_claude_has_explicit_invocation_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'concert-finder'
            installer.install(target, 'claude-code')
            self.assertTrue((target / 'SKILL.md').read_text().startswith('---\ndisable-model-invocation: true\n'))
            self.assertFalse((target / 'agents').exists())

    def test_unowned_folder_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / 'keep.txt').write_text('user content')
            for marker in ['[]', '{broken', '{"project":"other"}']:
                (target / installer.MARKER).write_text(marker)
                with self.assertRaises(ValueError):
                    installer.install(target, 'codex', replace=True)
                with self.assertRaises(ValueError):
                    installer.uninstall(target)
                self.assertEqual((target / 'keep.txt').read_text(), 'user content')

    def test_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            original = Path(temp) / 'original'
            installer.install(original, 'codex')
            alias = Path(temp) / 'alias'
            alias.symlink_to(original, target_is_directory=True)
            with self.assertRaises(ValueError):
                installer.install(alias, 'codex', replace=True)
            with self.assertRaises(ValueError):
                installer.uninstall(alias)
            self.assertTrue(original.exists())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'skill'
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'), '--client', 'codex', '--destination', str(target), '--dry-run'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(target.exists())

    def test_packages_contain_only_chat_skill_resources(self):
        expected = {'concert-finder/SKILL.md', 'concert-finder/scripts/playlist.py', 'concert-finder/references/inputs.md', 'concert-finder/LICENSE'}
        with tempfile.TemporaryDirectory() as temp:
            for path in packager.package(temp):
                with zipfile.ZipFile(path) as archive:
                    self.assertIsNone(archive.testzip())
                    if 'claude-code' in path.name:
                        self.assertEqual(set(archive.namelist()), expected)
                        self.assertIn('disable-model-invocation: true', archive.read('concert-finder/SKILL.md').decode())
                    else:
                        self.assertEqual(set(archive.namelist()), expected | {'concert-finder/agents/openai.yaml'})
                        self.assertIn('allow_implicit_invocation: false', archive.read('concert-finder/agents/openai.yaml').decode())
                self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), (Path(temp) / 'SHA256SUMS').read_text())


if __name__ == '__main__':
    unittest.main()
