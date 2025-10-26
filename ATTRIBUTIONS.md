# Data Source Attributions

This repository combines several datasets of Japanese given names from different sources.  
The overall compilation, structure, and derived analyses are © 2025 Francis Bond and Ivona Barešová, licensed under **CC-BY 4.0**  
(<https://creativecommons.org/licenses/by/4.0/>).

Some component datasets remain © their respective authors or institutions and are included here under fair-use for **research and educational purposes**.

Please credit the original compilers when using their data, and cite this Zenodo record for the combined release.

---

## 1. Baby Calendar (bc)
- **Source:** https://baby-calendar.jp/
- **Copyright:** © 株式会社ベビーカレンダー [Baby Calendar Co., Ltd.]
- **License:** Used under fair use for research and illustration; not for commercial redistribution.  
- **Range:** 2008-2022
- **Notes:** 17 names were excluded, one name we chnaged from boy to girl, based on the name selection story. 

---

## 2. Meiji Yasuda Life Insurance Company (meiji)
- **Source:** https://www.meijiyasuda.co.jp/enjoy/ranking/
- **Copyright:** © Meiji Yasuda Life Insurance Company
- **Processing:** Downloaded and regularized from the API and PDFs.
- **License:**  Used under fair use for research and illustration; not for commercial redistribution. 
- **Range:** 1912-2024
- **Notes:** Top 10 graphic forms from 1912, top 100 graphic and top 50 phonological forms with rankings from 2004

---

## 3. Heisei Namae Jiten (HS)
- **Source:** https://www.namaejiten.com/
- **Copyright:** © 平成名前辞典  [Heisei Name Dictionary]
- **Processing:** Downloaded and regularized
- **License:**  Used under fair use for research and illustration; not for commercial redistribution. 
- **Notes:** Filtered out 239  names that uses non-permissable kanji, such as, 昻樹, Ｊ映美, すた～ら, 花菜＆太一

---

## 4. Japanese Birth Data (BD)
- **Source:** https://www.ipss.go.jp/p-info/e/psj2023/PSJ2023-04.xls
- **Copyright:** ©  National Institute of Population and Social Security Research (IPSS)
- **Processing:** Added data on 2022 and 2023 from https://www.e-stat.go.jp/en/stat-search/files?page=1&layout=dataset&toukei=00450011&tstat=000001028897&cycle=7&tclass1=000001053058&tclass2=000001053061&tclass3=000001053064&stat_infid=000040207114&alpha=7%2C8%2C9&tclass4val=0
- **License:**  Used under fair use for research and illustration; not for commercial redistribution. 
- **Notes:** Filtered out 239  names that uses non-permissable kanji, such as, 昻樹, Ｊ映美, すた～ら, 花菜＆太一

---


## 5 Derived Data and Code
- **Authors:** Francis Bond & Ivona Barešová  
- **License:** [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
- **Includes:** Diversity analysis scripts (`div4.py`), derived frequency tables, and visualization outputs.

---

## Citation

If you use this data, please cite:

> Bond, F., & Barešová, I. (2025). *Online Resources for Japanese Names* Zenodo. https://doi.org/10.xxxx/zenodo.xxxxx

For specific datasets, please also acknowledge the original compilers as indicated above.

You may also be interested in the book we wrote using this data, which goes into a lot more detail:

> Glorie
