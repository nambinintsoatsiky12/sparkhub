from flask import Flask, render_template, request, jsonify, redirect
import datetime
import requests
from bs4 import BeautifulSoup
import re
import sqlite3

app = Flask(__name__)

# =============================================
# 🔑 TA CLÉ SCRAPERAPI
# =============================================
SCRAPERAPI_KEY = "f554d91dca9a43b2b06744478422a674"

# =============================================
# 🧠 BASE DE DONNÉES (CACHE)
# =============================================
from database import init_db, get_prices, save_price, save_annonce, get_all_annonces
init_db()

# =============================================
# 🌐 PAGE D'ACCUEIL
# =============================================
@app.route('/')
def home():
    return render_template('index.html', year=datetime.datetime.now().year)

# =============================================
# 🔍 PAGE DE RECHERCHE (RÉSULTATS)
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
def deposer_annonce():
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        prix = request.form.get('prix')
        contact = request.form.get('contact')
        save_annonce(titre, description, prix, contact)
        return redirect('/marketplace')
    return render_template('deposer.html', year=datetime.datetime.now().year)

# =============================================
# 💰 PAIEMENTS
# =============================================
@app.route('/paiements')
def paiements():
    return render_template('paiements.html', year=datetime.datetime.now().year)

# =============================================
# 👤 MON COMPTE (protégé)
# =============================================
@app.route('/mon-compte')
@login_required
def mon_compte():
    return render_template('mon_compte.html', year=datetime.datetime.now().year, user=current_user)
# =============================================
# 📡 WEBHOOK POUR GITHUB ACTIONS
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

    count = 0
    for item in data['updates']:
        keyword = item.get('keyword', 'general')
        title = item.get('title', 'Produit')
        price = item.get('price', 'N/A')
        source = item.get('source', 'GitHub')
        save_price(keyword, title, price, source)
        count += 1

    return jsonify({"status": "success", "message": f"{count} prix mis à jour"})

# =============================================
# 🚀 LANCEMENT
# =============================================
if __name__ == '__main__':
    app.run(debug=True)
