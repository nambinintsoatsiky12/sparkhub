from flask import Flask, render_template, request, jsonify, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import datetime
import os
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import bcrypt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SPARKHUB_DB_PATH", os.path.join(BASE_DIR, "prices.db"))


def load_env():
    """Charge les variables du fichier .env local (sans écraser l'environnement)."""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_env()

app = Flask(__name__)
app.secret_key = os.environ.get("SPARKHUB_SECRET_KEY", "sparkhub-local-development-key")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'connexion'
login_manager.remember_cookie_duration = datetime.timedelta(days=365)


def init_db():
    """Create the local development schema without overwriting existing data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT, title TEXT, price TEXT, source TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS annonces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, titre TEXT, description TEXT, prix TEXT, contact TEXT,
            image_url TEXT, categorie TEXT, date TEXT
        );
        CREATE TABLE IF NOT EXISTS commentaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annonce_id INTEGER, user_id INTEGER, commentaire TEXT, date TEXT
        );
        CREATE TABLE IF NOT EXISTS guard_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            device_type TEXT NOT NULL,
            platform TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            battery INTEGER,
            last_seen TEXT,
            latitude REAL,
            longitude REAL,
            accuracy REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS guard_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accuracy REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(device_id) REFERENCES guard_devices(id)
        );
        CREATE TABLE IF NOT EXISTS api_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            category TEXT NOT NULL DEFAULT 'Autre',
            auth_type TEXT NOT NULL DEFAULT 'Public',
            status TEXT NOT NULL DEFAULT 'live',
            requests_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


init_db()


class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1])
    return None

SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")

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

def get_all_annonces():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, titre, description, prix, contact, image_url, categorie, date FROM annonces ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_annonces(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, titre, description, prix, contact, image_url, categorie, date FROM annonces WHERE user_id = ? ORDER BY date DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def save_annonce(user_id, titre, description, prix, contact, image_url, categorie):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO annonces (user_id, titre, description, prix, contact, image_url, categorie, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, titre, description, prix, contact, image_url, categorie, now))
    conn.commit()
    conn.close()

def update_annonce(id, titre, description, prix, contact, image_url, categorie):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE annonces SET titre = ?, description = ?, prix = ?, contact = ?, image_url = ?, categorie = ? WHERE id = ?",
              (titre, description, prix, contact, image_url, categorie, id))
    conn.commit()
    conn.close()

def delete_annonce(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM annonces WHERE id = ?", (id,))
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

def save_commentaire(annonce_id, user_id, commentaire):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO commentaires (annonce_id, user_id, commentaire, date) VALUES (?, ?, ?, ?)",
              (annonce_id, user_id, commentaire, now))
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, password FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "password": row[2]}
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
        return False

@app.route('/')
def home():
    """Landing page for SparkHub's API discovery directory."""
    return render_template('apifinder.html', year=datetime.datetime.now().year)


@app.route('/guard')
def guard_home():
    return render_template('guard.html', year=datetime.datetime.now().year)


API_DIRECTORY = [
    {"name": "Open-Meteo", "url": "https://api.open-meteo.com/v1/forecast", "description": "Météo mondiale sans clé, idéale pour des agents et prototypes.", "category": "Météo", "auth_type": "Public", "status": "live", "requests_count": 12400},
    {"name": "REST Countries", "url": "https://restcountries.com/v3.1/all", "description": "Informations géographiques et politiques sur 250 pays.", "category": "Données publiques", "auth_type": "Public", "status": "live", "requests_count": 8900},
    {"name": "Open Library", "url": "https://openlibrary.org/search.json?q=", "description": "Catalogue ouvert de livres, auteurs et éditions du monde entier.", "category": "Culture", "auth_type": "Public", "status": "live", "requests_count": 6200},
    {"name": "Nominatim", "url": "https://nominatim.openstreetmap.org/search", "description": "Géocodage basé sur OpenStreetMap, sans compte requis.", "category": "Cartographie", "auth_type": "Public", "status": "live", "requests_count": 5100},
]


@app.route('/api/directory')
def api_directory():
    query = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip().lower()
    items = API_DIRECTORY
    if query:
        items = [item for item in items if query in (item['name'] + ' ' + item['description'] + ' ' + item['category']).lower()]
    if category and category != 'toutes les catégories':
        items = [item for item in items if item['category'].lower() == category]
    return jsonify({"results": items, "total": len(items)})


