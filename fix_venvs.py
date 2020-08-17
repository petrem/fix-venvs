#!/usr/bin/env python3

import argparse
import configparser
from collections import defaultdict
from functools import partial, reduce
from itertools import chain
from pathlib import Path
from venv import EnvBuilder


CONFFILE = "~/.venvs.conf"


def main():
    parser = argparse.ArgumentParser(
        prog=__name__,
        description="Find and fix virtualenvs after in-place upgrade of python"
    )
    parser.add_argument("--skip-config", default=False, action="store_true")
    parser.add_argument("--dry-run", default=False, action="store_true")
    parser.add_argument("--verbose", default=False, action="store_true")

    parser.add_argument("--virtualenvs", nargs="*", default=[])
    parser.add_argument("--collections", nargs="*", default=["~/.local/share/virtualenvs"])

    options = parser.parse_args()

    virtualenvs = options.virtualenvs
    collections = options.collections

    settings = defaultdict(lambda: None)
    if not options.skip_config:
        conffile = Path(CONFFILE).expanduser()
        print(f"Reading configuration file {conffile}")
        settings, conf_virtualenvs, conf_collections = _read_config(conffile)
        virtualenvs.extend(conf_virtualenvs)
        collections.extend(conf_collections)

    verbose = _first_not_none(options.verbose, settings.get("verbose"), False)
    dry_run = _first_not_none(options.dry_run, settings.get("dry_run"), False)

    if verbose and options.virtualenvs:
        print("Virtualenvs:")
        print("\n".join(f"\t{v}" for v in virtualenvs))
    if verbose and options.collections:
        print("Virtualenv collections:")
        print("\n".join(f"\t{c}" for c in collections))
    for v in _get_venvs(virtualenvs, collections):
        _fix_venv(v, dry_run=options.dry_run)


def _get_venvs(virtualenvs, collections):
    path_expand_user = _compose(Path.expanduser, Path)
    return chain(
        map(path_expand_user, virtualenvs),
        (
            d
            for collection in collections
            for d in _list_subdirs(path_expand_user(collection))
            if _is_venv(d)
        ),
    )


def _list_subdirs(path):
    return (d for d in path.glob("*") if d.is_dir())


def _read_config(conffile):
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(conffile)
    settings = cp["DEFAULT"]
    virtualenvs = []
    collections = []
    for section in cp.sections():
        if cp[section].getboolean("collection", False) is True:
            collections.append(section)
        else:
            virtualenvs.append(section)
    return dict(settings), virtualenvs, collections


def _is_venv(d):
    """Assume that if some key files are present, a directory is a virtualenv."""
    return all(map(Path.exists, [ d / "pyvenv.cfg", d / "bin" / "activate"]))


def _fix_venv(v, dry_run=False):
    op = lambda x: None if dry_run else Path.unlink
    removed_count = len(list(map(op, _find_broken_symlinks(v))))
    if removed_count > 0:
        print(f"{v} has {removed_count} broken symlinks removed.")
        if not dry_run:
            env_builder = EnvBuilder(upgrade=True, with_pip=True)
            context = env_builder.ensure_directories(v)
            env_builder.setup_python(context)
        print(f"{v} has been upgraded.")


def _find_broken_symlinks(d):
    for f in d.rglob("*"):
        if f.is_symlink():
            try:
                f.resolve(strict=True)
            except (FileNotFoundError, RuntimeError):
                yield f


def _compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def _first_not_none(*args):
    return next(filter(lambda a: a is not None, args))


if __name__ == "__main__":
    main()
