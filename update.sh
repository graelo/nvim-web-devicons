#!/usr/bin/env bash

set -euxo pipefail

git remote update
git reset --hard HEAD~1
git switch master && git merge upstream/master
git push origin master

git switch 16-color
git rebase master

for f in lua/nvim-web-devicons/{light,default}/*.lua; do
  uv run python remap.py "$f"
done

git add lua/nvim-web-devicons

git commit -m 'feat: add cterm_color codes'
git push --force
