#!/usr/bin/env bash
# deploy.sh
#
# Deploy the web application to the production server.
#
# Usage:  bash deploy.sh
#
# Syncs all files needed by the Flask app to compling.upol.cz:/var/www/namae/
# and restarts Apache so changes take effect.
#
# Server layout:
#   /var/www/namae/
#   ├── web/              (Flask app + static data + DB)
#   ├── wsgi.py
#   ├── requirements.txt
#   ├── ATTRIBUTIONS.md   (rendered by docs pages)
#   └── data/
#       ├── README.md     (rendered by docs pages)
#       └── download/
#           ├── README.md (rendered by docs pages)
#           └── *.tsv     (downloadable data files)

set -euo pipefail

DEST="compling.upol.cz:/var/www/namae"

cd "$(dirname "$0")"

# Use --relative so data/README.md and data/download/ keep their paths
rsync -avz --relative --exclude='__pycache__' \
    web \
    wsgi.py \
    requirements.txt \
    ATTRIBUTIONS.md \
    data/README.md \
    data/download \
    "$DEST"

echo ""
echo "Restarting Apache..."
# Requires passwordless sudo on the server for this command, or will prompt.
# To set up: add to /etc/sudoers on compling.upol.cz:
#   bond ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart apache2
ssh -t compling.upol.cz "sudo systemctl restart apache2"

echo "Done."
