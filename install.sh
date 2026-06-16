#!/usr/bin/env bash
# Symlink every skill in skills/ into the user's Claude Code / agent skill directories.
# Symlinks (not copies) so `git pull` updates installed skills in place.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
installed=0

for target in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  [ -d "$target" ] || continue
  for skill in "$REPO_DIR"/skills/*/; do
    name="$(basename "$skill")"
    existing="$target/$name"
    if [ -e "$existing" ] && [ ! -L "$existing" ]; then
      echo "SKIP $existing exists and is not a symlink — remove it manually to install" >&2
      continue
    fi
    ln -sfn "${skill%/}" "$existing"
    installed=$((installed + 1))
  done
  echo "Linked skills into $target"
done

if [ "$installed" -eq 0 ]; then
  echo "No skill directory found (~/.claude/skills). Is Claude Code installed?" >&2
  exit 1
fi

echo "Done ($installed links). Update later with: git -C $REPO_DIR pull"
