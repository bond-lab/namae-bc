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


### Run scripts


pushd scripts

mv --backup=numbered namae.db namae.db.bak

echo "Making Tables and reading names"
# make table copy from excel
python add-baby-calendar.py "../data/jmena 2008-2022.xlsx"

# add a table of single characters
echo "Adding Kanji"
python add-kanji.py

# make the attribute table
echo "Calculate attributes"

python calculate-features.py


# make the graphs
echo "Making Graphs"



popd

### need to make the jinmei graph


echo "Still need to 'cp scripts/namae.db web/db/namae.db'" 
