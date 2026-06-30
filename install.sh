#!/bin/sh
# companion-pet installer / doctor. Safe to re-run.
set -e
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT"

echo "==> companion-pet @ $ROOT"
chmod +x bin/companion scripts/codex-notify.py 2>/dev/null || true

# 1. make sure built-in art exists
if [ ! -f assets/builtin/characters.json ]; then
  echo "==> generating built-in mascots"
  python3 assets/builtin/make_art.py
fi

# 2. user character folder
mkdir -p "${HOME}/.companion/characters"
echo "==> drop your own PNG/GIF characters into: ${HOME}/.companion/characters"

# 3. tkinter-capable interpreter check
TKPY="$(./bin/companion which-python || true)"
if [ -n "$TKPY" ]; then
  echo "==> GUI interpreter: $TKPY (floating window enabled)"
else
  echo "!!  No tkinter-capable python3 found -> notification-only mode."
  echo "    Enable the floating window with one of:"
  echo "      brew install python-tk@3.14      # for Homebrew python 3.14"
  echo "      brew install python-tk@3.13"
fi

cat <<EOF

==> Claude Code:  register the plugin once, then it runs every session
      claude
      /plugin marketplace add $ROOT
      /plugin install companion-pet@companion-pet-marketplace
    (or for a quick one-off:  claude --plugin-dir $ROOT )

==> Codex (optional, stage 2): add to ~/.codex/config.toml
      notify = ["python3", "$ROOT/scripts/codex-notify.py"]

==> Try it now:
      $ROOT/bin/companion start      # show the companion
      $ROOT/bin/companion demo       # cycle through every ping
      $ROOT/bin/companion stop       # dismiss it
EOF
