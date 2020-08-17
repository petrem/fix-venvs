# Fix Virtualenvs

Fix virtualenvs after a python update.

Looks for repositories in places configurable in a `~/.venvs.conf` config file.

Uses only standard library modules to be able to run it outside any virtualenv.

**Note** while this is public, it's just a quick hack.

Config structure will probably change.

## Config file example

```
[DEFAULT]
verbose = no
dry_run = no

[.emacs.d/elpy/rpc-venv]

[~/code/.venv]

[work/coolproject/venv]

[~/.local/share/virtualenvs]
collection = true
```
