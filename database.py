import sqlite3
import datetime

DB_PATH = '/home/Sparkhub001/sparkhub/prices.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Table des prix (cache pour les recherches)
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

    # 2. Table des annonces (Marketplace)
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

    # 3. Table des utilisateurs (Inscription / Connexion)  <-- NOUVEAU
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec succès.")


# ========== FONCTIONS POUR LES PRIX ==========
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


# ========== FONCTIONS POUR LES ANNONCES ==========
def save_annonce(titre, description, prix, contact):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO annonces (titre, description, prix, contact, date) VALUES (?, ?, ?, ?, ?)",
              (titre, description, prix, contact, now))
    conn.commit()
    conn.close()

def get_all_annonces():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT titre, description, prix, contact, date FROM annonces ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# ========== FONCTIONS POUR LES UTILISATEURS ==========
def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, password FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "password": row[2]}
    return None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1]}
    return None

def create_user(email, hashed_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO users (email, password, created_at) VALUES (?, ?, ?)",
                  (email, hashed_password, now))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Email déjà utilisé
