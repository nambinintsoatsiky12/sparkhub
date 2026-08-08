from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import datetime
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = "SPARKHUB_SECRET_KEY_CHANGE_ME"

# =============================================
# 🔑 FLASK-LOGIN
# =============================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'connexion'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    from database import get_user_by_id
    user = get_user_by_id(user_id)
    if user:
        return User(user['id'], user['email'])
    return None

# =============================================
# 🔑 CLÉ SCRAPERAPI
# =============================================
SCRAPERAPI_KEY = "f554d91dca9a43b2b06744478422a674"

# =============================================
# 🧠 BASE DE DONNÉES
# =============================================
from database import (
    init_db, get_prices, save_price,
    save_annonce, get_all_annonces,
    get_user_by_email, get_user_by_id, create_user,
    save_commentaire, get_commentaires
)
init_db()

# =============================================
# 🏠 ACCUEIL
# =============================================
@app.route('/')
def home():
    return render_template('index.html', year=datetime.datetime.now().year)

# =============================================
# 🔍 RECHERCHE (COMPARATEUR)
# =============================================
@app.route('/scout')
def scout():
    query = request.args.get('query', '').strip().lower()
    country = request.args.get('country', 'worldwide')
    results = []
    updated_at = "Jamais mis à jour"

    if query:
        cache_key = f"{query}_{country}"
        db_results = get_prices(cache_key)

        if db_results:
            results = db_results
            updated_at = db_results[0].get('updated_at', 'Cache')
        else:
            try:
                if country == "worldwide" or country == "US":
                    search_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
                elif country == "FR":
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

                scraperapi_url = f"https://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={search_url}&country_code={country}&render=true"
                response = requests.get(scraperapi_url, timeout=30, proxies={"http": None, "https": None})
                html_content = response.text

                soup = BeautifulSoup(html_content, 'html.parser')
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
                        results.append({
                            'title': title,
                            'price': price_display,
                            'source': f"ScraperAPI ({country})",
                            'affiliate_link': affiliate_link
                        })
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
                            results.append({
                                'title': title,
                                'price': price_display,
                                'source': "ScraperAPI (Jumia)",
                                'affiliate_link': "#"
                            })

                updated_at = f"Aujourd'hui ({country})"

            except Exception as e:
                results = [
                    {'title': f"Erreur: {str(e)[:80]}", 'price': 'Vérifie ta clé ScraperAPI', 'source': 'Info', 'affiliate_link': '#'},
                ]
                updated_at = "API indisponible"

    return render_template('scout.html',
                          query=query,
                          results=results,
                          country=country,
                          updated_at=updated_at,
                          year=datetime.datetime.now().year)

# =============================================
# 📚 GUIDES
# =============================================
@app.route('/guides')
def guides():
    return render_template('guides.html', year=datetime.datetime.now().year)

# =============================================
# 🛒 MARKETPLACE
# =============================================
@app.route('/marketplace')
def marketplace():
    annonces = get_all_annonces()
    return render_template('marketplace.html', annonces=annonces, year=datetime.datetime.now().year)

# =============================================
# 📝 DÉPOSER UNE ANNONCE
# =============================================
@app.route('/deposer-annonce', methods=['GET', 'POST'])
@login_required
def deposer_annonce():
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        prix = request.form.get('prix')
        contact = request.form.get('contact')
        save_annonce(titre, description, prix, contact)
        flash("Annonce publiée !", "success")
        return redirect('/marketplace')
    return render_template('deposer.html', year=datetime.datetime.now().year)

# =============================================
# 👤 MON COMPTE
# =============================================
@app.route('/mon-compte')
@login_required
def mon_compte():
    conn = sqlite3.connect('/home/Sparkhub001/sparkhub/prices.db')
    c = conn.cursor()
    c.execute("SELECT id, titre, description, prix, contact, date FROM annonces WHERE user_id = ? ORDER BY date DESC", (current_user.id,))
    annonces = c.fetchall()
    conn.close()
    return render_template('mon_compte.html', annonces=annonces, year=datetime.datetime.now().year)

