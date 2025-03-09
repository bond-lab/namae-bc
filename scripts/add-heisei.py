import os
import sys
import sqlite3

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
                            if name != '※希望により削除':
                            c.execute(""" 
                            INSERT INTO namae (year, orth, pron, loc, gender, explanation, src)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""", (year, name, '', '', gender, '', 'hc'))          
    conn.commit()
    conn.close()

if __name__ == "__main__":
    data_directory = sys.argv[1]
    database_path = "namae.db"
    load_heisei_data(data_directory, database_path)
