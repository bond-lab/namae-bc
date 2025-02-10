

pushd scripts

mv --backup=numbered namae.db namae.db.bak

echo "Making Tables and reading names"
# make table copy from excel
python munge.py

# add a table of single characters
echo "Adding Kanji"
python munge-kanji.py

# make the attribute table
echo "Calculate attributes"

python meta.py

popd

### need to make the jinmei graph


echo "Still need to 'cp scripts/namae.db web/db/namae.db'" 
