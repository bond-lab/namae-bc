import sqlite3
import os

def main():
    db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create the cache table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS name_year_cache (
        src TEXT,
        year INTEGER,
        gender TEXT,
        count INTEGER,
        PRIMARY KEY (src, year, gender)
    )
    ''')

    # Clear existing cache entries for these sources
    c.execute("DELETE FROM name_year_cache WHERE src IN ('hs', 'hs+bc')")

    # Populate cache for 'hs'
    c.execute('''
    INSERT INTO name_year_cache (src, year, gender, count)
    SELECT 'hs', year, gender, COUNT(*)
    FROM namae
    WHERE src = 'hs'
    GROUP BY year, gender
    ''')

    # Populate cache for 'hs+bc' (combining both sources)
    c.execute('''
    INSERT INTO name_year_cache (src, year, gender, count)
    SELECT 'hs+bc', year, gender, COUNT(*)
    FROM namae
    WHERE src IN ('hs', 'bc')
    GROUP BY year, gender
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
