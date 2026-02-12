#!/bin/bash
###
###  Build the database and/or run analysis scripts.
###
###  Usage:
###    bash makedb.sh           # build DB + run analysis (default)
###    bash makedb.sh db        # build DB only
###    bash makedb.sh analysis  # run analysis only (DB must exist)
###

set -e

STEP="${1:-all}"

### set up python

# Check if build environment exists
if [ -d ".venv-build" ]
then
    source ".venv-build"/bin/activate
    uv pip install -r requirements-build.txt
else
    uv venv ".venv-build"
    source ".venv-build"/bin/activate
    uv pip install -r requirements-build.txt
fi

## location of database
mkdir -p web/db


#############################
###  Phase 1: Build the DB
#############################

if [ "$STEP" = "all" ] || [ "$STEP" = "db" ]; then

pushd scripts

if [ -f namae.db ]; then
    mv --backup=numbered namae.db namae.db.bak
fi


echo "Making Tables and reading names from Baby Calendar"
python add-baby-calendar.py "../data/jmena 2008-2022.xlsx"


echo "Adding Heisei data"
python add-heisei.py namae.db "../data/heisei"


echo "Adding Meiji data"
python add-meiji-api.py  namae.db  \
       ../data/meiji_yasuda_data/processed/combined_rankings.csv   \
       ../data/meiji_total_year.tsv  \
       ../data/meiji.xlsx

# python add-meiji.py "../data/meiji.xlsx"


echo "Adding Birth data"
python add-births.py namae.db

# add a table of single characters
echo "Adding Kanji"
python add-kanji.py

# make the attribute table
echo "Calculate attributes"

python calculate-features.py

python calc_feat_uniq.py namae.db


echo "Copy scripts/namae.db to web/db/namae.db'"

cp namae.db ../web/db/namae.db

# index the tables
echo "Adding indexes"

sqlite3 ../web/db/namae.db < add_indexes.sql

echo "Export TSV data"
python export_tsv.py

popd

echo "=== Database build complete ==="

fi


#############################
###  Phase 2: Analysis
#############################

if [ "$STEP" = "all" ] || [ "$STEP" = "analysis" ]; then

if [ ! -f web/db/namae.db ]; then
    echo "ERROR: web/db/namae.db not found. Run 'bash makedb.sh db' first." >&2
    exit 1
fi

pushd scripts

echo "Make Year graphs"

python plot-years.py ../web/db/namae.db \
       ../web/static/plot/

echo "Making Diversity Graphs"

python plot_diversity.py

# make things for the book

### make tables
python pub-tables.py ../web/db/namae.db \
       ../web/static/data/book_tables.json ## output file

### make year plots
python pub-years.py

### compare meiji and other data
python pub-agreement.py

### make meiji diversity

python plot_meiji.py

echo "Plot proportions"
mkdir -p proportion
python plot_proportion.py

echo "Plot gender overlap"
python plot_overlap.py --n-top 50  ../web/db/namae.db
python plot_overlap.py --n-top 500 ../web/db/namae.db
cp output/bc_*_50_* ../web/static/plot/.
cp output/meiji_*_50_* ../web/static/plot/.
cp output/hs_orth_50_* ../web/static/plot/.

echo "calculate grapheme/phoneme mapping"
python calc_regular.py ../web/db/namae.db

echo "Calculate genderedness of names"

python calc_gender.py ../web/db/namae.db \
       ../web/static/data/genderedness.json

echo "Pre-compute androgyny data"
python calc_androgyny.py

echo "Pre-compute overlap data"
python calc_overlap_json.py

echo "Pre-compute top names data"
python calc_topnames.py

echo "Pre-compute stats page data"
python calc_stats_json.py

echo "Pre-compute feature page data"
python calc_features_json.py

echo "Pre-compute names page data"
python calc_names_json.py

echo "Pre-compute irregular page data"
python calc_irregular_json.py

popd

### need to make the jinmei graph, but only once

## used in Chapter 6
# python scripts/img-jinmei.py -o web/static/plot/jinmei

echo "=== Analysis complete ==="

fi
