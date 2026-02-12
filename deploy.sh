#!/bin/bash
# Deploy the web application to the production server.
#
# Usage:  bash deploy.sh
#
# Syncs all files needed by the Flask app to compling.upol.cz:/var/www/namae/
# and restarts Apache so changes take effect.
#
# Server layout:
#   /var/www/namae/
#   ├── web/              (Flask app)
#   ├── wsgi.py
#   ├── requirements.txt
#   ├── ATTRIBUTIONS.md   (rendered by docs pages)
#   └── data/
#       ├── README.md     (rendered by docs pages)
#       └── download/
#           ├── README.md (rendered by docs pages)
#           └── *.tsv     (downloadable data files)

set -e

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
ssh compling.upol.cz sudo systemctl restart apache2

echo "Done."
