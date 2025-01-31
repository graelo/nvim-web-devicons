for f in lua/nvim-web-devicons/{light,default}/*.lua; do uv run python remap.py $f; done
