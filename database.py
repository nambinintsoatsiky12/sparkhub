import sqlite3
import datetime

DB_PATH = '/home/Sparkhub001/sparkhub/prices.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Table des prix (cache pour les recherches)
    c.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            title TEXT,
            price TEXT,
            source TEXT,
            updated_at TEXT
        )
    ''')
    # Table des annonces (Marketplace)
    c.execute('''
        CREATE TABLE IF NOT EXISTS annonces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT,
            description TEXT,
            prix TEXT,
            contact TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_prices(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, price, source, updated_at FROM prices WHERE keyword = ?", (key,))
    rows = c.fetchall()
    conn.close()
    return [{"title": r[0], "price": r[1], "source": r[2], "updated_at": r[3]} for r in rows]

def save_price(key, title, price, source):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("DELETE FROM prices WHERE keyword = ? AND title = ?", (key, title))
    c.execute("INSERT INTO prices (keyword, title, price, source, updated_at) VALUES (?, ?, ?, ?, ?)",
              (key, title, price, source, now))
    conn.commit()
    conn.close()

# ✅ NOUVELLE FONCTION pour sauvegarder une annonce
def save_annonce(titre, description, prix, contact):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO annonces (titre, description, prix, contact, date) VALUES (?, ?, ?, ?, ?)",
              (titre, description, prix, contact, now))
    conn.commit()
    conn.close()

# ✅ NOUVELLE FONCTION pour récupérer toutes les annonces
def get_all_annonces():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT titre, description, prix, contact, date FROM annonces ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return rows
