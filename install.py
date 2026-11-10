#!/usr/bin/env python3
"""Install or remove the explicit-only skill. No downloads, model calls or config edits."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

NAME = 'concert-finder'
MARKER = '.hear-it-live-install.json'
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'skills' / NAME


def destination(client, scope='user', base=None):
    root = Path(base) if base else (Path.home() if scope == 'user' else Path.cwd())
    return root / ('.agents' if client == 'codex' else '.claude') / 'skills' / NAME


def owned(target):
    try:
        data = json.loads((target / MARKER).read_text(encoding='utf-8'))
        return isinstance(data, dict) and data.get('project') == 'hear-it-live' and data.get('skill') == NAME
    except (OSError, ValueError):
        return False


def install(target, client, replace=False):
    target = Path(target).expanduser().absolute()
    if target.is_symlink():
        raise ValueError('Refusing to replace a symlink; choose another destination.')
    if target.exists() and (not replace or not owned(target)):
        raise ValueError('Destination exists. --replace only replaces an installation made by this installer.')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.hear-it-live-', dir=target.parent) as temp:
        staged = Path(temp) / NAME
        shutil.copytree(SOURCE, staged, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        skill_file = staged / 'SKILL.md'
        if client == 'claude-code':
            content = skill_file.read_text(encoding='utf-8')
            content = content.replace('---\n', '---\ndisable-model-invocation: true\n', 1)
            skill_file.write_text(content, encoding='utf-8')
            shutil.rmtree(staged / 'agents')  # Codex-only metadata is not needed here.
        (staged / MARKER).write_text(json.dumps({'project': 'hear-it-live', 'skill': NAME, 'client': client}, indent=2) + '\n', encoding='utf-8')
        if target.exists():
            backup = Path(temp) / 'previous'
            target.rename(backup)
            try:
                staged.rename(target)
            except OSError:
                backup.rename(target)
                raise
        else:
            staged.rename(target)
    return target


def uninstall(target):
    target = Path(target).expanduser().absolute()
    if target.is_symlink() or not owned(target):
        raise ValueError('Refusing to remove an unrecognised installation or symlink.')
    shutil.rmtree(target)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client', choices=['codex', 'claude-code'], required=True)
    p.add_argument('--scope', choices=['user', 'project'], default='user')
    p.add_argument('--destination', type=Path, help='custom skill directory, useful for testing')
    p.add_argument('--replace', action='store_true', help='replace only a previously managed installation')
    p.add_argument('--uninstall', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    target = args.destination or destination(args.client, args.scope)
    try:
        if args.dry_run:
            print(('Would remove ' if args.uninstall else 'Would install explicit-only skill at ') + str(target))
        elif args.uninstall:
            uninstall(target)
            print('Removed ' + str(target))
        else:
            result = install(target, args.client, args.replace)
            command = '$concert-finder' if args.client == 'codex' else '/concert-finder'
            print(f'Installed explicit-only skill: {result}\nStart a fresh chat and invoke {command}.')
        return 0
    except (OSError, ValueError) as exc:
        print(f'Installation stopped: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
