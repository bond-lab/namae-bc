###
###  Run the scripts to make the db and any graphs
###

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

### Run scripts


pushd scripts

if [ -f namae.db ]; then
    mv --backup=numbered namae.db namae.db.bak
fi


echo "Making Tables and reading names"
# make table copy from excel
python add-baby-calendar.py "../data/jmena 2008-2022.xlsx"

# add Heisei data
echo "Adding Heisei data"
python add-heisei.py "../data/heisei"

# add Meiji data
echo "Adding Meiji data"
python add-meiji-api.py  namae.db  \
       ../data/meiji_yasuda_data/processed/combined_rankings.csv   \
       ../data/meiji_total_year.tsv  \
       ../data/meiji.xlsx 

# python add-meiji.py "../data/meiji.xlsx"

# add a table of single characters
echo "Adding Kanji"
python add-kanji.py

# make the attribute table
echo "Calculate attributes"

python calculate-features.py


echo "Copy scripts/namae.db to web/db/namae.db'"

cp namae.db ../web/db/namae.db

# index the tables
#echo "Adding indexes"

#sqlite3 ../web/db/namae.db < add_indexes.sql

# Build name_year_cache
echo "Building yearly name cache"

python calculate-years.py

# make the graphs
echo "Making Graphs"

python plot-diversity.py

# make things for the book

### make tables
python pub-tables.py

### make year plots
python pub-years.py

### compare meiji and other data
python pub-agreement.py

### make meiji diversity
python plot-meiji.py

popd

### need to make the jinmei graph, but only once

## used in Chapter 6
# python scripts/img-jinmei.py -o web/static/plot/jinmei