# =============================================
# ✏️ MODIFIER UNE ANNONCE
# =============================================
@app.route('/modifier-annonce/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_annonce(id):
    conn = sqlite3.connect('/home/Sparkhub001/sparkhub/prices.db')
    c = conn.cursor()
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        prix = request.form.get('prix')
        contact = request.form.get('contact')
        c.execute("UPDATE annonces SET titre = ?, description = ?, prix = ?, contact = ? WHERE id = ? AND user_id = ?",
                  (titre, description, prix, contact, id, current_user.id))
        conn.commit()
        conn.close()
        flash("Annonce modifiée !", "success")
        return redirect('/mon-compte')
    c.execute("SELECT titre, description, prix, contact FROM annonces WHERE id = ? AND user_id = ?", (id, current_user.id))
    annonce = c.fetchone()
    conn.close()
    if not annonce:
        flash("Annonce introuvable ou vous n'avez pas les droits.", "danger")
        return redirect('/mon-compte')
    return render_template('modifier_annonce.html', annonce=annonce, id=id, year=datetime.datetime.now().year)

# =============================================
# 🗑️ SUPPRIMER UNE ANNONCE
# =============================================
@app.route('/supprimer-annonce/<int:id>')
@login_required
def supprimer_annonce(id):
    conn = sqlite3.connect('/home/Sparkhub001/sparkhub/prices.db')
    c = conn.cursor()
    c.execute("DELETE FROM annonces WHERE id = ? AND user_id = ?", (id, current_user.id))
    conn.commit()
    conn.close()
    flash("Annonce supprimée.", "info")
    return redirect('/mon-compte')

# =============================================
# 💬 COMMENTAIRES
# =============================================
@app.route('/commenter/<int:annonce_id>', methods=['POST'])
@login_required
def commenter(annonce_id):
    commentaire = request.form.get('commentaire')
    if commentaire:
        save_commentaire(annonce_id, current_user.id, commentaire)
        flash("Commentaire ajouté.", "success")
    return redirect('/marketplace')

# =============================================
# 💰 PAIEMENTS
# =============================================
@app.route('/paiements')
def paiements():
    return render_template('paiements.html', year=datetime.datetime.now().year)

# =============================================
# 👤 INSCRIPTION
# =============================================
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
            flash("Compte créé ! Vous pouvez vous connecter.", "success")
            return redirect('/connexion')
        else:
            flash("Cet email est déjà utilisé.", "danger")
            return redirect('/inscription')
    return render_template('inscription.html', year=datetime.datetime.now().year)

# =============================================
# 🔐 CONNEXION
# =============================================
@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_data = get_user_by_email(email)
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            user = User(user_data['id'], user_data['email'])
            login_user(user)
            flash("Connecté !", "success")
            return redirect('/')
        else:
            flash("Email ou mot de passe incorrect.", "danger")
    return render_template('connexion.html', year=datetime.datetime.now().year)

# =============================================
# 🚪 DÉCONNEXION
# =============================================
@app.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    flash("Déconnecté.", "info")
    return redirect('/')

# =============================================
# 📡 WEBHOOK
# =============================================
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

@app.route('/webhook-update', methods=['POST'])
def webhook_update():
    token = request.headers.get('X-Update-Token')
    if token != SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Non autorisé"}), 403
    data = request.get_json()
    if not data or 'updates' not in data:
        return jsonify({"status": "error", "message": "Données invalides"}), 400
    for item in data['updates']:
        save_price(
            item.get('keyword', 'general'),
            item.get('title', 'Produit'),
            item.get('price', 'N/A'),
            item.get('source', 'GitHub')
        )
    return jsonify({"status": "success"})

# =============================================
# 🚀 LANCEMENT
# =============================================
if __name__ == '__main__':
    app.run(debug=True)
