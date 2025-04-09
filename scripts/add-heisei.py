import os
import sys
import sqlite3
import regex
import yaml
from collections import defaultdict as dd

mapping = [('―', 'ー'),
           ('－', 'ー'),
           ('-', 'ー'),
           ('‐',  'ー'),
           ('晴', '晴'),
           ('昻', '昂'),
           ('煕', '熙'),
           ('晧', '皓'),
           ('逹', '達'),
           ('瑤', '瑶'),
           ('翆', '翠'),
           ('桒', '桑'),
           ('莱', '萊'),
           # ('絋',''),
           # ('﨣', ''),
           # ('靖', ''),
           # ('礼', ''),
           ]


with open('kanji.yaml') as fh:
    kanji = yaml.load(fh, Loader=yaml.SafeLoader)

allowed=kanji['joyo'].union(kanji['jinmei']).union(kanji['iterator'])
    
def possible(name, only_kanji=False):
    """
    True if a name is a possible Japanese first name

    That is, it is made up only of allowed kanji, hiragana or katakana
    """
    for c in name:
        if only_kanji:
            if c not in allowed:
                return False
        else:
            if c not in allowed and \
               not regex.match(r'^[\p{scx=Hiragana}\p{scx=Katakana}]+$', c):
                return False
    else:
        return True

#if name != '※希望により削除':


def load_heisei_data(data_dir, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log = open("heisei.log", 'w')
    stats =dd(int)        
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
                                oldname = name
                                name = name.replace(f, t)
                            if oldname != name:
                                print(f"REMAP: '{oldname}' - '{name}' - {directory}/{filename}",
                                      file=log)
                                stats['remap\ttype'] += 1
                                stats['remap\ttoken'] += frequency
                            if possible(name):
                                if len(name) <= 4 \
                                   or not possible(name, only_kanji=True):
                                    data= [(year, name, gender, 'hs')] * frequency
                                    c.executemany(""" 
                                    INSERT INTO namae (year, orth, gender, src)
                                    VALUES (?, ?, ?, ?)""", data)
                                    stats['good\ttype'] += 1
                                    stats['good\ttoken'] += frequency
                                else:
                                    print(f"FULLNAME: '{name}' -  {frequency} - {directory}/{filename}",
                                          file=log)
                                    stats['long\ttype'] += 1
                                    stats['long\ttoken'] += frequency 
                            else:
                                print(f"REJECT: '{name}' -  {frequency} - {directory}/{filename}",
                                      file=log)
                                stats['reject\ttype'] += 1
                                stats['reject\ttoken'] += frequency

    print("\n\n## Statistics\n", file=log)
    for s, f in stats.items():
        print(f'{s}\t{f}', file=log)
                                
    conn.commit()
    conn.close()

if __name__ == "__main__":
    data_directory = sys.argv[1]
    database_path = "namae.db"
    load_heisei_data(data_directory, database_path)
