#!/usr/bin/env python3
"""Build clean, explicit-only skill ZIPs for Codex and Claude Code."""
from pathlib import Path
import argparse
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'concert-finder'


def package(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for client in ['codex', 'claude-code']:
        archive = out / f'hear-it-live-{client}.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for file in sorted(SKILL.rglob('*')):
                if not file.is_file() or '__pycache__' in file.parts or file.suffix == '.pyc':
                    continue
                rel = file.relative_to(SKILL)
                if client == 'claude-code' and rel.parts[0] == 'agents':
                    continue
                content = file.read_bytes()
                if client == 'claude-code' and rel.as_posix() == 'SKILL.md':
                    content = content.decode().replace('---\n', '---\ndisable-model-invocation: true\n', 1).encode()
                z.writestr('concert-finder/' + rel.as_posix(), content)
            z.write(ROOT / 'LICENSE', 'concert-finder/LICENSE')
        artifacts.append(archive)
    checksums = '\n'.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name for p in artifacts) + '\n'
    (out / 'SHA256SUMS').write_text(checksums, encoding='utf-8')
    return artifacts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    for path in package(args.output):
        print(path)
