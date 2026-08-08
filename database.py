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

    # Table des annonces (Marketplace) avec user_id
    c.execute('''
    CREATE TABLE IF NOT EXISTS annonces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        titre TEXT,
        description TEXT,
        prix TEXT,
        contact TEXT,
        image_url TEXT,
        date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')
    # Table des utilisateurs
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT
        )
    ''')

    # Table des commentaires
    c.execute('''
        CREATE TABLE IF NOT EXISTS commentaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annonce_id INTEGER,
            user_id INTEGER,
            commentaire TEXT,
            date TEXT,
            FOREIGN KEY(annonce_id) REFERENCES annonces(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
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
def save_annonce(user_id, titre, description, prix, contact):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO annonces (user_id, titre, description, prix, contact, date) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, titre, description, prix, contact, now))
    conn.commit()
    conn.close()

def get_all_annonces():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT annonces.id, annonces.user_id, annonces.titre, annonces.description, 
               annonces.prix, annonces.contact, annonces.date, users.email 
        FROM annonces 
        JOIN users ON annonces.user_id = users.id 
        ORDER BY annonces.date DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_annonce_by_id(annonce_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, titre, description, prix, contact FROM annonces WHERE id = ?", (annonce_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_annonce(annonce_id, user_id, titre, description, prix, contact):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE annonces 
        SET titre = ?, description = ?, prix = ?, contact = ? 
        WHERE id = ? AND user_id = ?
    """, (titre, description, prix, contact, annonce_id, user_id))
    conn.commit()
    conn.close()

def delete_annonce(annonce_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM annonces WHERE id = ? AND user_id = ?", (annonce_id, user_id))
    conn.commit()
    conn.close()


# ========== FONCTIONS POUR LES COMMENTAIRES ==========
def save_commentaire(annonce_id, user_id, commentaire):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO commentaires (annonce_id, user_id, commentaire, date) VALUES (?, ?, ?, ?)",
              (annonce_id, user_id, commentaire, now))
    conn.commit()
    conn.close()

def get_commentaires(annonce_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT commentaires.commentaire, commentaires.date, users.email 
        FROM commentaires 
        JOIN users ON commentaires.user_id = users.id 
        WHERE annonce_id = ? 
        ORDER BY commentaires.date DESC
    """, (annonce_id,))
    rows = c.fetchall()
    conn.close()
    return [{"commentaire": r[0], "date": r[1], "email": r[2]} for r in rows]


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
