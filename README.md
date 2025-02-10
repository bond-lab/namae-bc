# namae-bc
Name data from the baby calendar and tools to manipulate it.







Contingency table for a given feature:

Last		Gender
Mora		M		F
お			120		223	
not-お




Should I look only at names with > 2 characters for?


Make the data by:
```
cd scripts
mv namae.db namae.bak.db 
# make table copy from excel
python munge.py
# make the attribute table
python meta.py
cp namae.db ../web/db/namae.db 
```
