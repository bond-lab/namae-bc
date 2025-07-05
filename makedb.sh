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


echo "Making Tables and reading names from Baby Calender"
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


echo "Copy scripts/namae.db to web/db/namae.db'"

cp namae.db ../web/db/namae.db

# index the tables
#echo "Adding indexes"

#sqlite3 ../web/db/namae.db < add_indexes.sql


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
python plot_proportion.py

echo "Plot gender overlap"
python plot_overlap.py ../web/db/namae.db

echo "calculate grapheme/phoneme mapping"
python calc_regular.py > poi


popd

### need to make the jinmei graph, but only once

# python scripts/img-jinmei.py -o web/static/plot/

