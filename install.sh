#!/usr/bin/env bash
# Link the skills into ~/.claude/skills (or $CLAUDE_SKILLS_DIR) and install Python deps.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
target="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$target"
for skill in pptx-deck pptx-layout-audit; do
  if [ -e "$target/$skill" ] && [ ! -L "$target/$skill" ]; then
    echo "skip: $target/$skill exists and is not a symlink" >&2
    continue
  fi
  ln -sfn "$here/skills/$skill" "$target/$skill"
  echo "linked $target/$skill"
done
python3 -m pip install -r "$here/requirements.txt"
command -v soffice >/dev/null || echo "note: install LibreOffice for visual QA (render_deck.py)"
command -v pdftoppm >/dev/null || echo "note: install poppler-utils for visual QA (render_deck.py)"
