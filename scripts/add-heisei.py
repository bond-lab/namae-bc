import os
import sys
import sqlite3
import re


mapping = [('―', 'ー'),
       ('－', 'ー'),
       ('-', 'ー'),
       ('‐',  'ー'),
       ('晴', '晴'),
       ('昻', '昂'),
       # ('﨣', ''),
       # ('靖', ''),
       # ('礼', ''),
       ]

bad = "Ｍ＆ｎ?Ｆ～ＤＷＴ※Ｐ＋…ＩＧ．ｒＶＫ？Ｅ￥Ｃｋｍ＊Ｎ-ＬＺＳＪ－/：ＢｊＲ；ＡＯｖ"

def load_heisei_data(data_dir, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for directory, gender in [('boy', 'M'), ('girl', 'F')]:
        dir_path = os.path.join(data_dir, directory)
        for filename in os.listdir(dir_path):
            if filename.endswith('.txt'):
                year = int(filename[1:3]) + 1988
                with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as file:
                    for line in file:
                        parts = line.strip().split('\t')
                        if len(parts) == 3:
                            name, frequency = parts[1], int(parts[2])
                            for (f, t) in mapping:
                                name = name.replace(f, t)
                            if name != '※希望により削除':
                                data= [(year, name, '', '', gender, '', 'hs')] * frequency
                                c.executemany(""" 
 INSERT INTO namae (year, orth, pron, loc, gender, explanation, src)
 VALUES (?, ?, ?, ?, ?, ?, ?)""", data)          
    conn.commit()
    conn.close()

if __name__ == "__main__":
    data_directory = sys.argv[1]
    database_path = "namae.db"
    load_heisei_data(data_directory, database_path)