@app.route('/api/directory/submit', methods=['POST'])
def submit_api_source():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()[:80]
    url = str(payload.get('url', '')).strip()[:500]
    description = str(payload.get('description', '')).strip()[:240]
    category = str(payload.get('category', 'Autre')).strip()[:40] or 'Autre'
    if not name or not re.match(r'^https?://[^\s]+$', url):
        return jsonify({"error": "Un nom et une URL http(s) valide sont nécessaires."}), 400
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO api_sources (name, url, description, category, created_at) VALUES (?, ?, ?, ?, ?)", (name, url, description, category, datetime.datetime.now(datetime.timezone.utc).isoformat()))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Cette source est déjà dans l'annuaire."}), 409
    return jsonify({"message": "Source proposée. Elle sera vérifiée avant publication."}), 201


@app.route('/api/guard/devices', methods=['GET', 'POST'])
@login_required
def guard_devices():
    """Devices are private to the authenticated account; no SIM or Google data is read."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        name = str(payload.get('name', '')).strip()[:80]
        device_type = str(payload.get('device_type', '')).strip()[:30]
        platform = str(payload.get('platform', '')).strip()[:30]
        consent = payload.get('consent') is True
        if not name or device_type not in {'phone', 'laptop', 'tablet', 'watch'} or not consent:
            conn.close()
            return jsonify({"error": "A device name, type, and explicit consent are required."}), 400
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            """INSERT INTO guard_devices
               (user_id, name, device_type, platform, created_at, last_seen)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (current_user.id, name, device_type, platform, now, now),
        )
        conn.commit()
        device_id = cursor.lastrowid
        conn.close()
        return jsonify({"id": device_id, "name": name, "device_type": device_type}), 201

    cursor.execute(
        """SELECT id, name, device_type, platform, status, battery, last_seen,
                  latitude, longitude, accuracy
           FROM guard_devices WHERE user_id = ? ORDER BY id DESC""",
        (current_user.id,),
    )
    devices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"devices": devices})


@app.route('/api/guard/position', methods=['POST'])
@login_required
def save_guard_position():
    """Store a position supplied by a registered, consented device belonging to its owner."""
    payload = request.get_json(silent=True) or {}
    try:
        device_id = int(payload.get('device_id'))
        latitude = float(payload.get('latitude'))
        longitude = float(payload.get('longitude'))
        accuracy = float(payload.get('accuracy', 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid location payload."}), 400

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180 and 0 <= accuracy <= 100000):
        return jsonify({"error": "Location values are out of range."}), 400

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM guard_devices WHERE id = ? AND user_id = ?",
        (device_id, current_user.id),
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Device not found."}), 404

    cursor.execute(
        """INSERT INTO guard_positions (device_id, latitude, longitude, accuracy, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (device_id, latitude, longitude, accuracy, now),
    )
    cursor.execute(
        """UPDATE guard_devices SET latitude = ?, longitude = ?, accuracy = ?, last_seen = ?
           WHERE id = ?""",
        (latitude, longitude, accuracy, now, device_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "saved", "recorded_at": now})


def fetch_scout_results(query, country):
    """Scrape les prix (cache SQLite puis ScraperAPI). Retourne (results, updated_at)."""
    results = []
    updated_at = "Jamais mis à jour"

    if not query:
        return results, updated_at

    cache_key = f"{query}_{country}"
    db_results = get_prices(cache_key)
    if db_results:
        # Le cache ne contient pas de lien d'achat : on le régénère.
        results = [{**r, 'affiliate_link': '#'} for r in db_results]
        updated_at = db_results[0].get('updated_at', 'Cache')
        return results, updated_at

    if not SCRAPERAPI_KEY:
        # Fallback gratuit : DummyJSON permet de tester le comparateur sans
        # clé payante. Les prix sont ceux du catalogue de démonstration en USD.
        try:
            demo = requests.get(
                "https://dummyjson.com/products/search",
                params={"q": query, "limit": 10},
                timeout=8,
            ).json().get("products", [])
            results = [{
                "title": item.get("title", "Produit"),
                "price": f"{item.get('price', 'N/A')} USD",
                "source": "Catalogue de démonstration",
                "affiliate_link": f"https://dummyjson.com/products/{item.get('id', '')}",
            } for item in demo]
            if results:
                return results, "Catalogue de démonstration · mis à jour maintenant"
        except (requests.RequestException, ValueError, TypeError):
            pass
        results = [{'title': 'Recherche temporairement indisponible',
                    'price': 'Réessayez dans quelques secondes',
                    'source': 'Service de secours',
                    'affiliate_link': '#'}]
        updated_at = "Service indisponible"
        return results, updated_at

    # Code pays normalisé pour ScraperAPI (ISO-2 minuscules)
    country_code = {"US": "us", "FR": "fr", "GB": "uk", "DE": "de",
                    "JP": "jp", "MG": "mg", "worldwide": "us"}.get(country, "us")

    try:
        if country == "FR":
            search_url = f"https://www.amazon.fr/s?k={query.replace(' ', '+')}"
        elif country == "GB":
            search_url = f"https://www.amazon.co.uk/s?k={query.replace(' ', '+')}"
        elif country == "DE":
            search_url = f"https://www.amazon.de/s?k={query.replace(' ', '+')}"
        elif country == "JP":
            search_url = f"https://www.amazon.co.jp/s?k={query.replace(' ', '+')}"
        elif country == "MG":
            search_url = f"https://www.jumia.mg/catalog/?q={query.replace(' ', '+')}"
        else:
            search_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"

        scraperapi_url = f"https://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={search_url}&country_code={country_code}"
        response = requests.get(scraperapi_url, timeout=30, proxies={"http": None, "https": None})
        soup = BeautifulSoup(response.text, 'html.parser')

        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        if not products:
            products = soup.find_all('article', class_='prd')

        count = 0
        for product in products:
            if count >= 10:
                break
            title_tag = product.find('h2')
            if not title_tag:
                title_tag = product.find('h3', class_='name')
            title = title_tag.text.strip() if title_tag else "Produit"
            price_tag = product.find('span', class_='a-price-whole')
            if not price_tag:
                price_tag = product.find('div', class_='prc')
            price = price_tag.text.strip() if price_tag else "N/A"
            currency = "Ar" if country == "MG" else "USD" if country == "US" else "EUR" if country in ["FR", "DE"] else "USD"
            link_tag = product.find('a', class_='a-link-normal')
            if not link_tag:
                link_tag = product.find('a', class_='core')
            affiliate_link = "#"
            if link_tag and link_tag.get('href'):
                if not link_tag['href'].startswith('http'):
                    affiliate_link = "https://www.amazon.com" + link_tag['href']
                else:
                    affiliate_link = link_tag['href']
            if price != "N/A" and title != "Produit":
                price_clean = re.sub(r'[^\d\s,.]', '', price).strip()
                price_display = f"{price_clean} {currency}" if price_clean else price
                save_price(cache_key, title, price_display, f"ScraperAPI ({country})")
                results.append({'title': title, 'price': price_display, 'source': f"ScraperAPI ({country})", 'affiliate_link': affiliate_link})
                count += 1

        if not results:
            jumia_url = f"https://www.jumia.mg/catalog/?q={query.replace(' ', '+')}"
            scraperapi_url_jumia = f"https://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={jumia_url}"
            response_jumia = requests.get(scraperapi_url_jumia, timeout=30, proxies={"http": None, "https": None})
            soup_jumia = BeautifulSoup(response_jumia.text, 'html.parser')
            products_jumia = soup_jumia.find_all('article', class_='prd')
            for product in products_jumia[:10]:
                title_tag = product.find('h3', class_='name')
                price_tag = product.find('div', class_='prc')
                if title_tag and price_tag:
                    title = title_tag.text.strip()
                    price = price_tag.text.strip()
                    price_display = f"{price} Ar"
                    save_price(cache_key, title, price_display, "ScraperAPI (Jumia)")
                    results.append({'title': title, 'price': price_display, 'source': "ScraperAPI (Jumia)", 'affiliate_link': "#"})

        updated_at = f"Aujourd'hui ({country})"

    except Exception as e:
        msg = str(e) or ""
        if "SSL" in msg or "Max retries" in msg or "Connection" in msg or "TLS" in msg or "timed out" in msg or "ConnectTimeout" in msg:
            friendly = "Impossible de joindre l'API (réseau)"
        else:
            friendly = f"Erreur: {msg[:60]}"
        results = [{'title': friendly, 'price': 'Réessayez dans un instant', 'source': 'Info', 'affiliate_link': '#'}]
        updated_at = "API indisponible"

    return results, updated_at


@app.route('/api/scout')
def api_scout():
    """Version JSON du comparateur, utilisée par le tableau de bord Guard."""
    query = request.args.get('query', '').strip().lower()
    country = request.args.get('country', 'worldwide')
    results, updated_at = fetch_scout_results(query, country)
    return jsonify({"query": query, "country": country, "updated_at": updated_at, "results": results})


@app.route('/scout')
def scout():
    query = request.args.get('query', '').strip().lower()
    country = request.args.get('country', 'worldwide')
    results, updated_at = fetch_scout_results(query, country)
    return render_template('scout.html', query=query, results=results, country=country, updated_at=updated_at, year=datetime.datetime.now().year)

@app.route('/guides')
def guides():
    return render_template('guides.html', year=datetime.datetime.now().year)

@app.route('/marketplace')
def marketplace():
    annonces = get_all_annonces()
    return render_template('marketplace.html', annonces=annonces, year=datetime.datetime.now().year, get_commentaires=get_commentaires)

@app.route('/deposer-annonce', methods=['GET', 'POST'])
@login_required
def deposer_annonce():
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        prix = request.form.get('prix')
        contact = request.form.get('contact')
        image_url = request.form.get('image_url')
        categorie = request.form.get('categorie')
        save_annonce(current_user.id, titre, description, prix, contact, image_url, categorie)
        flash("Annonce publiée !", "success")
        return redirect('/marketplace')
    return render_template('deposer.html', year=datetime.datetime.now().year)

@app.route('/mon-compte')
@login_required
def mon_compte():
    annonces = get_user_annonces(current_user.id)
    return render_template('mon_compte.html', annonces=annonces, year=datetime.datetime.now().year)

@app.route('/modifier-annonce/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_annonce(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        prix = request.form.get('prix')
        contact = request.form.get('contact')
        image_url = request.form.get('image_url')
        categorie = request.form.get('categorie')
        c.execute("UPDATE annonces SET titre = ?, description = ?, prix = ?, contact = ?, image_url = ?, categorie = ? WHERE id = ? AND user_id = ?",
                  (titre, description, prix, contact, image_url, categorie, id, current_user.id))
        conn.commit()
        conn.close()
        flash("Annonce modifiée.", "success")
        return redirect('/mon-compte')
    c.execute("SELECT titre, description, prix, contact, image_url, categorie FROM annonces WHERE id = ? AND user_id = ?", (id, current_user.id))
    annonce = c.fetchone()
    conn.close()
    if not annonce:
        flash("Annonce introuvable.", "danger")
        return redirect('/mon-compte')
    return render_template('modifier_annonce.html', annonce=annonce, id=id, year=datetime.datetime.now().year)

@app.route('/supprimer-annonce/<int:id>')
@login_required
def supprimer_annonce(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM annonces WHERE id = ? AND user_id = ?", (id, current_user.id))
    conn.commit()
    conn.close()
    flash("Annonce supprimée.", "info")
    return redirect('/mon-compte')

@app.route('/commenter/<int:annonce_id>', methods=['POST'])
@login_required
def commenter(annonce_id):
    commentaire = request.form.get('commentaire')
    if commentaire:
        save_commentaire(annonce_id, current_user.id, commentaire)
        flash("Commentaire ajouté.", "success")
    return redirect('/marketplace')

@app.route('/paiements')
def paiements():
    return render_template('paiements.html', year=datetime.datetime.now().year)

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if not email or not password:
            flash("Tous les champs sont obligatoires.", "danger")
            return redirect('/inscription')
        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return redirect('/inscription')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        if create_user(email, hashed.decode('utf-8')):
            flash("Compte créé ! Connectez-vous.", "success")
            return redirect('/connexion')
        else:
            flash("Email déjà utilisé.", "danger")
            return redirect('/inscription')
    return render_template('inscription.html', year=datetime.datetime.now().year)

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        user_data = get_user_by_email(email)
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            user = User(user_data['id'], user_data['email'])
            login_user(user, remember=remember)
            flash("Connecté !", "success")
            return redirect('/')
        else:
            flash("Email ou mot de passe incorrect.", "danger")
    return render_template('connexion.html', year=datetime.datetime.now().year)

@app.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    flash("Déconnecté.", "info")
    return redirect('/')

@app.route('/test-api')
def test_api():
    url = f"https://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url=https://www.amazon.com/s?k=iphone&country_code=US&render=true"
    try:
        r = requests.get(url, timeout=30, proxies={"http": None, "https": None})
        return f"Succès ! Longueur du HTML : {len(r.text)} caractères"
    except Exception as e:
        return f"Erreur : {str(e)}"

SECRET_TOKEN = os.environ.get("SPARKHUB_WEBHOOK_TOKEN", "")

@app.route('/webhook-update', methods=['POST'])
def webhook_update():
    token = request.headers.get('X-Update-Token')
    if not SECRET_TOKEN or token != SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Non autorisé"}), 403
    data = request.get_json()
    if not data or 'updates' not in data:
        return jsonify({"status": "error", "message": "Données invalides"}), 400
    for item in data['updates']:
        keyword = item.get('keyword', 'general')
        title = item.get('title', 'Produit')
        price = item.get('price', 'N/A')
        source = item.get('source', 'GitHub')
        save_price(keyword, title, price, source)
    return jsonify({"status": "success", "message": "Mise à jour reçue"})

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "").lower() == "true",
    )
